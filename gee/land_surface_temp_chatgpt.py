# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['gee']:
    import ee
    import geopandas as gpd

    # Initialize Earth Engine
    ee.Initialize()

    landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")

    # Set parameter
    AOI = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)  # update this for each AOI
    id = "Tshikapa"  # update this for each AOI
    id1 = id.lower()
    country = 'DRC'  # update this for each country and make an eponymous folder in google drive, as the destination of exported outputs

    # Filter for hottest months in the past X years
    years = ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022']
    month0 = '02'  # first hottest month  # update for each country
    month1 = '05'  # end of hottest month (note that this is exclusive)  # update for each country

    def filter_hot_month(index):
        return ee.Filter.date(years[index] + '-' + month0 + '-01', years[index] + '-' + month1 + '-01')

    range0 = filter_hot_month(0)
    range1 = filter_hot_month(1)
    range2 = filter_hot_month(2)
    range3 = filter_hot_month(3)
    range4 = filter_hot_month(4)
    range5 = filter_hot_month(5)
    range6 = filter_hot_month(6)
    range7 = filter_hot_month(7)
    range8 = filter_hot_month(8)
    range9 = filter_hot_month(9)

    rangefilter = ee.Filter.or(range0, range1, range2, range3, range4, range5, range6, range7, range8, range9)

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

    # Find minimum and maximum temperatures in AOI to set visualization parameters
    # AOI_min = collectionSummer \
    #     .reduceRegion({
    #         'reducer': ee.Reducer.min(),
    #         'geometry': AOI,
    #         'scale': 30,
    #         'maxPixels': 1e9
    #     }) \
    #     .get('ST_B10') \
    #     .getInfo()

    # AOI_max = collectionSummer \
    #     .reduceRegion({
    #         'reducer': ee.Reducer.max(),
    #         'geometry': AOI,
    #         'scale': 30,
    #         'maxPixels': 1e9#     .get('ST_B10') \
    #     .getInfo()

    # print('Minimum temperature in AOI', AOI_min)
    # print('Maximum temperature in AOI', AOI_max)

    # Visualize
    Map.centerObject(AOI)
    Map.addLayer(collectionSummer, {'palette': [
        '1a3678', '2955bc', '5699ff', '8dbae9', 'acd1ff', 'caebff', 'e5f9ff',
        'fdffb4', 'ffe6a2', 'ffc969', 'ffa12d', 'ff7c1f', 'ca531a', 'ff0000',
        'ab0000'
    ]  # , 'min': AOI_min, 'max': AOI_max

    }, 'LST')

    # Export
    ee.batch.Export.image.toDrive({
        'image': collectionSummer,
        'description': id1 + "_Summer",
        'folder': country,
        'region': AOI,
        'scale': 30,
        'maxPixels': 1e9
    })
