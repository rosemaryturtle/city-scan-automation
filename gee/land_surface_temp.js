var landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2");
    
// Set parameter
var AOI = Tshikapa;  // update this for each AOI
var id = "Tshikapa"; // update this for each AOI
var id1 = id.toLowerCase();
var country = 'DRC';  // update this for each country and make an eponymous folder in google drive, as the destination of exported outputs

// Filter for hottest months in the past X years
var years = ['2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022'];
var month0 = '02'; // first hottest month  // update for each country
var month1 = '05'; // end of hottest month (note that this is exclusive)  // update for each country

function filter_hot_month(index) {
  return ee.Filter.date(years[index]+'-'+month0+'-01', years[index]+'-'+month1+'-01');
}

var range0 = filter_hot_month(0);
var range1 = filter_hot_month(1);
var range2 = filter_hot_month(2);
var range3 = filter_hot_month(3);
var range4 = filter_hot_month(4);
var range5 = filter_hot_month(5);
var range6 = filter_hot_month(6);
var range7 = filter_hot_month(7);
var range8 = filter_hot_month(8);
var range9 = filter_hot_month(9);

var rangefilter = ee.Filter.or(range0, range1, range2, range3, range4, range5, range6, range7, range8, range9);

// Define a function to scale the data and mask unwanted pixels
var maskL457sr = function(image) {
  // Bit 0 - Fill
  // Bit 1 - Dilated Cloud
  // Bit 2 - Cirrus (high confidence)
  // Bit 3 - Cloud
  // Bit 4 - Cloud Shadow
  var qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0);
  var saturationMask = image.select('QA_RADSAT').eq(0);

  // Apply the scaling factors to the appropriate bands.
  var thermalBand = image.select('ST_B10').multiply(0.00341802).add(149.0);

  // Replace the original bands with the scaled ones and apply the masks.
  return image.addBands(thermalBand, null, true)
      .updateMask(qaMask)
      .updateMask(saturationMask);
};

// Apply filter and mask
var collectionSummer= landsat
  .filter(rangefilter)
  .filterBounds(AOI)
  // .filterMetadata('CLOUD_COVER','less_than', 20)
  .map(maskL457sr)
  .select('ST_B10')
  .mean()
  .add(-273.15)
  .clip(AOI);

// Find minimum and maximum temperatures in AOI to set visualization parameters
// var AOI_min = collectionSummer
// .reduceRegion({
//   reducer: ee.Reducer.min(),
//   geometry: AOI,
//   scale: 30,
//   maxPixels: 1e9
// })
// .get('ST_B10')
// .getInfo();

// var AOI_max = collectionSummer
// .reduceRegion({
//   reducer: ee.Reducer.max(),
//   geometry: AOI,
//   scale: 30,
//   maxPixels: 1e9
// })
// .get('ST_B10')
// .getInfo();

// print('Minimum temperature in AOI', AOI_min);
// print('Maximum temperature in AOI', AOI_max);

// Visualize
Map.centerObject(AOI);
Map.addLayer(collectionSummer, {palette: [
  '1a3678', '2955bc', '5699ff', '8dbae9', 'acd1ff', 'caebff', 'e5f9ff',
  'fdffb4', 'ffe6a2', 'ffc969', 'ffa12d', 'ff7c1f', 'ca531a', 'ff0000',
  'ab0000'
]//, min: AOI_min, max: AOI_max
  
},'LST');

// Export
Export.image.toDrive({
  image: collectionSummer, 
  description: id1 + "_Summer",
  folder: country,
  region: AOI,
  scale: 30,
  maxPixels: 1e9
});
