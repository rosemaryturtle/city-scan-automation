# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['landcover']:
    import ee
    import geopandas as gpd
    import datetime as dt

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Initialize Earth Engine
    ee.Initialize()

    lc = ee.ImageCollection('ESA/WorldCover/v200').first()

    # Read AOI shapefile --------
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)

    # Convert shapefile to ee.Geometry ------------
    jsonDict = eval(aoi_file['geometry'].to_json())

    if len(jsonDict['features']) > 1:
        print('Need to convert polygons into a multipolygon')
        print('or do something else, like creating individual raster for each polygon and then merge')
        exit()
    AOI = ee.Geometry.Polygon(jsonDict['features'][0]['geometry']['coordinates'])


    # PROCESSING #####################################
    lc_aoi = lc.clip(AOI)

    # Land cover burnability -----------------
    if menu['landcover_burn']:
        input_vals = [10, 11, 12, 20, 30, 40, 50, 60, 61, 62, 70, 
                    71, 80, 81, 82, 90, 100, 110, 120, 121, 122,
                    130, 140, 150, 151, 152, 153, 160, 170, 180,
                    190, 200, 201, 202, 210, 220]
        output_vals = [0.66, 0.5, 0.33, 0.66, 0.66, 0.66, 0.83, 1, 0.83, 1, 0.66, 
                    0.66, 0.83, 0.66, 0.5, 0.66, 0.83, 0.5, 0.83, 0.66, 0.83,
                    0.66, 0.33, 0.5, 0.16, 0.33, 0.33, 0.83, 0.83, 0.5,
                    0, 0, 0, 0, 0, 0]
        lc_burn = lc_aoi.remap(input_vals, output_vals, 0)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': lc_aoi,
                                                    'description': f'{city_name_l}_lc',
                                                    'region': AOI,
                                                    'scale': 10,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9})
    task0.start()

    if menu['landcover_burn']:
        task1 = ee.batch.Export.image.toCloudStorage(**{'image': lc_burn,
                                                        'description': f'{city_name_l}_lc_burn',
                                                        'region': AOI,
                                                        'scale': 10,
                                                        'bucket': global_inputs['cloud_bucket'],
                                                        'maxPixels': 1e9})
        task1.start()
