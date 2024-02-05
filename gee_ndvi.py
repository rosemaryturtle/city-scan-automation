# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['green']:
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


    # GEE PARAMETERS #####################################
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

    NDVI_last_year = ee.DateRange(f'{str(dt.date.today().year-1)}-01-01', f'{str(dt.date.today().year)}-01-01')

    # Functions --------------------
    def maskS2clouds(image):
        qa = image.select('QA60')

        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11

        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

        return image.updateMask(mask).divide(10000)


    # PROCESSING #########################################
    s2a_Season = ee.ImageCollection('COPERNICUS/S2').filterBounds(AOI).filter(rangefilter).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).map(maskS2clouds)

    S2a_RecentAnnual = ee.ImageCollection('COPERNICUS/S2').filterBounds(AOI).filterDate(NDVI_last_year).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).map(maskS2clouds)

    s2a_med_Season = s2a_Season.median().clip(AOI)
    s2a_med_RecentAnnual = S2a_RecentAnnual.median().clip(AOI)

    nir_season = s2a_med_Season.select('B8')
    red_season = s2a_med_Season.select('B4')
    ndvi_Season = nir_season.subtract(red_season).divide(nir_season.add(red_season)).rename('NDVI')

    nir_recent = s2a_med_RecentAnnual.select('B8')
    red_recent = s2a_med_RecentAnnual.select('B4')
    ndvi_recentannual = nir_recent.subtract(red_recent).divide(nir_recent.add(red_recent)).rename('NDVI')

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{
        'image': ndvi_Season,
        'description': f'{city_name_l}_NDVI_Season',
        'bucket': global_inputs['cloud_bucket'],
        'region': AOI,
        'scale': 10,
        'maxPixels': 1e9
    })
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{
        'image': ndvi_recentannual,
        'description': f'{city_name_l}_NDVI_Annual',
        'bucket': global_inputs['cloud_bucket'],
        'region': AOI,
        'scale': 10,
        'maxPixels': 1e9
    })
    task1.start()
