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
        country_iso3: str,
        output_dir: str,
        return_raster: bool = True
    ):
    """
    Download WorldPop raster from global bucket for the AOI country and clip it.

    Parameters
    ----------
    aoi : GeoDataFrame
        AOI polygon(s).
    city_name : str
        City name for naming output files.
    country_iso3 : str
        ISO3 country code (e.g. "IDN", "KHM").
    output_dir : str
        Directory where clipped raster will be saved.
    return_raster : bool
        If True, return clipped raster array & metadata.

    Returns
    -------
    (array, metadata) or None
    """

    logger.info("Starting WorldPop data collection…")

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
    worldpop_blob = f"WorldPop/{country_iso3}_ppp_2020_constrained.tif"
    worldpop_url = bucket_base + worldpop_blob

    # Rasterio requires /vsicurl/ for HTTP-based TIFFs
    raster_path = f"/vsicurl/{worldpop_url}"
    logger.info(f"Requesting WorldPop raster: {worldpop_url}")

    try:
        with rasterio.open(raster_path) as src:
            logger.info("WorldPop raster opened successfully.")

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
        logger.error(f"Error reading or clipping WorldPop raster: {e}")
        return None

    # Create output directory
    spatial_dir = os.path.join(output_dir, "spatial")
    os.makedirs(spatial_dir, exist_ok=True)

    output_path = os.path.join(spatial_dir, f"{city_name}_population.tif")

    # Save clipped raster
    try:
        with rasterio.open(output_path, "w", **clipped_meta) as dst:
            dst.write(clipped_image)
        logger.info(f"Clipped WorldPop saved to: {output_path}")
    except Exception as e:
        logger.error(f"Error saving clipped raster: {e}")
        return None

    logger.info("WorldPop complete.")

    if return_raster:
        return clipped_image, clipped_meta

    return None
