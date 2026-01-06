def process_earthquake(aoi_file, city_name_l, output_dir):
    """
    Processes earthquake ground shaking data by clipping to AOI, rasterizing, 
    and saving results in a similar structure to flood processing.

    Args:
        aoi_file (GeoDataFrame): The area of interest.
        city_name_l (str): Name of the city or study area.
        output_dir (str): Local directory to save output files.
        
    Outputs:
        Clipped raster (TIFF).
    """
    import requests
    import zipfile
    import io
    import rasterio
    import rasterio.features
    import rasterio.mask
    import numpy as np
    import geopandas as gpd
    from os.path import exists, join
    import os

    print('Running process_earthquake')

    # ------------------------------------------------------------------------------
    # 1️. Download ZIP and extract raster into memory
    # ------------------------------------------------------------------------------
    url = "https://cloud.openquake.org/s/6SnFk2f92JEr76H/download"
    desired_file = "v2023_1_pga_475_rock_3min.tif"

    response = requests.get(url)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        if desired_file in z.namelist():
            with z.open(desired_file) as tif_file:
                geotiff_bytes = tif_file.read()
        else:
            raise FileNotFoundError(f"{desired_file} not found in ZIP")

    # ------------------------------------------------------------------------------
    # 2️. Clip raster to AOI bbox
    # ------------------------------------------------------------------------------
    aoi = gpd.read_file(aoi_file)

    with rasterio.MemoryFile(geotiff_bytes) as memfile:
        with memfile.open() as src:
            src_crs = src.crs
            src_transform = src.transform

            if aoi.crs.to_string() != src_crs.to_string():
                aoi = aoi.to_crs(src_crs)

            bounds = aoi.total_bounds  # (minx, miny, maxx, maxy)
            window = rasterio.windows.from_bounds(
                *bounds, transform=src.transform
            )

            clipped_image = src.read(window=window)
            clipped_transform = src.window_transform(window)

            clipped_profile = src.profile.copy()
            clipped_profile.update(
                transform=clipped_transform,
                width=clipped_image.shape[2],
                height=clipped_image.shape[1],
            )


    # ------------------------------------------------------------------------------
    # 3. Save output files
    # ------------------------------------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)
    clipped_tif_file = join(output_dir, f'{city_name_l}_earthquake.tif')

    # Save clipped raster
    with rasterio.open(clipped_tif_file, "w", **clipped_profile) as dst:
        dst.write(clipped_image)


    print(f"Files successfully processed and saved to {output_dir}")
    print("Process completed.")
