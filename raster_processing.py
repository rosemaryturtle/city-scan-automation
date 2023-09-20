import os
import sys
import math
import warnings
import yaml
import geopandas as gpd
from osgeo import gdal
import glob
import numpy as np
import rasterio.mask
import rasterio
import requests
from pathlib import Path
from rasterio.merge import merge
import json
from os.path import exists
import csv
from rasterio.warp import calculate_default_transform, reproject, Resampling

# SET UP ##############################################

print('welcome to city scan 2')

# load configuration file, this files stores the file locations for the global data files
# the global config file usually only needs to be changed once, depending on the user's local machine setup
# with open("global_data_config_personal_windows.yml", "r") as ymlfile:
#     cfg = yaml.safe_load(ymlfile)

# load city inputs files, to be updated for each city scan
with open("city_inputs.yml", 'r') as f:
    city_inputs = yaml.safe_load(f)

city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

# load global inputs, such as data sources that generally remain the same across scans
with open("global_inputs.yml", 'r') as f:
    global_inputs = yaml.safe_load(f)

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

# Read AOI shapefile --------
print('attempt to read AOI shapefile')
# transform the input shp to correct prj (epsg 4326)
aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)
features = aoi_file.geometry

# Define output folder ---------
output_folder = Path('output')

if not os.path.exists(output_folder):
    os.mkdir(output_folder)


# DOWNLOAD DATA ##########################################
data_folder = Path('data')

try:
    os.mkdir(data_folder)
except FileExistsError:
    pass

# Download and prepare WorldPop data ------------
if menu['population']:
    pop_folder = data_folder / 'pop'

    try:
        os.mkdir(pop_folder)
    except FileExistsError:
        pass

    # default population data source: WorldPop

    # use WorldPop API to query data URL
    wp_file_json = requests.get('https://hub.worldpop.org/rest/data/pop/cic2020_100m?iso3=' + city_inputs['country_iso3']).json()
    wp_file_list = wp_file_json['data'][0]['files']

    # check if the country's population raster has already been downloaded
    # download if the file does not already exist
    if not exists(pop_folder / (city_inputs['country_name'].replace(' ', '_').lower() + '_pop.tif')):
        if len(wp_file_list) > 1:
            # if more than one raster file is listed (uncommon), download each file and then mosaic them
            for f in wp_file_list:
                wp_file = requests.get(f)
                wp_file_name = f.split('/')[-1]
                
                open(pop_folder / wp_file_name, 'wb').write(wp_file.content)

            try:
                raster_to_mosaic = []
                mosaic_file = city_inputs['country_name'].replace(' ', '_').lower() + '_pop.tif'

                mosaic_list = os.listdir(pop_folder.iterdir())
                for p in mosaic_list:
                    if p.endswith('.tif'):
                        raster = rasterio.open(pop_folder / p)
                        raster_to_mosaic.append(raster)

                mosaic, output = merge(raster_to_mosaic)
                output_meta = raster.meta.copy()
                output_meta.update(
                    {"driver": "GTiff",
                        "height": mosaic.shape[1],
                        "width": mosaic.shape[2],
                        "transform": output,
                    }
                )

                with rasterio.open(pop_folder / mosaic_file, 'w', **output_meta) as m:
                    m.write(mosaic)
            except MemoryError:
                print('MemoryError when merging population raster files.')
                print('Try GIS instead for merging.')
        elif len(wp_file_list) == 1:
            wp_file = requests.get(wp_file_list[0])
            wp_file_name = city_inputs['country_name'].replace(' ', '_').lower() + '_pop.tif'
            open(pop_folder / wp_file_name, 'wb').write(wp_file.content)
        else:
            print('No WorldPop file available')
            print('Use a different WorldPop dataset or another population data source')

