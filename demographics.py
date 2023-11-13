import sys, os, inspect, logging, importlib
import glob
import requests
import pandas as pd
import json
import pickle
import geopandas as gpd
import matplotlib 
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
import requests

import rasterio
from rasterio.plot import show
import rasterio.mask
from rasterio import features
import numpy as np
import csv
import fiona
from pathlib import Path

def download_rwi(ISO_code):
    #Making use of the WorldPop API: https://www.worldpop.org/sdi/introapi/

    age_sex_url = f"https://www.worldpop.org/rest/data/age_structures/ascic_2020?iso3={ISO_code}"  # Replace with the actual endpoint
    #params = {"country": "Albania"}  # Replace with the correct parameter name and country
    response = requests.get(age_sex_url)
    data = response.json()

    # Extract the files list from the JSON response
    files_list = data['data'][0]['files']

    # Create a directory to store the downloaded files
    #os.makedirs('worldpop_data', exist_ok=True)


    search_criteria = f"demographics/worldpop_data/*constrained.tif"

    demographics_file = glob.glob(search_criteria)

    if not demographics_file:  # Checks if the list is empty
        print("Warning: No demographics files exist within the demographics directory, downloading files")
        # Loop through each file URL and download
        for file_url in files_list:
            response = requests.get(file_url, stream=True)
            filename = os.path.join('demographics/worldpop_data', file_url.split('/')[-1])
            
            with open(filename, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Downloaded {filename}")
    else:
        print("Directory is not empty. Skipping downloading demographics files...")

def get_iso_code(file):
    extent = gpd.read_file(f'admin/{file}').set_crs(epsg=4326)
    centroid = extent.geometry.centroid
    world = gpd.read_file("WB_countries_Admin0_10m/WB_countries_Admin0_10m.shp")
    country = world[world.geometry.contains(centroid[0])]
    iso3_code = country['ISO_A3'].values[0]
    return iso3_code

def run_demographics(file, city, country_acronym, output_folder):

    print('inside run_demographics')

    # AOI
    aoi = gpd.read_file(f'admin/{file}')

    country_acronym = country_acronym.lower()

    # define parameters
    sexes = ['f', 'm']
    age_groups = {0: '<1',
              1: '1-4'}
    for a in range(5, 80, 5):
        age_groups[a] = str(a) + '-' + str(a + 4)
    age_groups[80] = '80+'
    children_under_5 = [0,1]
    elderly_60_plus = [60,65,70,75,80]
    youth = [15,20]
    all_age_groups = list(age_groups.keys())
    woman_reproductive_age = [15,20,25,30,35,40,45]

    # all_age_groups
    with fiona.open(f'admin/{file}', "r") as shapefile:
        features = [feature["geometry"] for feature in shapefile]
        
        count = 0
        # all
        for s in sexes:
            for a in all_age_groups:

                print(a)

                count += 1

                if count == 1:
                    input_raster = country_acronym + '_' + s +'_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        pop_array, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        out_meta = src.meta.copy()
                else:
                    input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array_masked, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        pop_array = pop_array + result_array_masked

                # make all values less than 0 be 0
                pop_array[pop_array<0] = 0
                
                out_meta.update({"driver": "GTiff",
                                "height": pop_array.shape[1],
                                "width": pop_array.shape[2],
                                "transform": out_transform})
        
        # save the output
        output_file = city + '_all_pop' + '_2020.tif'
        print('print output on line 121')
        print(output_folder)
        print(output_file)
        output_location = output_folder + "/" + output_file

        with rasterio.open(output_location, "w", **out_meta) as dest:
            dest.write(pop_array)

        # children_under_5
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            count = 0
            for s in sexes:
                for a in children_under_5:
                    
                    print(a)
                    
                    count += 1
                    
                    if count == 1:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            out_meta = src.meta.copy()
                    else:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array_masked, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            result_array = result_array + result_array_masked
                            
            # make all values less than 0 be 0
            result_array[result_array<0] = 0
            
            # get the indices where the result array has a value greater than 0
            filtered_indices = np.where(result_array > 0)
            filtered_pop_array = pop_array[filtered_indices]
            
            result_array[result_array>0] = result_array[result_array>0] / filtered_pop_array
            
            # make all values less than 0 be 0
            result_array[result_array<0] = 0

            out_meta.update({"driver": "GTiff",
                            "height": result_array.shape[1],
                            "width": result_array.shape[2],
                            "transform": out_transform})

            # save the output
            output_file = city + '_children_under_5' + '_2020.tif'
            output_location = output_folder + "/" + output_file
            with rasterio.open(output_location, "w", **out_meta) as dest:
                dest.write(result_array)

        # elderly_60_plus
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            count = 0
            for s in sexes:
                for a in elderly_60_plus:
                    
                    print(a)
                    
                    count += 1
                    
                    if count == 1:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            out_meta = src.meta.copy()
                    else:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array_masked, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            result_array = result_array + result_array_masked

            # make all values less than 0 be 0
            result_array[result_array<0] = 0
            
            # get the indices where the result array has a value greater than 0
            filtered_indices = np.where(result_array > 0)
            filtered_pop_array = pop_array[filtered_indices]
            
            result_array[result_array>0] = result_array[result_array>0] / filtered_pop_array
            
            # make all values less than 0 be 0
            result_array[result_array<0] = 0

            out_meta.update({"driver": "GTiff",
                            "height": result_array.shape[1],
                            "width": result_array.shape[2],
                            "transform": out_transform})

            # save the output
            output_file = city + '_elderly_60_plus' + '_2020.tif'
            output_location = output_folder + "/" + output_file
            with rasterio.open(output_location, "w", **out_meta) as dest:
                dest.write(result_array)

        # youth
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            count = 0
            for s in sexes:
                for a in youth:
                    
                    print(a)
                    
                    count += 1
                    
                    if count == 1:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            out_meta = src.meta.copy()
                    else:
                        input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                        with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                            result_array_masked, out_transform = rasterio.mask.mask(
                                src, features, crop=True)
                            result_array = result_array + result_array_masked

            # make all values less than 0 be 0
            result_array[result_array<0] = 0
            
            # get the indices where the result array has a value greater than 0
            filtered_indices = np.where(result_array > 0)
            filtered_pop_array = pop_array[filtered_indices]
            
            result_array[result_array>0] = result_array[result_array>0] / filtered_pop_array
            
            # make all values less than 0 be 0
            result_array[result_array<0] = 0

            out_meta.update({"driver": "GTiff",
                            "height": result_array.shape[1],
                            "width": result_array.shape[2],
                            "transform": out_transform})

            # save the output
            output_file = city + '_youth' + '_2020.tif'
            output_location = output_folder + "/" + output_file
            with rasterio.open(output_location, "w", **out_meta) as dest:
                dest.write(result_array)

        # woman_reproductive_age
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            count = 0
            for a in woman_reproductive_age:

                print(a)

                count += 1

                if count == 1:
                    input_raster = country_acronym + '_f_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        out_meta = src.meta.copy()
                else:
                    input_raster = country_acronym + '_f_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array_masked, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        result_array = result_array + result_array_masked

            # make all values less than 0 be 0
            result_array[result_array<0] = 0
            
            # get the indices where the result array has a value greater than 0
            filtered_indices = np.where(result_array > 0)
            filtered_pop_array = pop_array[filtered_indices]
            
            result_array[result_array>0] = result_array[result_array>0] / filtered_pop_array
            
            # make all values less than 0 be 0
            result_array[result_array<0] = 0

            out_meta.update({"driver": "GTiff",
                            "height": result_array.shape[1],
                            "width": result_array.shape[2],
                            "transform": out_transform})

            # save the output
            output_file = city + '_woman_reproductive_age' + '_2020.tif'
            output_location = output_folder + "/" + output_file
            with rasterio.open(output_location, "w", **out_meta) as dest:
                dest.write(result_array)

        # sex-ratio # all_age_groups
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            count = 0
            # females
            for a in all_age_groups:

                print(a)

                count += 1

                if count == 1:
                    input_raster = country_acronym + '_f_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        out_meta = src.meta.copy()
                else:
                    input_raster = country_acronym + '_f_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array_masked, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        result_array = result_array + result_array_masked

                out_meta.update({"driver": "GTiff",
                                "height": result_array.shape[1],
                                "width": result_array.shape[2],
                                "transform": out_transform})
                
            # males
            count = 0
            for a in all_age_groups:

                print(a)

                count += 1

                if count == 1:
                    input_raster = country_acronym + '_m_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        male_result_array, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        out_meta = src.meta.copy()
                else:
                    input_raster = country_acronym + '_m_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        result_array_masked, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        male_result_array = male_result_array + result_array_masked

            # make all values less than 0 be 0
            male_result_array[male_result_array<0] = 0
            #result_array is the female raster
            result_array[result_array<0] = 0
            
            # get the indices where the result array has a value greater than 0
            filtered_indices = np.where(male_result_array > 0)
            filtered_result_array = result_array[filtered_indices]
            
            # the male_result_array becomes the final male/female ratio raster
            male_result_array[male_result_array>0] = male_result_array[male_result_array>0] / filtered_result_array
                        
        #     final_result_array = male_result_array / result_array
            
            out_meta.update({"driver": "GTiff",
                                "height": result_array.shape[1],
                                "width": result_array.shape[2],
                                "transform": out_transform})
            
            # save the output
            output_file = city + '_sex_ratio' + '_2020.tif'
            output_location = output_folder + "/" + output_file
            with rasterio.open(output_location, "w", **out_meta) as dest:
                dest.write(male_result_array)

        # Step 1 to create the age distribution CSVs. Clips the country data files by the city AOI.
        with fiona.open(f'admin/{file}', "r") as shapefile:
            features = [feature["geometry"] for feature in shapefile]
            
            for s in sexes:
                for a in age_groups:
                    input_raster = country_acronym + '_' + s + '_' + str(a) + '_2020_constrained.tif'
                    with rasterio.open(Path('demographics/worldpop_data') / input_raster) as src:
                        out_image, out_transform = rasterio.mask.mask(
                            src, features, crop=True)
                        out_meta = src.meta.copy()

                    out_meta.update({"driver": "GTiff",
                                    "height": out_image.shape[1],
                                    "width": out_image.shape[2],
                                    "transform": out_transform})

                    # save the output
                    output_file = city + '_' + s + '_' + str(a) + '_2020.tif'
                    output_location = output_folder + "/" + output_file
                    with rasterio.open(output_location, "w", **out_meta) as dest:
                        dest.write(out_image)

        # This reads in back the previous outputs to create the age distribution CSVs
        #with open((Path('output') / (city + '_age_distribution.csv')), 'w') as f:
        print('attempting to write final age distribution CSVs')
        with open((Path(output_folder) / (city + '_age_distribution.csv')), 'w') as f:
            f.write('age_group,female,male\n')
            for a in age_groups:
                f_array = rasterio.open(Path(output_folder) / (city + '_f_' + str(a) + '_2020.tif')).read(1)
                female = np.sum(f_array[f_array > 0])
                m_array = rasterio.open(Path(output_folder) / (city + '_m_' + str(a) + '_2020.tif')).read(1)
                male = np.sum(m_array[m_array > 0])
                f.write('%s,%s,%s\n' % (age_groups[a], female, male))

    

def process_demographics(admin_folder, output_folder):

    try:
        os.mkdir(output_folder + '/demographics')
    except FileExistsError:
        pass

    output_folder = output_folder + 'demographics'

    print('before loop output_folder')
    print(output_folder)

    print('before loop')
    print(admin_folder)

    for file in os.listdir(admin_folder):
        if file.endswith(".shp"):

            print(file)

            AOI_file_name = os.path.splitext(file)[0]

            ISO_code = get_iso_code(file)

            print('printing ISO_code')
            print(ISO_code)

            download_rwi(ISO_code)

            run_demographics(file, AOI_file_name, ISO_code, output_folder)
