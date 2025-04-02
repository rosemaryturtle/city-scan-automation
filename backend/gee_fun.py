import ee

# Initialize Earth Engine
ee.Initialize()

def flatten_to_2d(geom):
    import shapely
    
    if geom.has_z:
        # If it's a Polygon, handle the exterior and any interiors (holes)
        if geom.geom_type == 'Polygon':
            # Convert to 2D by ignoring the Z coordinate
            new_exterior = [(x, y) for x, y, _ in geom.exterior.coords]
            new_interiors = [[(x, y) for x, y, _ in interior.coords] for interior in geom.interiors]
            return shapely.geometry.Polygon(new_exterior, new_interiors)
        
        # If it's a MultiPolygon, process each Polygon within it
        elif geom.geom_type == 'MultiPolygon':
            new_polygons = []
            for polygon in geom.geoms:
                new_exterior = [(x, y) for x, y, _ in polygon.exterior.coords]
                new_interiors = [[(x, y) for x, y, _ in interior.coords] for interior in polygon.interiors]
                new_polygons.append(shapely.geometry.Polygon(new_exterior, new_interiors))
            return shapely.geometry.MultiPolygon(new_polygons)
    
    # Return the geometry unchanged if it does not have Z coordinates or is not a Polygon/MultiPolygon
    return geom

def aoi_to_ee_geometry(aoi_file):
    import shapely

    # Remove Z coordinates (convert to 2D)
    aoi_file['geometry'] = aoi_file['geometry'].apply(flatten_to_2d)
    
    AOI = ee.Geometry(shapely.geometry.mapping(aoi_file.unary_union))
    
    return AOI

def filter_season_months(city_name_l, aoi_file, local_output_dir, first_year, last_year, data_bucket, cloud_bucket, output_dir, season):
    # Check if argument is valid ------------
    if season == 'summer':
        est = 'hottest'
    elif season == 'winter':
        est = 'coldest'
    else:
        print('filter_season_months function error')
        print('season argument invalid')
        exit()

    import math
    import utils
    import io
    import xarray as xr
    import numpy as np
    from os.path import exists

    centroid = aoi_file.centroid

    # Identify seasonal months using CRU data ----------------------
    if not exists(f'{local_output_dir}/{city_name_l}_{est}_months.txt'):
        temp_dict = {}
        for i in range(math.floor(first_year / 10) * 10, math.ceil(last_year / 10) * 10, 10):
            if i >= 2020:
                nc = xr.open_dataset(io.BytesIO(utils.read_blob_to_memory(data_bucket, 'CRU/tmp/cru_ts4.08.2021.2023.tmp.dat.nc')))  # TODO: make it easier to update to new CRU versions
            else:
                nc = xr.open_dataset(io.BytesIO(utils.read_blob_to_memory(data_bucket, f'CRU/tmp/cru_ts4.08.{i+1}.{i+10}.tmp.dat.nc')))

            for month in range(1, 13):
                temp_dict[month] = []
                for year in range(max(i, first_year), min(i+11, last_year+1)):
                    time = str(year) + '-' + str(month) + '-15'
                    val = nc.sel(lon = centroid.x[0], lat = centroid.y[0], time = time, method = 'nearest')['tmp'].to_dict()['data']
                    temp_dict[month].append(val)
                temp_dict[month] = np.nanmean(temp_dict[month])
        
        avg_temp_dict = {}
        for month in range(1, 13):
            avg_temp_dict[(month-1)%12+1] = np.nanmean([temp_dict[(month-1)%12+1], temp_dict[(month)%12+1], temp_dict[(month+1)%12+1]])

        first_est_months = max(zip(avg_temp_dict.values(), avg_temp_dict.keys()))[1]
        est_months = [first_est_months, (first_est_months)%12+1, (first_est_months+1)%12+1]
        
        # Write seasonal months to text ---------------------------
        with open(f'{local_output_dir}/{city_name_l}_{est}_months.txt', 'w') as file:
            # Write each number to the file on a new line
            for number in est_months:
                file.write(f"{number}\n")
        
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{est}_months.txt', f'{output_dir}/{city_name_l}_{est}_months.txt')
    else:
        est_months = []
        with open(f'{local_output_dir}/{city_name_l}_{est}_months.txt') as file:
            for line in file:
                # Convert each line to an integer and append to the list
                est_months.append(int(line.strip()))

    # Date filter -----------------
    def ee_filter_month(month):
        if 1 <= month <= 11:
            return [ee.Filter.date(f'{year}-{str(month).zfill(2)}-01', f'{year}-{month+1}-01') for year in range(first_year, last_year + 1)]
        elif month == 12:
            return [ee.Filter.date(f'{year}-12-01', f'{year+1}-01-01') for year in range(first_year, last_year + 1)]
        else:
            return
    
    range_list0 = ee_filter_month(est_months[0])
    range_list1 = ee_filter_month(est_months[1])
    range_list2 = ee_filter_month(est_months[2])

    rangefilter = ee.Filter.Or(range_list0 + range_list1 + range_list2)

    return rangefilter

