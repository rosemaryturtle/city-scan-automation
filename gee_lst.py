# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['summer_lst']:
    print('run gee_lst')
    
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

    landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

    # Read AOI shapefile --------
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)

    # Convert shapefile to ee.Geometry ------------
    jsonDict = eval(aoi_file['geometry'].to_json())

    if len(jsonDict['features']) > 1:
        print('Need to convert polygons into a multipolygon')
        print('or do something else, like creating individual raster for each polygon and then merge')
        exit()
    
    jsonDict['features'][0]['geometry']['coordinates'][0] = [x[:-1] for x in jsonDict['features'][0]['geometry']['coordinates'][0]]
    AOI = ee.Geometry.MultiPolygon(jsonDict['features'][0]['geometry']['coordinates'])


    # GEE PARAMETERS ################################
    # Date filter -----------------
    if city_inputs["last_hot_month"] > city_inputs["first_hot_month"]:
        range_list = [ee.Filter.date(f'{year}-{city_inputs["first_hot_month"]}-01',
                                     f'{year}-{city_inputs["last_hot_month"]+1}-01') for year in range(city_inputs['first_year'], 
                                                                                                       city_inputs['last_year'] + 1)]
    elif city_inputs["last_hot_month"] < city_inputs["first_hot_month"]:
        range_list0 = [ee.Filter.date(f'{year}-{city_inputs["first_hot_month"]}-01',
                                      f'{year+1}-01-01') for year in range(city_inputs['first_year'],
                                                                           city_inputs['last_year'] + 1)]
        range_list1 = [ee.Filter.date(f'{year}-01-01',
                                      f'{year}-{city_inputs["last_hot_month"]+1}-01') for year in range(city_inputs['first_year'],
                                                                                                        city_inputs['last_year'] + 1)]
        range_list = range_list0 + range_list1

    rangefilter = ee.Filter.Or(range_list)

    # Cloud mask function ----------------
    def maskL457sr(image):
        # Bit 0 - Fill
        # Bit 1 - Dilated Cloud
        # Bit 2 - Cirrus (high confidence)
        # Bit 3 - Cloud
        # Bit 4 - Cloud Shadow
        qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
        saturationMask = image.select('QA_RADSAT').eq(0)
        # Apply the scaling factors to the appropriate bands.
        thermalBand = image.select('ST_B10').multiply(0.00341802).add(149.0)
        # Replace the original bands with the scaled ones and apply the masks.
        return image.addBands(thermalBand, None, True).updateMask(qaMask).updateMask(saturationMask)


    # GEE PROCESSING ###############################
    collectionSummer = landsat.filter(rangefilter).filterBounds(AOI).map(maskL457sr).select('ST_B10').mean().add(-273.15).clip(AOI)
    task = ee.batch.Export.image.toCloudStorage(**{
        'image': collectionSummer,
        'description': f"{city_name_l}_summer",
        'bucket': global_inputs['cloud_bucket'],
        # 'folder': city_inputs['country_name'],
        'region': AOI,
        'scale': 30,
        'maxPixels': 1e9
    })
    task.start()
