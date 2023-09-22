# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['gee']:
    import ee
    import geopandas as gpd
    import geemap as gm
    from pathlib import Path

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # Initialize Earth Engine
    ee.Initialize()

    landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
    
    # Set parameter
    AOI = gm.shp_to_ee(city_inputs['AOI_path'])  # update this for each AOI
    
    # Filter for hottest months in the past X years
    # years = range(city_inputs['first_year'],
    #               city_inputs['last_year'] + 1)

    # def filter_hot_month(year):
    #     return ee.Filter.date(f"{str(year)}-{str(city_inputs['first_hot_month']).zfill(2)}-01", 
    #                           f"{str(year)}-{str(int(city_inputs['last_hot_month']) + 1).zfill(2)}-01")

    # rangefilter = ee.Filter.Or(*[filter_hot_month(year) for year in years])

    years = ['2018', '2019', '2020', '2021', '2022']
    month0 = '06'  # first hottest month  # update for each country
    month1 = '10'  # end of hottest month (note that this is exclusive)  # update for each country

    def filter_hot_month(index):
        return ee.Filter.date(years[index] + '-' + month0 + '-01', years[index] + '-' + month1 + '-01')

    range0 = filter_hot_month(0)
    range1 = filter_hot_month(1)
    range2 = filter_hot_month(2)
    range3 = filter_hot_month(3)
    range4 = filter_hot_month(4)

    rangefilter = ee.Filter.Or(range0, range1, range2, range3, range4)

    # Define a function to scale the data and mask unwanted pixels
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

    # Apply filter and mask
    collectionSummer = landsat \
        .filter(rangefilter) \
        .filterBounds(AOI) \
        .map(maskL457sr) \
        .select('ST_B10') \
        .mean() \
        .add(-273.15) \
        .clip(AOI)
    
    # Export
    task = ee.batch.Export.image.toDrive(**{
        'image': collectionSummer,
        'crs': 'EPSG:4326',
        'description': f"{city_name_l}_summer",
        'folder': city_inputs['country_name'],
        'region': AOI.geometry(),
        'skipEmptyTiles': True,
        'scale': 30,
        'maxPixels': 1e9
    })

    task.start()
