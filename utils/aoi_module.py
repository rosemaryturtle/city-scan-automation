# Import
import geopandas as gpd
from shapely.geometry import Point
from utils.log_module import setup_logger
logger = setup_logger(__name__)

def find_country(aoi):
    """
    Helper function to find country name and country iso3 code based on intersecting aoi with global country database
    
    Parameters
    ----------
    aoi : GeoDataFrame
        The AOI geodataframe.
    """

    # define global public bucket and relevant blobs 
    global_bucket_dir = 'https://storage.googleapis.com/city-scan-global-public/'
    country_blob_dir = 'wb_countries/WB_countries_Admin0_10m.shp'
    # extract ISO3 from AOI
    countries = gpd.read_file(f'{global_bucket_dir}{country_blob_dir}').to_crs(epsg=4326)
    # Perform spatial join to find intersections
    intersection = gpd.overlay(aoi, countries, how='intersection')
    # Calculate the area of each intersection
    intersection['area'] = intersection.geometry.area
    # Find the country with the largest intersection area
    max_area_country = intersection.loc[intersection['area'].idxmax()]
    # Get the ISO3 code and name of the country with the largest intersection area
    country_iso3 = max_area_country['ISO_A3'].lower()
    country_name = max_area_country['NAME_EN'].replace(' ', '_').replace("'", "").lower()
    logger.info(f'detect ISO3 from AOI: {country_iso3}')

    return country_iso3, country_name