def gee_landcover(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir):
    print('run gee_landcover')

    import csv

    # SET UP #########################################
    AOI = aoi_to_ee_geometry(aoi_file)
    lc = ee.ImageCollection('ESA/WorldCover/v200').first()


    # PROCESSING #####################################
    lc_aoi = lc.clip(AOI)

    # Calculate stats -----------------------
    # Calculate the pixel counts for each land cover type
    lc_hist = lc_aoi.reduceRegion(
        reducer=ee.Reducer.frequencyHistogram(),
        geometry=AOI,
        # scale=10,
        maxPixels=1e10
    )
    lc_hist1 = lc_hist.getInfo()['Map']
    
    # Create a dictionary to store the counts
    counts_dict = {}

    # Create value dictionary
    class_values = {
        10: 'Tree cover',
        20: 'Shrubland',
        30: 'Grassland',
        40: 'Cropland',
        50: 'Built-up',
        60: 'Bare / sparse vegetation',
        70: 'Snow and ice',
        80: 'Permanent water bodies',
        90: 'Herbaceous wetland',
        95: 'Mangroves',
        100: 'Moss and lichen'
    }

    # Populate the dictionary with counts for each land cover type
    for class_val in class_values:
        class_name = class_values[class_val]
        count = lc_hist1.get(str(class_val), 0)
        counts_dict[class_name] = count

    # Write the counts dictionary to a CSV file
    with open(f'{local_output_dir}/{city_name_l}_lc.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Land Cover Type', 'Pixel Count'])
        writer.writeheader()
        for class_name, count in counts_dict.items():
            writer.writerow({'Land Cover Type': class_name, 'Pixel Count': count})

    # Export results to Google Cloud Storage bucket ------------------
    no_data_val = -9999
    lc_aoi = lc_aoi.unmask(value = no_data_val, sameFootprint = False)
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': lc_aoi,
                                                    'description': f'{city_name_l}_lc',
                                                    'region': AOI,
                                                    'scale': 10,
                                                    'bucket': cloud_bucket,
                                                    'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_lc",
                                                    'maxPixels': 1e10,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task0.start()
    
    return [f"{output_dir}/spatial/{city_name_l}_lc.tif"]

