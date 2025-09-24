import os
import io
import tempfile
import zipfile
import requests
import geopandas as gpd
import rasterio
from rasterio.merge import merge
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import array_bounds
from rasterio import Affine
from rasterio.io import MemoryFile
from rasterio.mask import mask
from shapely.geometry import mapping
from tqdm import tqdm
import utils  # your upload_blob helper


def _find_tile_id_column(gdf):
    """Return the tile id column name in tile_gdf (robust to different names)."""
    for c in gdf.columns:
        if c.lower() in ("tile_id", "tileid", "tile"):
            return c
    # fallback to first column that looks like an id if present
    return None


def ghs_population(aoi_file, city_inputs, local_output_dir, city_name_l, cloud_bucket, output_dir):
    """
    Download, mosaic, clip (in Mollweide), reproject to EPSG:4326, save and upload
    GHS population rasters for an AOI.

    Parameters
    ----------
    aoi_file : path or GeoDataFrame
        The AOI geometry (polygons). If string, it will be read with geopandas.
    city_inputs : dict
        City inputs (not used heavily here but kept for compatibility).
    local_output_dir : str
        Local directory to write final tifs before upload.
    city_name_l : str
        Lowercased city name used in output filenames.
    cloud_bucket : str
        GCS bucket name (used by utils.upload_blob).
    output_dir : str
        Destination prefix inside the bucket (utils.upload_blob will add subfolders).
    """
    # config
    years = list(range(1975, 2035, 5))
    tile_shp_link = "https://ghsl.jrc.ec.europa.eu/download/GHSL_data_54009_shapefile.zip"
    download_base_url = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A'
    download_prefix = 'GHS_POP_E'
    download_subdir = 'GHS_POP_E{year}_GLOBE_R2023A_54009_100/V1-0/tiles'

    os.makedirs(local_output_dir, exist_ok=True)

    # ----------------------------
    # Prepare AOI (GeoDataFrame -> ensure loaded)
    # ----------------------------
    if isinstance(aoi_file, str):
        aoi = gpd.read_file(aoi_file)
    elif isinstance(aoi_file, gpd.GeoDataFrame):
        aoi = aoi_file.copy()
    else:
        raise ValueError("aoi_file must be a path or a GeoDataFrame")

    # ensure AOI is in EPSG:4326 first (keeps expectations consistent)
    aoi_4326 = aoi.to_crs(epsg=4326)

    # Mollweide projection (GHSL native)
    mollweide_proj = "+proj=moll +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    aoi_54009 = aoi_4326.to_crs(mollweide_proj)

    # ----------------------------
    # STEP 1: Download and read tile shapefile (auto-detect internal .shp)
    # ----------------------------
    print("Downloading tile shapefile...")
    r = requests.get(tile_shp_link)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zipfile:
        tmp_zipfile.write(r.content)
        tmp_zip_path = tmp_zipfile.name

    with zipfile.ZipFile(tmp_zip_path, "r") as z:
        shp_candidates = [n for n in z.namelist() if n.endswith(".shp")]
        if not shp_candidates:
            os.remove(tmp_zip_path)
            raise FileNotFoundError("No shapefile inside downloaded tile ZIP.")
        shp_name = shp_candidates[0]
        print(f"Found shapefile inside ZIP: {shp_name}")

    # read tile index and reproject to Mollweide
    tile_gdf = gpd.read_file(f"zip://{tmp_zip_path}!{shp_name}").to_crs(mollweide_proj)

    # determine tile id column name
    tile_id_col = _find_tile_id_column(tile_gdf)
    if tile_id_col is None:
        # fallback to common names if not found
        raise KeyError("Could not find tile id column in tile shapefile.")

    # ----------------------------
    # STEP 2: Find intersecting tiles (use actual AOI geometry NOT bbox)
    # ----------------------------
    print("Finding intersecting tiles...")
    aoi_union = aoi_54009.unary_union
    # Do the intersection in Mollweide (native tile CRS)
    intersecting_tiles = tile_gdf[tile_gdf.intersects(aoi_union)]

    if intersecting_tiles.empty:
        print("No intersecting GHSL tiles found for AOI. Exiting.")
        os.remove(tmp_zip_path)
        return

    tile_ids = intersecting_tiles[tile_id_col].tolist()
    print(f"Found {len(tile_ids)} intersecting tiles: {tile_ids}")

    # ----------------------------
    # STEP 3: For each year -> download tile zips, open tifs in memory, mosaic, clip (Mollweide)
    # ----------------------------
    for year in tqdm(years, desc="Years"):
        tifs = []
        tmp_tile_paths = []  # keep track to delete temp zips

        for tile in tile_ids:
            # build remote filename, e.g. GHS_POP_E1975_..._R10_C29.zip
            file_name = f"{download_prefix}{year}_GLOBE_R2023A_54009_100_V1_0_{tile}.zip"
            sub_path = download_subdir.format(year=year)
            url = f"{download_base_url}/{sub_path}/{file_name}"

            try:
                r = requests.get(url)
                # some tiles may not exist for older/other years
                r.raise_for_status()
            except Exception as e:
                print(f"Tile not available or failed to download: {url} -> {e}")
                continue

            # save zip to temp file (so we can list and open inside)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_tile:
                tmp_tile.write(r.content)
                tile_zip_path = tmp_tile.name
                tmp_tile_paths.append(tile_zip_path)

            # open zip and find .tif members; read into rasterio MemoryFile
            with zipfile.ZipFile(tile_zip_path, "r") as z:
                tif_members = [m for m in z.namelist() if m.endswith(".tif")]
                if not tif_members:
                    continue
                for member in tif_members:
                    with z.open(member) as tif_bytes:
                        mem = MemoryFile(tif_bytes.read())
                        ds = mem.open()
                        tifs.append(ds)

        if not tifs:
            print(f"No tiles downloaded for year {year} (skipping).")
            # cleanup temp tile zips
            for p in tmp_tile_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass
            continue

        # ----------------------------
        # Mosaic (in Mollweide CRS).  merge() returns array (bands, rows, cols) and transform
        # ----------------------------
        mosaic_arr, mosaic_transform = merge(tifs)
        src_meta = tifs[0].meta.copy()
        src_crs = tifs[0].crs  # should be Mollweide (EPSG:54009)
        # Ensure we set correct meta for in-memory mosaic
        mosaic_meta = src_meta.copy()
        mosaic_meta.update({
            "driver": "GTiff",
            "height": mosaic_arr.shape[1],
            "width": mosaic_arr.shape[2],
            "transform": mosaic_transform,
            "count": mosaic_arr.shape[0],
            "dtype": mosaic_arr.dtype,
            "crs": src_crs
        })

        # Write mosaic into an in-memory dataset so we can mask it easily
        with MemoryFile() as mem_mf:
            with mem_mf.open(**mosaic_meta) as mosaic_ds:
                mosaic_ds.write(mosaic_arr)

                # ----------------------------
                # STEP 4: Clip mosaic to AOI (in Mollweide CRS)
                # ----------------------------
                # Prepare AOI geometry in Mollweide for mask
                aoi_shapes = [mapping(aoi_union)]
                clipped_arr, clipped_transform = mask(mosaic_ds, aoi_shapes, crop=True)
                clipped_meta = mosaic_ds.meta.copy()
                clipped_meta.update({
                    "height": clipped_arr.shape[1],
                    "width": clipped_arr.shape[2],
                    "transform": clipped_transform,
                    "count": clipped_arr.shape[0]
                })

        # close opened tile datasets and delete temp zips
        for ds in tifs:
            try:
                ds.close()
                # MemoryFile backing the ds will be cleaned when ds is garbage-collected
            except Exception:
                pass
        for p in tmp_tile_paths:
            try:
                os.remove(p)
            except Exception:
                pass

        # ----------------------------
        # STEP 5: Reproject clipped raster to EPSG:4326 and save to local_output_dir
        # ----------------------------
        dst_crs = "EPSG:4326"
        # compute bounds of clipped raster in source CRS (Mollweide)
        h_clipped = clipped_arr.shape[1]
        w_clipped = clipped_arr.shape[2]
        bounds = array_bounds(h_clipped, w_clipped, clipped_transform)  # (minx, miny, maxx, maxy)

        # calculate transform/size for destination (lat/lon)
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src_crs, dst_crs, w_clipped, h_clipped, *bounds
        )

        out_meta = clipped_meta.copy()
        out_meta.update({
            "crs": dst_crs,
            "transform": dst_transform,
            "width": dst_width,
            "height": dst_height
        })

        out_tif = os.path.join(local_output_dir, f"{city_name_l}_ghs_pop_E{year}.tif")

        # ensure dtype and count are correct
        out_meta["count"] = clipped_arr.shape[0]
        out_meta["dtype"] = clipped_arr.dtype

        # write and reproject per band
        with rasterio.open(out_tif, "w", **out_meta) as dst:
            for band_idx in range(clipped_arr.shape[0]):
                reproject(
                    source=clipped_arr[band_idx],
                    destination=rasterio.band(dst, band_idx + 1),
                    src_transform=clipped_transform,
                    src_crs=src_crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )

        print(f"Saved clipped+reprojected GeoTIFF: {out_tif}")

        # ----------------------------
        # STEP 6: Upload to GCS
        # ----------------------------
        try:
            utils.upload_blob(cloud_bucket, out_tif, f"{output_dir}/{os.path.basename(out_tif)}")
        except Exception as e:
            print(f"Upload failed for {out_tif}: {e}")

    # cleanup tile index zip
    try:
        os.remove(tmp_zip_path)
    except Exception:
        pass

    print("✅ ghs_population finished successfully.")
