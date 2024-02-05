# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['landcover']:
    import ee
    import geopandas as gpd

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

    jsonDict['features'][0]['geometry']['coordinates'][0] = [x[:-1] for x in jsonDict['features'][0]['geometry']['coordinates'][0]]
    AOI = ee.Geometry.Polygon(jsonDict['features'][0]['geometry']['coordinates'])


    # PROCESSING #####################################
    lc_aoi = lc.clip(AOI)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': lc_aoi,
                                                    'description': f'{city_name_l}_lc',
                                                    'region': AOI,
                                                    'scale': 10,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9})
    task0.start()
