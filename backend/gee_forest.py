# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['forest']:
    print('run gee_forest')
    
    import ee
    import geopandas as gpd

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Initialize Earth Engine
    ee.Initialize()

    fc = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")

    # Read AOI shapefile --------
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)

    # Convert shapefile to ee.Geometry ------------
    jsonDict = eval(gpd.GeoSeries([aoi_file['geometry'].force_2d().union_all()]).to_json())
    
    if len(jsonDict['features']) > 1:
        print('Need to convert polygons into a multipolygon')
        print('or do something else, like creating individual raster for each polygon and then merge')
        exit()

    # if len(jsonDict['features'][0]['geometry']['coordinates'][0][0]) > 2:
    #     jsonDict['features'][0]['geometry']['coordinates'][0] = [x[0:2] for x in jsonDict['features'][0]['geometry']['coordinates'][0]]
    AOI = ee.Geometry.MultiPolygon(jsonDict['features'][0]['geometry']['coordinates'])


    # PROCESSING #####################################
    no_data_val = 0

    deforestation0023 = fc.select('loss').eq(1).clip(AOI).unmask(value = no_data_val, sameFootprint = False).rename('fcloss0023')
    forestCover00 = fc.select('treecover2000').gte(20).clip(AOI)
    # note: forest gain is only updated until 2012
    forestCoverGain0012 = fc.select('gain').eq(1).clip(AOI)
    forestCover23 = forestCover00.subtract(deforestation0023).add(forestCoverGain0012).gte(1).rename('fc23').unmask(value = no_data_val, sameFootprint = False)
    # TODO: check if the nodata value (0) works, in lines 56 and 82
    deforestation_year = fc.select('lossyear').clip(AOI).unmask(value = no_data_val, sameFootprint = False)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': forestCover23,
                                                    'description': f'{city_name_l}_ForestCover23',
                                                    'region': AOI,
                                                    'scale': 30,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{'image': deforestation_year,
                                                    'description': f'{city_name_l}_Deforestation',
                                                    'region': AOI,
                                                    'scale': 30,
                                                    'bucket': global_inputs['cloud_bucket'],
                                                    'maxPixels': 1e9,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task1.start()