#Landcover graph Tree
def gee_landcover_stats(cloud_bucket, city_name, city_name_l, local_output_dir, output_dir, render_dir, font_dict):
    from os.path import exists
    lc_stats_file = f"{local_output_dir}/{city_name_l}_lc.csv"
    
    if exists(lc_stats_file):
        import pandas as pd
        import matplotlib.pyplot as plt
        import plotly.express as px
        import squarify
        import utils
        import yaml

        lc_stats = pd.read_csv(lc_stats_file)
        
        lc_stats = lc_stats[lc_stats['Pixel Count'] > 0]
        
        lc_colors = {
            "Tree cover": "#397e48",
            "Built-up": "#c4281b",
            "Grassland": "#88af52",
            "Bare / sparse vegetation": "#a59b8f",
            "Cropland": "#e49634",
            "Water bodies": "#429bdf",
            "Permanent water bodies": "#00008b",
            "Mangroves": "#90EE90",
            "Moss and lichen": "#013220",
            "Shrubland": "#dfc25a",
            "Herbaceous wetland": "#7d87c4",
            "Snow and ice": "#F5F5F5"
        }
        
        total_pixels = lc_stats['Pixel Count'].sum()
        lc_stats['Percentage'] = lc_stats['Pixel Count'] / total_pixels * 100
        
        
        plt.figure(figsize=(12, 8))
        squarify.plot(sizes=lc_stats['Pixel Count'], label=lc_stats['Land Cover Type'], 
                        color=[lc_colors[lc_type] for lc_type in lc_stats['Land Cover Type']], 
                        alpha=0.8, pad=True)
        plt.title(f"Land Cover Distribution of {city_name}")
        plt.axis('off')
        plt.tight_layout()

        render_path_png = f"{local_output_dir}/{city_name_l}_landcover_treemap.png"
        plt.savefig(render_path_png)
        plt.close()
        utils.upload_blob(cloud_bucket, render_path_png, f'{render_dir}/{city_name_l}_landcover_treemap.png', type='render')
        
        fig = px.treemap(lc_stats, path=['Land Cover Type'], values='Pixel Count', color='Land Cover Type', 
                            color_discrete_map=lc_colors)
        
        fig.update_traces(textinfo='label+percent entry', textposition='middle center')
        fig.update_layout(margin=dict(t=50, l=25, r=25, b=25),font=font_dict)
        
        render_path_html = f"{local_output_dir}/{city_name_l}_landcover_treemap.html"
        fig.write_html(render_path_html, full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, render_path_html, f'{render_dir}/{city_name_l}_landcover_treemap.html', type='render')

        highest_values = lc_stats.sort_values(by='Percentage', ascending=False).head(3)
        ordinal_dict = {1: "first", 2: "second", 3: "third"}
        lc_text_dict = {}
        for i, (index, row) in enumerate(highest_values.iterrows()):
            ordinal_str = ordinal_dict.get(i + 1, str(i + 1) + "th")
            lc_text_dict[ordinal_str] = f"The {ordinal_str} highest landcover value is {row['Land Cover Type']} with {row['Percentage']:.2f}% of the total land area".replace('first ', '')
        
        with open(f'{local_output_dir}/{city_name_l}_lc_stats.yml', 'w') as file:
            yaml.dump(lc_text_dict, file)
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_lc_stats.yml', f'{output_dir}/{city_name_l}_lc_stats.yml')