# Download and prepare WSF evolution data ----------------
if menu['wsf']:
    wsf_folder = data_folder / 'wsf'

    try:
        os.mkdir(wsf_folder)
    except FileExistsError:
        pass

    aoi_bounds = aoi_file.bounds

    for i in range(len(aoi_bounds)):
        for x in range(math.floor(aoi_bounds.minx[i] - aoi_bounds.minx[i] % 2), math.ceil(aoi_bounds.maxx[i]), 2):
            for y in range(math.floor(aoi_bounds.miny[i] - aoi_bounds.miny[i] % 2), math.ceil(aoi_bounds.maxy[i]), 2):
                file_name = 'WSFevolution_v1_' + str(x) + '_' + str(y)
                if not exists(wsf_folder / (file_name + '.tif')):
                    file = requests.get('https://download.geoservice.dlr.de/WSF_EVO/files/' + file_name + '/' + file_name + '.tif')
                    open(wsf_folder / (file_name + '.tif'), 'wb').write(file.content)

    # count how many raster files have been downloaded
    def tif_counter(list):
        if list.endswith('.tif'):
            return True
        return False

    if len(list(filter(tif_counter, os.listdir(wsf_folder)))) > 1:
        try:
            raster_to_mosaic = []
            mosaic_file = city_name_l + '_wsf_evolution.tif'

            if not exists(wsf_folder / mosaic_file):
                mosaic_list = os.listdir(wsf_folder)
                for p in mosaic_list:
                    if p.endswith('.tif'):
                        raster = rasterio.open(wsf_folder / p)
                        raster_to_mosaic.append(raster)

                mosaic, output = merge(raster_to_mosaic)
                output_meta = raster.meta.copy()
                output_meta.update(
                    {"driver": "GTiff",
                        "height": mosaic.shape[1],
                        "width": mosaic.shape[2],
                        "transform": output,
                    }
                )

                with rasterio.open(wsf_folder / mosaic_file, 'w', **output_meta) as m:
                    m.write(mosaic)
        except MemoryError:
            print('MemoryError when merging WSF evolution raster files.') 
            print('Try GIS instead for merging.')
    elif len(list(filter(tif_counter, os.listdir(wsf_folder)))) == 1:
        os.rename(wsf_folder / (list(filter(tif_counter, os.listdir(wsf_folder)))[0]), wsf_folder / (city_name_l + '_wsf_evolution.tif'))
    else:
        print('No WSF evolution file available')

"""
# elevation

elevation_file = 'test'

tifCounter = len(glob.glob1('./04_elevation/', "*.tif"))

print('tifCounter, elevation files:')
print(tifCounter)

if tifCounter == 1:
    for name in glob.glob('./04_elevation/*.tif'):
        print('inside elevation glob single')
        print(name)
        elevation_file = name
elif tifCounter == 0:
    warnings.warn("there are no elevation files")
else:
    for name in glob.glob('./04_elevation/*merged.tif'):
        print('inside elevation glob multiple')
        print(name)
        elevation_file = name

if elevation_file == 'test':
    warnings.warn("Warning because there are multiple elevation files but no merged elevation file. Make sure to merge the elevation files and include the word 'merged' in the name of the file.")


# imperviousness
imperv_file = 'test'

print('go into imperviousness glob')
for name in glob.glob('./13_imperviousness/*imperviousness*.tif'):
    print('inside imperviousness glob')
    print(name)
    imperv_file = name
"""


# DEFINE FUNCTIONS #################################

# Raster clip functions ----------------
def clipdata(input_raster, data_type):
    with rasterio.open(input_raster) as src:
        # shapely presumes all operations on two or more features exist in the same Cartesian plane.
        out_image, out_transform = rasterio.mask.mask(
            src, features, crop=True)
        out_meta = src.meta.copy()

    out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

    with rasterio.open(output_folder / (city_name_l + '_' + data_type + '.tif'), "w", **out_meta) as dest:
        dest.write(out_image)

