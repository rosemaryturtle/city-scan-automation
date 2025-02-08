import geopandas as gpd
from shapely.geometry import Point

def find_country(data_bucket, countries_shp_dir, countries_shp_blob, local_data_dir, aoi_file = None, aoi_point = None):
    """
    Checks country based on which country aoi_file overlaps with the most or which country aoi_point is located in.
    """
    import utils
    
    # Load global countries shapefile
    for blob in utils.list_blobs_with_prefix(data_bucket, f"{countries_shp_dir}/{countries_shp_blob}"):
        utils.download_blob(data_bucket, blob.name, f"{local_data_dir}/{blob.name.split('/')[-1]}", check_exists=True)
    countries = gpd.read_file(f"{local_data_dir}/{countries_shp_blob}.shp").to_crs(epsg=4326)

    if aoi_file is not None:
        # Perform spatial join to find intersections
        intersection = gpd.overlay(aoi_file, countries, how='intersection')

        # Calculate the area of each intersection
        intersection['area'] = intersection.geometry.area

        # Find the country with the largest intersection area
        max_area_country = intersection.loc[intersection['area'].idxmax()]
    elif aoi_point is not None:
        # Ensure aoi_point is a shapely Point
        if not isinstance(aoi_point, Point):
            aoi_point = Point(aoi_point)

        # Create a GeoDataFrame for the point
        point_gdf = gpd.GeoDataFrame([{'geometry': aoi_point}], crs=countries.crs)

        # Perform spatial join to find the country containing the point
        intersection = gpd.sjoin_nearest(point_gdf, countries, how='left')

        # Get the country containing the point
        max_area_country = intersection.iloc[0]
    else:
        raise ValueError("Either aoi_file or aoi_point must be provided")
    
    # Get the ISO3 code and name of the country with the largest intersection area
    country_iso3 = max_area_country['ISO_A3']
    country_name = max_area_country['NAME_EN']
    country_name_l = country_name.replace(' ', '_').replace("'", "").lower()

    return country_iso3, country_name, country_name_l

def standardize_location(city_name, data_bucket, countries_shp_dir, countries_shp_blob, local_data_dir):
    """
    Geocode the city name to get standardized city and country names, along with ISO3 country code.
    """
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="city_boundary_extractor")
    location = geolocator.geocode(city_name, language='en')
    
    if not location:
        raise ValueError(f"Could not geocode {city_name}")
    
    # Parse the address to extract city and country
    address_parts = location.address.split(', ')
    city = address_parts[0]  # First part is usually the city
    country = address_parts[-1]  # Last part is usually the country
    
    # Get ISO3 code for the country
    country_iso3, country_name, country_name_l = find_country(data_bucket, countries_shp_dir, countries_shp_blob, local_data_dir, aoi_point=Point(location.longitude, location.latitude))
    
    return {
        'city': city,
        'country': country_name,
        'iso3_code': country_iso3,
        'latitude': location.latitude,
        'longitude': location.longitude,
        'country_name_l': country_name_l
    }

def check_osm_boundary_area(city_name, country_name):
    """
    Retrieve OSM boundary and check its area.
    
    Args:
        city_name (str): Name of the city
        country_name (str): Name of the country
    
    Returns:
        dict: A dictionary containing boundary information and area check results
    """
    try:
        # Attempt to retrieve boundary from OpenStreetMap
        import osmnx as ox
        query = f"{city_name}, {country_name}"
        city_boundary = ox.geocode_to_gdf(query)
        
        # Reproject to an equal-area projection for accurate area calculation
        # equal_area_crs = CRS.from_epsg(6933)  # World Equidistant Cylindrical projection
        city_boundary_area = city_boundary.to_crs(epsg=6933)
        
        # Calculate area in square kilometers
        area_sq_km = city_boundary_area.geometry.area.iloc[0] / 1_000_000
        
        return {
            'boundary': city_boundary,
            'area_sq_km': area_sq_km,
            'is_too_large': area_sq_km > 1000,  # Define threshold for "too large"
            'success': True
        }
    
    except Exception as e:
        return {
            'boundary': None,
            'area_sq_km': None,
            'is_too_large': False,
            'success': False,
            'error': str(e)
        }

def create_buffer(lat, lon, buffer_distance_km, city_name):
    """
    Create a buffer polygon around a point using a specified distance in kilometers.
    """
    point = Point(lon, lat)
    
    gdf = gpd.GeoDataFrame({'city': [city_name]}, geometry=[point], crs="EPSG:4326")
    
    gdf_local = gdf.to_crs(epsg=3857)
    
    buffered_geom_local = gdf_local.geometry.buffer(buffer_distance_km * 1000)  # Buffer in meters
    
    buffered_gdf = gpd.GeoDataFrame(geometry=buffered_geom_local, crs="EPSG:3857").to_crs(epsg=4326)
    
    return buffered_gdf

def get_city_boundary(city_name, local_gpkg_path, data_bucket, countries_shp_dir, countries_shp_blob, local_data_dir):
    """
    Retrieve the boundary of a city using a local GeoPackage or OpenStreetMap.
    If both fail or OSM boundary is too large, create a buffer around the city's coordinates.
    """
    standardized_location = standardize_location(city_name, data_bucket, countries_shp_dir, countries_shp_blob, local_data_dir)
    city = standardized_location['city']
    country = standardized_location['country']
    iso3_code = standardized_location['iso3_code']
    country_name_l = standardized_location['country_name_l']
    lat, lon = standardized_location['latitude'], standardized_location['longitude']
    point = Point(lon, lat)  # Create a Point geometry from the coordinates
    
    print(f"Standardized Location: City: {city}, Country: {country}")

    if local_gpkg_path:
        print("Checking local GeoPackage using coordinates...")
        gdf = gpd.read_file(local_gpkg_path)
        
        # Perform spatial query to find the polygon containing the point
        containing_polygon = gdf[gdf.contains(point)]
        
        if not containing_polygon.empty:
            print("Polygon found in local GeoPackage.")
            return containing_polygon, iso3_code, country, country_name_l
        else:
            print("No polygon found in local GeoPackage for the given coordinates.")
    
    print("Fetching boundary from OpenStreetMap...")
    
    osm_result = check_osm_boundary_area(city, country)
    
    if osm_result['success']:
        if osm_result['is_too_large']:
            print(f"OSM boundary is too large ({osm_result['area_sq_km']} sq km). Proceeding to create buffer.")
        else:
            print(f"OSM boundary retrieved successfully with area {osm_result['area_sq_km']} sq km.")
            return osm_result['boundary'], iso3_code, country, country_name_l
    
    print("Creating buffered polygon as fallback...")
    
    lat, lon = standardized_location['latitude'], standardized_location['longitude']
    
    buffer_distance_km = 5  # Universal buffer distance for small cities
    buffered_gdf = create_buffer(lat, lon, buffer_distance_km, city)
    
    print(f"Buffered polygon created with {buffer_distance_km} km radius.")
    
    return buffered_gdf, iso3_code, country, country_name_l

def save_to_shp(gdf, output_path):
    """
    Save the GeoDataFrame to a shapefile.
    Ensure the GeoDataFrame is in EPSG:4326 projection.
    """
    import os

    # Ensure gdf is in EPSG:4326 projection
    if gdf.crs != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save the GeoDataFrame to a shapefile
    gdf.to_file(output_path)
    print(f"Boundary saved as shapefile at {output_path}")
