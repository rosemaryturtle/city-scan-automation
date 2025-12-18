# import
import os
import geopandas as gpd
from utils.log_module import setup_logger
from shapely.geometry import Polygon
import pandas as pd
import numpy as np

logger = setup_logger(__name__)

def datacollection(
        aoi: gpd.GeoDataFrame,
        city_name: str,
        country_iso3: str,
        output_dir: str,
        return_gdf: bool = True
    ):
    """
    Download Relative Wealth Index CSV from global bucket for the AOI country and construct geodataframe.

    Parameters
    ----------
    aoi : GeoDataFrame
        AOI polygon(s).
    city_name : str
        City name for naming output files.
    country_iso3 : str
        ISO3 country code (e.g. "IDN", "KHM").
    output_dir : str
        Directory where geodataframe will be saved.
    return_gdf : bool
        If True, return geodataframe.

    Returns
    -------
    Geodataframe or None
    """

    logger.info("Starting Relative Wealth Index data collection…")

    # Validate AOI
    if aoi is None or aoi.empty:
        logger.error("AOI is empty. Cannot continue.")
        return None

    # Ensure AOI is in correct CRS for csv operations
    if aoi.crs is None:
        logger.error("AOI has no CRS defined.")
        return None

    logger.info(f"AOI CRS: {aoi.crs}")

    # Construct GCS URL
    country_iso3 = country_iso3.upper()
    bucket_base = "https://storage.googleapis.com/city-scan-global-public/"
    rwi_blob = f"relative_wealth_index/{country_iso3}_relative_wealth_index.csv"
    rwi_url = bucket_base + rwi_blob
    logger.info(f"Requesting rwi csv: {rwi_url}")

    try:
        # Build geometry from lat/lon
        rwi_df = pd.read_csv(rwi_url)
        rwi_gdf = gpd.GeoDataFrame(
            rwi_df,
            geometry=gpd.points_from_xy(rwi_df.longitude, rwi_df.latitude),
            crs="EPSG:4326"
        )
        
        # Project both datasets to a metric CRS (Web Mercator)
        rwi_proj = rwi_gdf.to_crs(3857)
        aoi_proj = aoi.to_crs(3857)

        # ----------------------------------------------------------
        # Estimate spacing from median nearest-neighbor distance
        # ----------------------------------------------------------
        logger.info("Estimating grid spacing from nearest-neighbor distance…")

        coords = np.array([
            (geom.x, geom.y) for geom in rwi_proj.geometry
        ])

        # Compute pairwise distances (brute force, but OK for country-scale grids)
        # Exclude self-distance (0)
        distances = []
        for i in range(len(coords)):
            dx = coords[i, 0] - coords[:, 0]
            dy = coords[i, 1] - coords[:, 1]
            d = np.sqrt(dx**2 + dy**2)
            d = d[d > 0]  # remove self-distance
            distances.append(d.min())

        median_spacing = np.median(distances) #2445.98
        half_spacing = median_spacing / 2

        logger.info(
            f"Estimated median nearest-neighbor spacing: "
            f"{median_spacing:.2f} meters"
        )

        # Build polygons around each point
        polygons = []
        for idx, row in rwi_proj.iterrows():
            x, y = row.geometry.x, row.geometry.y
            poly = Polygon([
                (x - half_spacing, y - half_spacing),
                (x + half_spacing, y - half_spacing),
                (x + half_spacing, y + half_spacing),
                (x - half_spacing, y + half_spacing)
            ])
            polygons.append(poly)

        # Replace geometry with polygons
        rwi_tiles = rwi_proj.copy()
        rwi_tiles["geometry"] = polygons

        # Clip to AOI
        rwi_tiles = gpd.clip(rwi_tiles, aoi_proj)
        rwi_tiles = rwi_tiles.to_crs(aoi.crs)

        # Create categorical bins for RWI
        bins = 5
        
        labels_en = [
            "Least Wealthy",
            "Less Wealthy",
            "Average",
            "More Wealthy",
            "Most Wealthy"
        ]

        rwi_tiles["wealth_cat_en"] = pd.qcut(rwi_tiles["rwi"], bins, labels=labels_en)



    except Exception as e:
        logger.error(f"Error reading or clipping rwi csv: {e}")
        return None

    # Create output directory
    spatial_dir = os.path.join(output_dir, "spatial")
    os.makedirs(spatial_dir, exist_ok=True)

    # Save clipped csv
    try:
        rwi_tiles.to_file(f"{spatial_dir}/{city_name}_rwi.gpkg", driver = 'GPKG', layer = 'rwi')
    except Exception as e:
        logger.error(f"Error saving clipped csv: {e}")
        return None

    logger.info("rwi complete.")

    if return_gdf:
        return rwi_tiles

    return None