# Different from clipdata because wsf needs to be bucketed by year
def clipdata_wsf(input_raster):
    # automatically find utm zone
    avg_lng = features.unary_union.centroid.x

    # calculate UTM zone from avg longitude to define CRS to project to
    utm_zone = math.floor((avg_lng + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    # features = features.tolist()

    # clip
    with rasterio.open(input_raster) as src:
        # shapely presumes all operations on two or more features exist in the same Cartesian plane.
        out_image, out_transform = rasterio.mask.mask(
            src, features, crop=True)
        out_meta = src.meta.copy()

        out_meta.update({"driver": "GTiff",
                            "height": out_image.shape[1],
                            "width": out_image.shape[2],
                            "transform": out_transform})

        output_4326_raster_clipped = output_folder / (city_name_l + '_wsf_4326.tif')

        # save for stats
        with rasterio.open(output_4326_raster_clipped, "w", **out_meta) as dest:
            dest.write(out_image)

        # 3. need to transform the clipped ghsl to utm
        with rasterio.open(output_4326_raster_clipped) as src:
            transform, width, height = calculate_default_transform(
                src.crs, utm_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': utm_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            output_utm_raster_clipped = output_folder / (city_name_l + '_wsf_utm.tif')
            with rasterio.open(output_utm_raster_clipped, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=utm_crs,
                        resampling=Resampling.nearest)
        
        with rasterio.open(output_utm_raster_clipped) as src:
            pixelSizeX, pixelSizeY = src.res

            array = src.read()

            # Reclassify
            year_dict = {}
            for year in range(1985, 2016):
                # resolution of each pixel about 30 sq meters. Multiply by pixelSize and Divide by 1,000,000 to get sq km
                if year == 1985:
                    year_dict[year] = np.count_nonzero(
                    array == year) * pixelSizeX * pixelSizeY / 1000000
                else:
                    year_dict[year] = np.count_nonzero(
                        array == year) * pixelSizeX * pixelSizeY / 1000000 + year_dict[year-1]

            # save CSV
            with open(output_folder / (city_name_l + "_wsf_stats.csv"), 'w') as f:
                f.write("year,cumulative sq km\n")
                for key in year_dict.keys():
                    f.write("%s,%s\n" % (key, year_dict[key]))

        # Reclassify
        out_image[out_image < 1985] = 0
        out_image[(out_image <= 2015) & (out_image >= 2006)] = 4
        out_image[(out_image < 2006) & (out_image >= 1996)] = 3
        out_image[(out_image < 1996) & (out_image >= 1986)] = 2
        out_image[out_image == 1985] = 1

        output_4326_raster_clipped_reclass = output_folder / (city_name_l + '_wsf_4326_reclass.tif')

        # save for stats
        with rasterio.open(output_4326_raster_clipped_reclass, "w", **out_meta) as dest:
            dest.write(out_image)

"""
# Same as clipdata(), but set the nodata value to -99999
def clipdata_elev(admin_folder, input_raster, output_folder, prepend_file_text):

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):
            print(file)
            with fiona.open(admin_folder + '/' + file, "r") as shapefile:
                features = [feature["geometry"] for feature in shapefile]

                with rasterio.open(input_raster) as src:
                    out_image, out_transform = rasterio.mask.mask(src, features, crop = True, nodata = -99999)
                    out_meta = src.meta.copy()

                out_meta.update({"driver": "GTiff",
                                "height": out_image.shape[1],
                                "width": out_image.shape[2],
                                "transform": out_transform,
                                'nodata': -99999})

                with rasterio.open(output_folder + '/' + prepend_file_text + "_%s.tif" % file[:-4], "w", **out_meta) as dest:
                    dest.write(out_image)
"""


# RASTER PROCESSING ################################

print('starting processing')

# population
if menu['population']:
    clipdata(pop_folder / (city_inputs['country_name'].replace(' ', '_').lower() + '_pop.tif'), 'population')

# wsf
if menu['wsf']:
    clipdata_wsf(wsf_folder / (city_name_l + '_wsf_evolution.tif'))

# other raster files
# these are simple raster clipping from a global raster
# to add another such type of raster clipping, just add to the list below
simple_raster_clip = ['solar', 'air', 'landslide', 'impervious', 'liquefaction']

# if the data source for a certain raster file is provided in both city_inputs and global_inputs,
# city_inputs will override global_inputs.
# in both yaml files, the key for the data source must be the raster name from the list above + '_source'
for r in simple_raster_clip:
    if menu[r]:
        if (f'{r}_source' in city_inputs) and bool(city_inputs[f'{r}_source']):
            clipdata(city_inputs[f'{r}_source'], r)
        elif (f'{r}_source' in global_inputs) and bool(global_inputs[f'{r}_source']):
            clipdata(global_inputs[f'{r}_source'], r)
        else:
            print('data source for ' + r + ' does not exist in city or global inputs yaml')

"""
# 04 elevation
# waiting for FABDEM download
if tifCounter > 0:
    clipdata_elev(admin_folder, elevation_file, output_folder, '04_elevation')

"""
