
var folder = "users/gbenz/June30";
var folder_ref = folder.split("/")[2] + "/";
print(folder_ref);
//Define Dates and Labels
var season = "Summer";
//var year = "16"
//var NTL_time = "2013-06-01, 2023-06-01"
var NTL_time = ee.DateRange('2013-06-01', '2023-06-01');
var NDVI_2022 = ee.DateRange('2022-01-01', '2023-01-01');

var year = "2022";
// NDVI and LST Date Range
var hot_begin = '06'; //month
var day_begin = '-01';
var hot_end = '08'; //month
var day_end = '-31';
//var date = ee.Filter.date('20' + year + '-' + hot_begin + day_begin,'20' + year + '-' + hot_end + day_end);

var range0 = ee.Filter.date('2015-' + hot_begin + day_begin,'2015-' + hot_end + day_end);
var range1 = ee.Filter.date('2016-' + hot_begin + day_begin,'2016-' + hot_end + day_end);
var range2 = ee.Filter.date('2017-' + hot_begin + day_begin,'2017-' + hot_end + day_end);
var range3 = ee.Filter.date('2020-' + hot_begin + day_begin,'2020-' + hot_end + day_end);
var range4 = ee.Filter.date('2021-' + hot_begin + day_begin,'2021-' + hot_end + day_end);
var range5 = ee.Filter.date('2022-' + hot_begin + day_begin,'2022-' + hot_end + day_end);

var rangefilter = ee.Filter.or(range1, range2, range3, range4, range5);

//Define Functions outside of 'For' loop
function maskS2clouds(image) {
  var qa = image.select('QA60');

  // Bits 10 and 11 are clouds and cirrus, respectively.
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;

  // Both flags should be set to zero, indicating clear conditions.
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0)
      .and(qa.bitwiseAnd(cirrusBitMask).eq(0));

  return image.updateMask(mask).divide(10000);
}

function applyScaleFactors(image) {
  var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
  var saturationMask = image.select('QA_RADSAT').eq(0);
  var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
  var thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0);
  return image.addBands(opticalBands, null, true)
              .addBands(thermalBands, null, true)
              .updateMask(qaMask)
              .updateMask(saturationMask);
}
//Functions for VIIRS:
var addTime = function(image) {
  return image.addBands(image.metadata('system:time_start')
    .divide(1000 * 60 * 60 * 24 * 365));
};

var assetList = ee.data.listAssets(folder)['assets']
                    .map(function(d) { return d.id });

var loopCount = assetList.length;