def gee_elevation(city_name_l, aoi_file, cloud_bucket, output_dir):
    print('run gee_elevation')

    import geopandas as gpd
    
    # SET UP #########################################
    aoi_file_buf = gpd.GeoDataFrame(geometry=aoi_file.buffer(0.001))
    AOI_buf = aoi_to_ee_geometry(aoi_file_buf)
    AOI = aoi_to_ee_geometry(aoi_file)
    elevation = ee.Image("USGS/SRTMGL1_003")


    # PROCESSING #####################################
    no_data_val = -9999
    elevation_clip_buf = elevation.clip(AOI_buf).unmask(value = no_data_val, sameFootprint = False)
    elevation_clip = elevation.clip(AOI).unmask(value = no_data_val, sameFootprint = False)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': elevation_clip,
                                                    'description': f'{city_name_l}_elevation',
                                                    'region': AOI,
                                                    'scale': 30,
                                                    'bucket': cloud_bucket,
                                                    'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_elevation",
                                                    'maxPixels': 1e10,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{'image': elevation_clip_buf,
                                                    'description': f'{city_name_l}_elevation_buf',
                                                    'region': AOI_buf,
                                                    'scale': 30,
                                                    'bucket': cloud_bucket,
                                                    'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_elevation_buf",
                                                    'maxPixels': 1e10,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task1.start()

    return [f"{output_dir}/spatial/{city_name_l}_elevation.tif", f"{output_dir}/spatial/{city_name_l}_elevation_buf.tif"]

def gee_forest(city_name_l, aoi_file, cloud_bucket, output_dir):
    print('run gee_forest')
    
    # SET UP #########################################
    AOI = aoi_to_ee_geometry(aoi_file)
    fc = ee.Image("UMD/hansen/global_forest_change_2023_v1_11")


    # PROCESSING #####################################
    no_data_val = 0

    deforestation0023 = fc.select('loss').eq(1).clip(AOI).unmask(value = no_data_val, sameFootprint = False).rename('fcloss0023')
    forestCover00 = fc.select('treecover2000').gte(20).clip(AOI)
    # note: forest gain is only updated until 2012
    forestCoverGain0012 = fc.select('gain').eq(1).clip(AOI)
    forestCover23 = forestCover00.subtract(deforestation0023).add(forestCoverGain0012).gte(1).rename('fc23').unmask(value = no_data_val, sameFootprint = False)
    deforestation_year = fc.select('lossyear').clip(AOI).unmask(value = no_data_val, sameFootprint = False)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{'image': forestCover23,
                                                    'description': f'{city_name_l}_forest_cover23',
                                                    'region': AOI,
                                                    'scale': 30.92,
                                                    'bucket': cloud_bucket,
                                                    'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_forest_cover23",
                                                    'maxPixels': 1e10,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{'image': deforestation_year,
                                                    'description': f'{city_name_l}_deforestation',
                                                    'region': AOI,
                                                    'scale': 30.92,
                                                    'bucket': cloud_bucket,
                                                    'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_deforestation",
                                                    'maxPixels': 1e10,
                                                    'fileFormat': 'GeoTIFF',
                                                    'formatOptions': {
                                                        'cloudOptimized': True,
                                                        'noData': no_data_val
                                                    }})
    task1.start()

    return [f"{output_dir}/spatial/{city_name_l}_forest_cover23.tif", f"{output_dir}/spatial/{city_name_l}_deforestation.tif"]

def gee_lst(city_name_l, aoi_file, local_output_dir, first_year, last_year, data_bucket, cloud_bucket, output_dir, season):
    print('run gee_lst')
    
    # SET UP #########################################
    AOI = aoi_to_ee_geometry(aoi_file)
    landsat = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")


    # GEE PARAMETERS ################################
    # Date filter -----------------
    rangefilter = filter_season_months(city_name_l, aoi_file, local_output_dir, first_year, last_year, data_bucket, cloud_bucket, output_dir, season)

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
    no_data_val = -9999
    collection_season = landsat.filter(rangefilter).filterBounds(AOI).map(maskL457sr).select('ST_B10').mean().add(-273.15).clip(AOI).unmask(value = no_data_val, sameFootprint = False)
    task = ee.batch.Export.image.toCloudStorage(**{
        'image': collection_season,
        'description': f"{city_name_l}_{season}",
        'bucket': cloud_bucket,
        'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_{season}",
        'region': AOI,
        'scale': 30,
        'maxPixels': 1e10,
        'fileFormat': 'GeoTIFF',
        'formatOptions': {
            'cloudOptimized': True,
            'noData': no_data_val
        }
    })
    task.start()

    return [f"{output_dir}/spatial/{city_name_l}_{season}.tif"]

def gee_ndxi(city_name_l, aoi_file, local_output_dir, first_year, last_year, data_bucket, cloud_bucket, output_dir, index_type):
    print(f'run gee_{index_type}')

    # Check if argument is valid ------------
    if not index_type in ['ndmi', 'ndvi']:
        print('gee_ndxi function error')
        print('index_type argument invalid')
        exit()
    
    # SET UP #########################################
    AOI = aoi_to_ee_geometry(aoi_file)


    # GEE PARAMETERS #####################################
    # Date filter -----------------
    rangefilter = filter_season_months(city_name_l, aoi_file, local_output_dir, first_year, last_year, data_bucket, cloud_bucket, output_dir, season = 'summer')

    # Functions --------------------
    def maskS2clouds(image):
        qa = image.select('QA60')

        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11

        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))

        return image.updateMask(mask).divide(10000)


    # PROCESSING #########################################
    no_data_val = -9999
    
    s2a_Season = ee.ImageCollection('COPERNICUS/S2_HARMONIZED').filterBounds(AOI).filter(rangefilter).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).map(maskS2clouds)
    s2a_med_Season = s2a_Season.median().clip(AOI).unmask(value = no_data_val, sameFootprint = False)

    if index_type == 'ndmi':
        ndxi_Season = s2a_med_Season.normalizedDifference(['B8', 'B11']).rename('NDMI')
    elif index_type == 'ndvi':
        ndxi_Season = s2a_med_Season.normalizedDifference(['B8', 'B4']).rename('NDVI')

    # Export results to Google Cloud Storage bucket ------------------
    task = ee.batch.Export.image.toCloudStorage(**{
        'image': ndxi_Season,
        'description': f'{city_name_l}_{index_type}_season',
        'bucket': cloud_bucket,
        'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_{index_type}_season",
        'region': AOI,
        'scale': 10,
        'maxPixels': 1e10,
        'fileFormat': 'GeoTIFF',
        'formatOptions': {
            'cloudOptimized': True,
            'noData': no_data_val
        }
    })
    task.start()

    return [f"{output_dir}/spatial/{city_name_l}_{index_type}_season.tif"]

