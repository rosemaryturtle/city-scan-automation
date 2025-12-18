# import
import os
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from utils.log_module import setup_logger

logger = setup_logger(__name__)

def datacollection(
        aoi: gpd.GeoDataFrame,
        city_name: str,
        output_dir: str,
        return_raster: bool = True
    ):
    """
    Download landslide raster from global bucket and clip it to AOI.

    Parameters
    ----------
    aoi : GeoDataFrame
        AOI polygon(s).
    city_name : str
        City name for naming output files.
    output_dir : str
        Directory where clipped raster will be saved.
    return_raster : bool
        If True, return clipped raster array & metadata.

    Returns
    -------
    (array, metadata) or None
    """

    logger.info("Starting landslide data collection…")

    # Validate AOI
    if aoi is None or aoi.empty:
        logger.error("AOI is empty. Cannot continue.")
        return None

    # Ensure AOI is in correct CRS for raster operations
    if aoi.crs is None:
        logger.error("AOI has no CRS defined.")
        return None

    logger.info(f"AOI CRS: {aoi.crs}")

    # Construct GCS URL
    bucket_base = "https://storage.googleapis.com/city-scan-global-public/"
    landslide_blob = f"landslide/global-landslide-susceptibility-map-2-27-23.tif"
    landslide_url = bucket_base + landslide_blob

    # Rasterio requires /vsicurl/ for HTTP-based TIFFs
    raster_path = f"/vsicurl/{landslide_url}"
    logger.info(f"Requesting landslide raster: {landslide_url}")

    try:
        with rasterio.open(raster_path) as src:
            logger.info("landslide raster opened successfully.")

            shapes = [geom.__geo_interface__ for geom in aoi.geometry]

            clipped_image, clipped_transform = mask(
                src,
                shapes=shapes,
                crop=True,
                nodata=0
            )

            clipped_meta = src.meta.copy()
            clipped_meta.update({
                "driver": "GTiff",
                "height": clipped_image.shape[1],
                "width": clipped_image.shape[2],
                "transform": clipped_transform,
                "nodata": 0
            })

    except Exception as e:
        logger.error(f"Error reading or clipping landslide raster: {e}")
        return None

    # Create output directory
    spatial_dir = os.path.join(output_dir, "spatial")
    os.makedirs(spatial_dir, exist_ok=True)

    output_path = os.path.join(spatial_dir, f"{city_name}_landslide.tif")

    # Save clipped raster
    try:
        with rasterio.open(output_path, "w", **clipped_meta) as dst:
            dst.write(clipped_image)
        logger.info(f"Clipped landslide saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving clipped raster: {e}")
        return None

    logger.info("landslide complete.")

    if return_raster:
        return clipped_image, clipped_meta

    return None
