# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['forest']:
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

    fc = ee.Image("UMD/hansen/global_forest_change_2018_v1_6")

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
    deforestation0018 = fc.select('loss').eq(1).clip(AOI).rename('fcloss0018')
    forestCover00 = fc.select('treecover2000').gte(20).clip(AOI)
    forestCoverGain0018 = fc.select('gain').eq(1).clip(AOI)
    forestCover18 = forestCover00.subtract(deforestation0018).add(forestCoverGain0018).gte(1).rename('fc00')

    fc18Andfcloss = deforestation0018.addBands(forestCover18)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': forestCover18,
                                                    'description': f'{city_name_l}_ForestCover18',
                                                    'region': AOI,
                                                    'scale': 30,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9})
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{'image': deforestation0018,
                                                    'description': f'{city_name_l}_Deforestation',
                                                    'region': AOI,
                                                    'scale': 30,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9})
    task1.start()