for (var i = 0; i < loopCount; i++) {
  
  var id = assetList[i].split("/")[3];
  print("Working on:" + id);
  var table = ee.FeatureCollection('users/gbenz/'+folder_ref+id);
//var id = "AAA_Areni_AOI";

Map.centerObject(table, 12);

//Step 2: Access the Sentinel-2 Level-2A data and filter it for all the the images of the year 2020 that lie within the geometries boundaries. Keep only the relevant bands and filter for cloud coverage.
var s2a_Season = ee.ImageCollection('COPERNICUS/S2')
                  .filterBounds(table)
                  .filter(rangefilter)
           //       .select('B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B11','B12','QA60')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                  .map(maskS2clouds);
                  
var S2a_RecentAnnual = ee.ImageCollection('COPERNICUS/S2')
                  .filterBounds(table)
                  .filterDate(NDVI_2022)
           //       .select('B1','B2','B3','B4','B5','B6','B7','B8','B8A','B9','B11','B12','QA60')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                  .map(maskS2clouds);
                  
//Print your ImageCollection to your console tab to inspect it
print(s2a_Season, 'S2A');
print(S2a_RecentAnnual, 'S2A');

//Map.centerObject(s2a,9)

//Step 3: Create a single Image by reducing by Median and clip it to the extent of the geometry
var s2a_med_Season = s2a_Season.median()
                    .clip(table);
var s2a_med_RecentAnnual = S2a_RecentAnnual.median()
                    .clip(table);
                    
var nir_season = s2a_med_Season.select('B8');
var red_season = s2a_med_Season.select('B4');
var ndvi_Season = nir_season.subtract(red_season).divide(nir_season.add(red_season)).rename('NDVI');
print(ndvi_Season, 'NDVI: Season');

var nir_recent = s2a_med_RecentAnnual.select('B8');
var red_recent = s2a_med_RecentAnnual.select('B4');
var ndvi_recentannual = nir_recent.subtract(red_recent).divide(nir_recent.add(red_recent)).rename('NDVI');
print(ndvi_recentannual, 'NDVI: Recent');

// Display the result.
var ndviParams = {min: -1, max: 1, palette: ['blue', 'white', 'green']};
Map.addLayer(ndvi_Season, ndviParams, id + ' NDVI Seasonal ', false);
Map.addLayer(ndvi_recentannual, ndviParams, id +' NDVI Recent Annual ', false);

//Print your Image to your console tab to inspect it
print(s2a_med_Season, 'Median reduced Image Lebanon July 2020');
print(s2a_med_RecentAnnual, 'Median reduced Image Lebanon July 2020');

//Add your Image as a map layer
var visParams = {'min': 400,'max': [4000,3000,3000],   'bands':'B8,B4,B3'};
Map.addLayer(s2a_med_Season, visParams,id + 'Sentinel-2 Median', false);
//Map.centerObject(Extent);

var gt_threshold = 0.2;

//MORE VALUABLE TO SHOW RANGE OF NDVI VALUES
//COULD CATEGORIZE NDVI BY THRESHOLD:
//1. (WATER) 2. (BUA) 3. (SHRUB/GRASS) 4. (DENSE VEG) 5. (VERY DENSE)
//var Greenspace_Season = ndvi_Season.gt(gt_threshold)
//var Greenspace_RecAnnual = ndvi_recentannual.gt(gt_threshold)

Map.addLayer(ndvi_Season,{palette: ['green','blue']},id + ' NDVI: Season');
Map.addLayer(ndvi_recentannual,{palette: ['green','blue']},id + ' NDVI: Recent Annual');

// //////////////////EXPORT RESULTS TO GOOGLE DRIVE//////////////////////////////

//Export final flood layer
Export.image.toDrive({
  image: ndvi_Season,
  description: id + '_NDVI_Season',
  region: table,
  scale: 10,
  folder: 'CRP_'+id,
  maxPixels: 1e9
});

Export.image.toDrive({
  image: ndvi_recentannual, 
  description: id + "_NDVI_Annual",
  folder: "CRP_" + id,
  region: table,
  scale: 10,
  maxPixels: 1e9
});

var viirs_Collection = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG");
Map.setOptions('SATELLITE');

// NIGHT TIME LIGHT

Map.addLayer(table, {},id + 'Area of Interest');

var viirs_cf_cvg = viirs_Collection.select('avg_rad');

var viirs_with_time = viirs_Collection.filterDate(NTL_time).map(addTime);

// print(viirs_with_time);

var linear_fit = viirs_with_time.select(['system:time_start', 'avg_rad'])
  // Compute the linear trend over time.
  .reduce(ee.Reducer.linearFit())
  .clip(table);
Map.addLayer(linear_fit, '',id + 'Linear Fit', false);

//var SumVis = {min: 0, max: 5000, palette: ['00FFFF', '0000FF']};
//Map.addLayer(ndwi, ndwiViz, 'NDWI', false);

var sum_of_light = viirs_with_time.select(['system:time_start', 'avg_rad'])
  // Compute the sum over time.
  .reduce(ee.Reducer.sum())
  .clip(table);
Map.addLayer(sum_of_light,'' ,id + 'sum of light', false);

// // // //////////////////EXPORT RESULTS TO GOOGLE DRIVE//////////////////////////////
//var folder = "Africa_Workshop"

Export.image.toDrive({
  image: linear_fit.select('scale'),
  description: id + '_linfit',
  folder: 'CRP_'+id,
  region: table,
  scale: 100,
  maxPixels: 1e9
});
Export.image.toDrive({
  image: sum_of_light.select('avg_rad_sum'),
  description: id + '_avg_rad_sum',
  folder: 'CRP_'+id,
  region: table,
  scale: 100,
  maxPixels: 1e9
});

//FOREST COVER

var fc = ee.Image("UMD/hansen/global_forest_change_2018_v1_6");

var deforestation0018 = fc.select('loss').eq(1).clip(table).rename('fcloss0018');
var forestCover00 = fc.select('treecover2000').gte(20).clip(table);
var forestCoverGain0018 = fc.select('gain').eq(1).clip(table);
var forestCover18 = (forestCover00.subtract(deforestation0018).add(forestCoverGain0018)).gte(1).rename('fc00');

Map.addLayer(deforestation0018.mask(deforestation0018),{palette: ['red']},id + 'deforestation 2000-2018', false);
Map.addLayer(forestCover18.mask(forestCover18),{palette: ['green']},id + 'forest cover 2018', false);

var fc18Andfcloss = deforestation0018.addBands(forestCover18);

Map.addLayer(fc18Andfcloss,{},id + 'fc18Andfcloss', false);

// //////////////////EXPORT RESULTS TO GOOGLE DRIVE//////////////////////////////

//Export final flood layer
Export.image.toDrive({
  image: forestCover18,
  description: id + '_ForestCover18',
  region: table,
  scale: 30,
  folder: 'CRP_'+id,
  maxPixels: 1e9
});
Export.image.toDrive({
  image: deforestation0018,
  description: id + '_Deforestation',
  region: table,
  scale: 30,
  folder: 'CRP_'+id,
  maxPixels: 1e9
});

}