def gee_nightlight(city_name_l, aoi_file, cloud_bucket, output_dir):
    print('run gee_nightlight')
    
    # SET UP #########################################
    AOI = aoi_to_ee_geometry(aoi_file)
    viirs = ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")


    # GEE PARAMETERS #####################################
    # Date filter ----------------------
    max_date = viirs.reduceColumns(ee.Reducer.max(), ["system:time_start"]).get('max')

    NTL_time = ee.DateRange(ee.Date(max_date.getInfo()).advance(-10, 'year'), ee.Date(max_date.getInfo()))

    # Function ------------------------
    def addTime(image):
        return image.addBands(image.metadata('system:time_start').divide(1000 * 60 * 60 * 24 * 365))


    # PROCESSING #########################################
    no_data_val = -9999

    viirs_with_time = viirs.filterDate(NTL_time).map(addTime)

    linear_fit = viirs_with_time.select(['system:time_start', 'avg_rad']).reduce(ee.Reducer.linearFit()).clip(AOI).unmask(value = no_data_val, sameFootprint = False)
    sum_of_light = viirs_with_time.select(['system:time_start', 'avg_rad']).reduce(ee.Reducer.sum()).clip(AOI).unmask(value = no_data_val, sameFootprint = False)

    # Export results to Google Cloud Storage bucket ------------------
    task0 = ee.batch.Export.image.toCloudStorage(**{
        'image': linear_fit.select('scale'),
        'description': f'{city_name_l}_linfit',
        'bucket': cloud_bucket,
        'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_linfit",
        'region': AOI,
        'scale': 463.83,
        'maxPixels': 1e10,
        'fileFormat': 'GeoTIFF',
        'formatOptions': {
            'cloudOptimized': True,
            'noData': no_data_val
        }
    })
    task0.start()

    task1 = ee.batch.Export.image.toCloudStorage(**{
       'image': sum_of_light.select('avg_rad_sum'),
        'description': f'{city_name_l}_avg_rad_sum',
        'bucket': cloud_bucket,
        'fileNamePrefix': f"{output_dir}/spatial/{city_name_l}_avg_rad_sum",
        'region': AOI,
        'scale': 463.83,
        'maxPixels': 1e10,
        'fileFormat': 'GeoTIFF',
        'formatOptions': {
            'cloudOptimized': True,
            'noData': no_data_val
        }
    })
    task1.start()

    return [f"{output_dir}/spatial/{city_name_l}_linfit.tif", f"{output_dir}/spatial/{city_name_l}_avg_rad_sum.tif"]
