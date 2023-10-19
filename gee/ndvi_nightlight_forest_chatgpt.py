import ee

# Authenticate to Earth Engine
ee.Authenticate()
ee.Initialize()

# Define the folder
folder = "users/gbenz/June30"
folder_ref = folder.split("/")[2] + "/"
print(folder_ref)

# Define Dates and Labels
season = "Summer"
year = "2022"
NTL_time = ee.DateRange('2013-06-01', '2023-06-01')
NDVI_2022 = ee.DateRange('2022-01-01', '2023-01-01')

# NDVI and LST Date Range
hot_begin = '06'
day_begin = '-01'
hot_end = '08'
day_end = '-31'

range0 = ee.Filter.date('2015-' + hot_begin + day_begin, '2015-' + hot_end + day_end)
range1 = ee.Filter.date('2016-' + hot_begin + day_begin, '2016-' + hot_end + day_end)
range2 = ee.Filter.date('2017-' + hot_begin + day_begin, '2017-' + hot_end + day_end)
range3 = ee.Filter.date('2020-' + hot_begin + day_begin, '2020-' + hot_end + day_end)
range4 = ee.Filter.date('2021-' + hot_begin + day_begin, '2021-' + hot_end + day_end)
range5 = ee.Filter.date('2022-' + hot_begin + day_begin, '2022-' + hot_end + day_end)

rangefilter = ee.Filter.Or(range1, range2, range3, range4, range5)

# Define Functions outside of 'For' loop
def maskS2clouds(image):
    qa = image.select('QA60')

    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

    return image.updateMask(mask).divide(10000)

def applyScaleFactors(image):
    qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
    saturationMask = image.select('QA_RADSAT').eq(0)
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(opticalBands, None, True).addBands(thermalBands, None, True).updateMask(qaMask).updateMask(saturationMask)

# Functions for VIIRS
def addTime(image):
    return image.addBands(image.metadata('system:time_start').divide(1000 * 60 * 60 * 24 * 365))

# Get a list of assets in the specified folder
assetList = ee.data.listAssets(folder)['assets'].map(lambda d: d['id'])
loopCount = assetList.length().getInfo()

for i in range(loopCount):
    id = assetList[i].split("/")[3]
    print("Working on:" + id)
    table = ee.FeatureCollection('users/gbenz/' + folder_ref + id)

    # Step 2: Access the Sentinel-2 Level-2A data and filter it
    s2a_Season = (ee.ImageCollection('COPERNICUS/S2')
                  .filterBounds(table)
                  .filter(rangefilter)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                  .map(maskS2clouds))

    S2a_RecentAnnual = (ee.ImageCollection('COPERNICUS/S2')
                        .filterBounds(table)
                        .filterDate(NDVI_2022)
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                        .map(maskS2clouds))

    print(s2a_Season, 'S2A')
    print(S2a_RecentAnnual, 'S2A')

    # Step 3: Create a single Image by reducing by Median and clip it
    s2a_med_Season = (s2a_Season.median()
                     .clip(table))
    s2a_med_RecentAnnual = (S2a_RecentAnnual.median()
                           .clip(table))

    nir_season = s2a_med_Season.select('B8')
    red_season = s2a_med_Season.select('B4')
    ndvi_Season = nir_season.subtract(red_season).divide(nir_season.add(red_season)).rename('NDVI')
    print(ndvi_Season, 'NDVI: Season')

    nir_recent = s2a_med_RecentAnnual.select('B8')
    red_recent = s2a_med_RecentAnnual.select('B4')
    ndvi_recentannual = nir_recent.subtract(red_recent).divide(nir_recent.add(red_recent)).rename('NDVI')
    print(ndvi_recentannual, 'NDVI: Recent')

    # Display the result
    ndviParams = {'min': -1, 'max': 1, 'palette': ['blue', 'white', 'green']}
    print(id + ' NDVI Seasonal')
    print(id + ' NDVI Recent Annual')

    # Export results to Google Drive
    task1 = ee.batch.Export.image.toDrive(image=ndvi_Season,
                                         description=id + '_NDVI_Season',
                                         region=table,
                                         scale=10,
                                         folder='CRP_' + id,
                                         maxPixels=1e9)
    task1.start()

    task2 = ee.batch.Export.image.toDrive(image=ndvi_recentannual,
                                         description=id + '_NDVI_Annual',
                                         folder="CRP_" + id,
                                         region=table,
                                         scale=10,
                                         maxPixels=1e9)
    task2.start()

    viirs_Collection = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
    task3 = viirs_Collection.map(addTime)
    Map.setOptions('SATELLITE')

    # Night Time Light
    viirs_cf_cvg = viirs_Collection.select('avg_rad')
    viirs_with_time = viirs_Collection.filterDate(NTL_time).map(addTime)

    linear_fit = viirs_with_time.select(['system:time_start', 'avg_rad']).reduce(ee.Reducer.linearFit()).clip(table)
    Map.addLayer(linear_fit, '', id + 'Linear Fit', False)

    sum_of_light = viirs_with_time.select(['system:time_start', 'avg_rad']).reduce(ee.Reducer.sum()).clip(table)
    Map.addLayer(sum_of_light, '', id + 'sum of light', False)

    # Export results to Google Drive
    task4 = ee.batch.Export.image.toDrive(image=linear_fit.select('scale'),
                                         description=id + '_linfit',
                                         folder='CRP_' + id,
                                         region=table,
                                         scale=100,
                                         maxPixels=1e9)
    task4.start()

    task5 = ee.batch.Export.image.toDrive(image=sum_of_light.select('avg_rad_sum'),
                                         description=id + '_avg_rad_sum',
                                         folder='CRP_' + id,
                                         region=table,
                                         scale=100,
                                         maxPixels=1e9)
    task5.start()

    # Forest Cover
    fc = ee.Image("UMD/hansen/global_forest_change_2018_v1_6")
    deforestation0018 = fc.select('loss').eq(1).clip(table).rename('fcloss0018')
    forestCover00 = fc.select('treecover2000').gte(20).clip(table)
    forestCoverGain0018 = fc.select('gain').eq(1).clip(table)
    forestCover18 = (forestCover00.subtract(deforestation0018).add(forestCoverGain0018)).gte(1).rename('fc00')

    Map.addLayer(deforestation0018.mask(deforestation0018), {'palette': ['red']}, id + 'deforestation 2000-2018', False)
    Map.addLayer(forestCover18.mask(forestCover18), {'palette': ['green']}, id + 'forest cover 2018', False)

    fc18Andfcloss = deforestation0018.addBands(forestCover18)

    Map.addLayer(fc18Andfcloss, {}, id + 'fc18Andfcloss', False)

    # Export results to Google Drive
    task6 = ee.batch.Export.image.toDrive(image=forestCover18,
                                         description=id + '_ForestCover18',
                                         region=table,
                                         scale=30,
                                         folder='CRP_' + id,
                                         maxPixels=1e9)
    task6.start()

    task7 = ee.batch.Export.image.toDrive(image=deforestation0018,
                                         description=id + '_Deforestation',
                                         region=table,
                                         scale=30,
                                         folder='CRP_' + id,
                                         maxPixels=1e9)
    task7.start()
