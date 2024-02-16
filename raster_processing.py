# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
# TODO: Add a log txt file
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['raster_processing']:
    import os
    import math
    import csv
    import geopandas as gpd
    import numpy as np
    import rasterio.mask
    import rasterio
    import requests
    from pathlib import Path
    from rasterio.merge import merge
    from os.path import exists
    import zipfile
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from shutil import copyfile

    # SET UP ##############################################

    # load city inputs files, to be updated for each city scan
    with open("city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs, such as data sources that generally remain the same across scans
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Read AOI shapefile --------
    print('read AOI shapefile')
    # transform the input shp to correct prj (epsg 4326)
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)
    features = aoi_file.geometry

    # Define output folder ---------
    output_folder = Path('output')

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)


    # DOWNLOAD AND PREPARE DATA ##########################################
    data_folder = Path('data')

    try:
        os.mkdir(data_folder)
    except FileExistsError:
        pass

    def tile_finder(direction, tile_size = 1):
        coord_list = []

        if direction == 'lat':
            hemi_options = ['N', 'S']
            coord_min = aoi_bounds.miny
            coord_max = aoi_bounds.maxy
            zfill_digits = 2
        elif direction == 'lon':
            hemi_options = ['E', 'W']
            coord_min = aoi_bounds.minx
            coord_max = aoi_bounds.maxx
            zfill_digits = 3
        else:
            print('Invalid direction. How did this happen?')

        for i in range(len(aoi_bounds)):
            if math.floor(coord_min[i]) >= 0:
                hemi = hemi_options[0]
                for y in range(math.floor(coord_min[i] / tile_size) * tile_size, 
                                math.ceil(coord_max[i] / tile_size) * tile_size, 
                                tile_size):
                    coord_list.append(f'{hemi}{str(y).zfill(zfill_digits)}')
            elif math.ceil(coord_max[i]) >= 0:
                for y in range(0, 
                                math.ceil(coord_max[i] / tile_size) * tile_size, 
                                tile_size):
                    coord_list.append(f'{hemi_options[0]}{str(y).zfill(zfill_digits)}')
                for y in range(math.floor(coord_min[i] / tile_size) * tile_size, 
                                0, 
                                tile_size):
                    coord_list.append(f'{hemi_options[1]}{str(-y).zfill(zfill_digits)}')
            else:
                hemi = hemi_options[1]
                for y in range(math.floor(coord_min[i] / tile_size) * tile_size, 
                                math.ceil(coord_max[i] / tile_size) * tile_size, 
                                tile_size):
                    coord_list.append(f'{hemi}{str(-y).zfill(zfill_digits)}')

        return coord_list

    # Download and prepare WorldPop data ------------
    if menu['population']:
        pop_folder = data_folder / 'pop'

        try:
            os.mkdir(pop_folder)
        except FileExistsError:
            pass

        # default population data source: WorldPop

        # use WorldPop API to query data URL
        wp_file_json = requests.get(f"https://hub.worldpop.org/rest/data/pop/cic2020_100m?iso3={city_inputs['country_iso3']}").json()
        wp_file_list = wp_file_json['data'][0]['files']

        # check if the country's population raster has already been downloaded
        # download if the file does not already exist
        if not exists(pop_folder / f"{city_inputs['country_name'].replace(' ', '_').lower()}_pop.tif"):
            if len(wp_file_list) > 1:
                # if more than one raster file is listed (uncommon), download each file and then mosaic them
                for f in wp_file_list:
                    wp_file = requests.get(f)
                    wp_file_name = f.split('/')[-1]
                    
                    open(pop_folder / wp_file_name, 'wb').write(wp_file.content)

                try:
                    raster_to_mosaic = []
                    mosaic_file = f"{city_inputs['country_name'].replace(' ', '_').lower()}_pop.tif"

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
                wp_file_name = f"{city_inputs['country_name'].replace(' ', '_').lower()}_pop.tif"
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
                    file_name = f'WSFevolution_v1_{x}_{y}'
                    if not exists(wsf_folder / f'{file_name}.tif'):
                        file = requests.get(f'https://download.geoservice.dlr.de/WSF_EVO/files/{file_name}/{file_name}.tif')
                        open(wsf_folder / f'{file_name}.tif', 'wb').write(file.content)

        # count how many raster files have been downloaded
        def tif_counter(list):
            if list.endswith('.tif'):
                return True
            return False

        if len(list(filter(tif_counter, os.listdir(wsf_folder)))) > 1:
            try:
                raster_to_mosaic = []
                mosaic_file = f'{city_name_l}_wsf_evolution.tif'

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
            os.rename(wsf_folder / (list(filter(tif_counter, os.listdir(wsf_folder)))[0]), wsf_folder / f'{city_name_l}_wsf_evolution.tif')
        else:
            print('No WSF evolution file available')

    # Download and prepare FABDEM data ---------------------
    if menu['elevation'] or menu['slope']:
        elev_folder = data_folder / 'elev'

        try:
            os.mkdir(elev_folder)
        except FileExistsError:
            pass

        aoi_bounds = aoi_file.bounds

        lat_tiles_big = tile_finder('lat', 10)
        lon_tiles_big = tile_finder('lon', 10)
        lat_tiles_small = tile_finder('lat', 1)
        lon_tiles_small = tile_finder('lon', 1)

        def tile_end_matcher(tile_starter):
            if tile_starter == 'S10':
                return 'N00'
            elif tile_starter == 'W010':
                return 'E000'
            elif tile_starter[0] == 'N' or tile_starter[0] == 'E':
                return f'{tile_starter[0]}{str(int(tile_starter[1:]) + 10).zfill(len(tile_starter) - 1)}'
            elif tile_starter[0] == 'S' or tile_starter[0] == 'W':
                return f'{tile_starter[0]}{str(int(tile_starter[1:]) - 10).zfill(len(tile_starter) - 1)}'
            else:
                print('Invalid input. How did this happen?')

        for lat in lat_tiles_big:
            for lon in lon_tiles_big:
                file_name = f'{lat}{lon}-{tile_end_matcher(lat)}{tile_end_matcher(lon)}_FABDEM_V1-2.zip'
                if not exists(elev_folder / file_name):
                    print('download elevation file')
                    print(file_name)
                    file = requests.get(f'https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/{file_name}')
                    open(elev_folder / file_name, 'wb').write(file.content)

                # unzip downloads
                for lat1 in lat_tiles_small:
                    for lon1 in lon_tiles_small:
                        file_name1 = f'{lat1}{lon1}_FABDEM_V1-2.tif'
                        if not exists(elev_folder / file_name1):
                            try:
                                with zipfile.ZipFile(elev_folder / file_name, 'r') as z:
                                    z.extract(file_name1, elev_folder)
                            except:
                                pass

        # count how many raster files have been unzipped
        def tif_counter(list):
            if list.endswith('.tif'):
                return True
            return False

        if len(list(filter(tif_counter, os.listdir(elev_folder)))) > 1:
            try:
                raster_to_mosaic = []
                mosaic_file = f'{city_name_l}_elevation.tif'

                if not exists(elev_folder / mosaic_file):
                    mosaic_list = os.listdir(elev_folder)
                    for p in mosaic_list:
                        if p.endswith('.tif'):
                            raster = rasterio.open(elev_folder / p)
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

                    with rasterio.open(elev_folder / mosaic_file, 'w', **output_meta) as m:
                        m.write(mosaic)
            except MemoryError:
                print('MemoryError when merging elevation raster files.') 
                print('Try GIS instead for merging.')
        elif len(list(filter(tif_counter, os.listdir(elev_folder)))) == 1:
            os.rename(elev_folder / (list(filter(tif_counter, os.listdir(elev_folder)))[0]), elev_folder / f'{city_name_l}_elevation.tif')
        else:
            print('No elevation file available')
    
    # Download and prepare demographics data ------------------
    if menu['demographics']:
        demo_folder = data_folder / 'demographics'

        try:
            os.mkdir(demo_folder)
        except FileExistsError:
            pass
        
        demo_file_json = requests.get(f"https://www.worldpop.org/rest/data/age_structures/ascic_2020?iso3={city_inputs['country_iso3']}").json()
        demo_file_list = demo_file_json['data'][0]['files']

        for f in demo_file_list:
            demo_file_name = f.split('/')[-1]

            if not exists(demo_folder / demo_file_name):
                demo_file = requests.get(f)
                open(demo_folder / demo_file_name, 'wb').write(demo_file.content)
    
    # Prepare flood data (coastal, fluvial, pluvial) ---------------------
    if menu['flood_coastal'] or menu['flood_fluvial'] or menu['flood_pluvial']:
        # merged data folder (before clipping)
        flood_folder = data_folder / 'flood'

        try:
            os.mkdir(flood_folder)
        except FileExistsError:
            pass

        # 8 return periods
        rps = [10, 100, 1000, 20, 200, 5, 50, 500]

        # find relevant tiles
        lat_tiles = tile_finder('lat')
        lon_tiles = tile_finder('lon')

        flood_threshold = global_inputs['flood']['threshold']
        flood_years = global_inputs['flood']['year']
        flood_ssps = global_inputs['flood']['ssp']
        flood_ssp_labels = {1: '1_2.6', 2: '2_4.5', 3: '3_7.0', 5: '5_8.5'}
        flood_prob_cutoff = global_inputs['flood']['prob_cutoff']
        if not len(flood_prob_cutoff) == 2:
            print('2 cutoffs required')
            exit()  # TODO: think about breaking the for loop and creating an "unsuccessful" list to print in the end
        
        # translate the annual probability cutoffs to bins of return periods
        flood_rp_bins = {f'lt{flood_prob_cutoff[0]}': [], 
                         f'{flood_prob_cutoff[0]}-{flood_prob_cutoff[1]}': [], 
                         f'gt{flood_prob_cutoff[1]}': []}
        for rp in rps:
            annual_prob = 1/rp*100
            if annual_prob < flood_prob_cutoff[0]:
                flood_rp_bins[f'lt{flood_prob_cutoff[0]}'].append(rp)
            elif annual_prob >= flood_prob_cutoff[0] and annual_prob <= flood_prob_cutoff[1]:
                flood_rp_bins[f'{flood_prob_cutoff[0]}-{flood_prob_cutoff[1]}'].append(rp)
            elif annual_prob > flood_prob_cutoff[1]:
                flood_rp_bins[f'gt{flood_prob_cutoff[1]}'].append(rp)

        def flood_processing(flood_type):
            # raw data folder
            flood_type_folder_dict = {'coastal': 'COASTAL_UNDEFENDED',
                                      'fluvial': 'FLUVIAL_UNDEFENDED',
                                      'pluvial': 'PLUVIAL_DEFENDED'}
            raw_flood_folder = Path(f'D:/World Bank/CRP/data/Fathom 3.0/Sri Lanka/{flood_type_folder_dict[flood_type]}')
            
            # prepare flood raster files (everything before clipping)
            for year in flood_years:
                if year <= 2020:
                    for rp in rps:
                        # identify tiles and merge as needed
                        raster_to_mosaic = []
                        mosaic_file = f'{city_name_l}_{flood_type}_{year}_1in{rp}.tif'

                        if not exists(flood_folder / mosaic_file):
                            for lat in lat_tiles:
                                for lon in lon_tiles:
                                    raster_file_name = f'{year}/1in{rp}/1in{rp}-{flood_type_folder_dict[flood_type].replace('_', '-')}-{year}_{lat.lower()}{lon.lower()}.tif'
                                    if exists(raw_flood_folder / raster_file_name):
                                        raster_to_mosaic.append(raw_flood_folder / raster_file_name)
                            if len(raster_to_mosaic) == 0:
                                print(f'no raster to merge for {year} 1-in-{rp}')
                            elif len(raster_to_mosaic) == 1:
                                copyfile(raster_to_mosaic[0], flood_folder / mosaic_file)
                            else:
                                try:
                                    mosaic, output = merge(raster_to_mosaic)
                                    output_meta = raster.meta.copy()
                                    output_meta.update(
                                        {"driver": "GTiff",
                                        "height": mosaic.shape[1],
                                        "width": mosaic.shape[2],
                                        "transform": output,
                                        }
                                    )

                                    with rasterio.open(flood_folder / mosaic_file, 'w', **output_meta) as m:
                                        m.write(mosaic)
                                except MemoryError:
                                    print(f'MemoryError when merging flood_{flood_type} raster files.') 
                                    print(f'{year} 1-in-{rp}')
                                    print('Try GIS instead for merging.')
                                    exit()
                        
                        # apply threshold
                        if exists(flood_folder / mosaic_file):
                            with rasterio.open(flood_folder / mosaic_file) as src:
                                out_image = src.read(1)
                                out_image[out_image == src.meta['nodata']] = 0
                                out_image[out_image < flood_threshold] = 0
                                out_image[out_image >= flood_threshold] = 1

                                out_meta = src.meta.copy()
                                out_meta.update({'nodata': 0})

                            with rasterio.open(flood_folder / (mosaic_file[:-4] + '_con.tif'), "w", **out_meta) as dest:
                                dest.write(out_image)

                    for bin in flood_rp_bins:
                        raster_to_merge = [f'{city_name_l}_{flood_type}_{year}_1in{rp}_con.tif' for rp in flood_rp_bins[bin] if exists(flood_folder / (f'{city_name_l}_{flood_type}_{year}_1in{rp}_con.tif'))]
                        raster_arrays = []

                        for r in raster_to_merge:
                            with rasterio.open(flood_folder / r) as src:
                                raster_arrays.append(src.read(1))
                                out_meta = src.meta.copy()
                            
                        out_image = np.logical_or.reduce(raster_arrays).astype(np.uint8)
                        out_meta.update(dtype = rasterio.uint8)
                        
                        with rasterio.open(output_folder / f'{city_name_l}_{flood_type}_{year}_{bin}.tif', 'w', **out_meta) as dst:
                            dst.write(out_image, 1)
                elif year > 2020:
                    for ssp in flood_ssps:
                        for rp in rps:
                            # identify tiles and merge as needed
                            raster_to_mosaic = []
                            mosaic_file = f'{city_name_l}_{flood_type}_{year}_ssp{ssp}_1in{rp}.tif'

                            if not exists(flood_folder / mosaic_file):
                                for lat in lat_tiles:
                                    for lon in lon_tiles:
                                        raster_file_name = f'{year}/SSP{flood_ssp_labels[ssp]}/1in{rp}/1in{rp}-{flood_type_folder_dict[flood_type].replace('_', '-')}-{year}-SSP{flood_ssp_labels[ssp]}_{lat.lower()}{lon.lower()}.tif'
                                        if exists(raw_flood_folder / raster_file_name):
                                            raster_to_mosaic.append(raw_flood_folder / raster_file_name)
                                if len(raster_to_mosaic) == 0:
                                    print(f'no raster to merge for {year} ssp{ssp} 1-in-{rp}')
                                elif len(raster_to_mosaic) == 1:
                                    copyfile(raster_to_mosaic[0], flood_folder / mosaic_file)
                                else:
                                    try:
                                        mosaic, output = merge(raster_to_mosaic)
                                        output_meta = raster.meta.copy()
                                        output_meta.update(
                                            {"driver": "GTiff",
                                            "height": mosaic.shape[1],
                                            "width": mosaic.shape[2],
                                            "transform": output,
                                            }
                                        )

                                        with rasterio.open(flood_folder / mosaic_file, 'w', **output_meta) as m:
                                            m.write(mosaic)
                                    except MemoryError:
                                        print(f'MemoryError when merging flood_{flood_type} raster files.') 
                                        print(f'{year} ssp{ssp} 1-in-{rp}')
                                        print('Try GIS instead for merging.')
                                        exit()
                            
                            # apply threshold
                            if exists(flood_folder / mosaic_file):
                                with rasterio.open(flood_folder / mosaic_file) as src:
                                    out_image = src.read(1)
                                    out_image[out_image == src.meta['nodata']] = 0
                                    out_image[out_image < flood_threshold] = 0
                                    out_image[out_image >= flood_threshold] = 1

                                    out_meta = src.meta.copy()
                                    out_meta.update({'nodata': 0})

                                with rasterio.open(flood_folder / (mosaic_file[:-4] + '_con.tif'), "w", **out_meta) as dest:
                                    dest.write(out_image)

                        for bin in flood_rp_bins:
                            raster_to_merge = [f'{city_name_l}_{flood_type}_{year}_ssp{ssp}_1in{rp}_con.tif' for rp in flood_rp_bins[bin] if exists(flood_folder / (f'{city_name_l}_{flood_type}_{year}_ssp{ssp}_1in{rp}_con.tif'))]
                            raster_arrays = []

                            for r in raster_to_merge:
                                with rasterio.open(flood_folder / r) as src:
                                    raster_arrays.append(src.read(1))
                                    out_meta = src.meta.copy()
                                
                            out_image = np.logical_or.reduce(raster_arrays).astype(np.uint8)
                            out_meta.update(dtype = rasterio.uint8)
                            
                            with rasterio.open(output_folder / f'{city_name_l}_{flood_type}_{year}_ssp{ssp}_{bin}.tif', 'w', **out_meta) as dst:
                                dst.write(out_image, 1)

        for ft in ['coastal', 'fluvial', 'pluvial']:
            if menu[f'flood_{ft}']:
                flood_processing(ft)


    # DEFINE FUNCTIONS #################################

    # Raster clip functions ----------------
    def clipdata(input_raster, data_type):
        with rasterio.open(input_raster) as src:
            # shapely presumes all operations on two or more features exist in the same Cartesian plane.
            out_image, out_transform = rasterio.mask.mask(
                src, features, all_touched = True, crop = True)
            out_meta = src.meta.copy()

        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        with rasterio.open(output_folder / f'{city_name_l}_{data_type}.tif', "w", **out_meta) as dest:
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
                src, features, all_touched = True, crop = True)
            out_meta = src.meta.copy()

            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})

            output_4326_raster_clipped = output_folder / f'{city_name_l}_wsf_4326.tif'

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

                output_utm_raster_clipped = output_folder / f'{city_name_l}_wsf_utm.tif'
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
                with open(output_folder / f"{city_name_l}_wsf_stats.csv", 'w') as f:
                    f.write("year,cumulative sq km\n")
                    for key in year_dict.keys():
                        f.write("%s,%s\n" % (key, year_dict[key]))

            # Reclassify
            out_image[out_image < 1985] = 0
            out_image[(out_image <= 2015) & (out_image >= 2006)] = 4
            out_image[(out_image < 2006) & (out_image >= 1996)] = 3
            out_image[(out_image < 1996) & (out_image >= 1986)] = 2
            out_image[out_image == 1985] = 1

            output_4326_raster_clipped_reclass = output_folder / f'{city_name_l}_wsf_4326_reclass.tif'

            # save for stats
            with rasterio.open(output_4326_raster_clipped_reclass, "w", **out_meta) as dest:
                dest.write(out_image)

    def clipdata_demo(input_raster):
        with rasterio.open(input_raster) as src:
            # shapely presumes all operations on two or more features exist in the same Cartesian plane.
            out_image, out_transform = rasterio.mask.mask(
                src, features, all_touched = True, crop = True)
            out_meta = src.meta.copy()

        out_meta.update({"driver": "GTiff",
                         "height": out_image.shape[1],
                         "width": out_image.shape[2],
                         "transform": out_transform})

        return out_image, out_meta


    # RASTER PROCESSING ################################
    print('starting processing')

    # population
    if menu['population']:
        clipdata(pop_folder / f"{city_inputs['country_name'].replace(' ', '_').lower()}_pop.tif", 'population')

    # wsf
    if menu['wsf']:
        clipdata_wsf(wsf_folder / f'{city_name_l}_wsf_evolution.tif')
    
    # elevation
    if menu['elevation'] or menu['slope']:
        clipdata(elev_folder / f'{city_name_l}_elevation.tif', 'elevation')

        # Calculate elevation stats
        with rasterio.open(elev_folder / f'{city_name_l}_elevation.tif') as src:
            # Read raster data
            raster_data = src.read(1)
            
            # Get min and max values of the raster
            min_val = np.nanmin(raster_data)
            max_val = np.nanmax(raster_data)
            
            # Calculate equal interval bin edges
            num_bins = 5
            bin_edges = np.linspace(min_val, max_val, num_bins + 1)
            
            # Round bin edges to the nearest 10
            bin_edges = np.round(bin_edges, -1)
            
            # Calculate histogram
            hist, _ = np.histogram(raster_data, bins=bin_edges)
            
            # Write bins and hist to a CSV file
            with open(elev_folder / f'{city_name_l}_elevation.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Bin', 'Count'])
                for i, count in enumerate(hist):
                    bin_range = f"{int(bin_edges[i])}-{int(bin_edges[i+1])}"
                    writer.writerow([bin_range, count])

    # slope
    if menu['slope']:
        import richdem as rd

        # Reproject elevation raster to a projected coordinate system
        with rasterio.open(output_folder / f'{city_name_l}_elevation.tif') as src:
            dst_crs = 'EPSG:3857'  # Web Mercator projection
            transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
            out_meta = src.meta.copy()
            out_meta.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(output_folder / f'{city_name_l}_elevation_3857.tif', 'w', **out_meta) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

        # Calculate slope
        elev = rd.LoadGDAL(str(output_folder / f'{city_name_l}_elevation_3857.tif'))
        slope = rd.TerrainAttribute(elev, attrib = 'slope_degrees')
        rd.SaveGDAL(str(output_folder / f'{city_name_l}_slope_3857.tif'), slope)

        # Reproject slope raster to WGS84
        with rasterio.open(output_folder / f'{city_name_l}_slope_3857.tif') as src:
            dst_crs = 'EPSG:4326'
            transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
            out_meta = src.meta.copy()
            out_meta.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(output_folder / f'{city_name_l}_slope.tif', 'w', **out_meta) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)

        # Calculate slope stats
        with rasterio.open(output_folder / f'{city_name_l}_slope.tif') as src:
            # Read raster data
            raster_data = src.read(1)
            
            # Define the bins
            bins = [0, 2, 5, 10, 20, 90]  # Define your desired bins
            
            # Calculate histogram
            hist, _ = np.histogram(raster_data, bins=bins)
            
            # Write bins and hist to a CSV file
            with open(output_folder / f'{city_name_l}_slope.csv', 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Bin', 'Count'])
                for i, count in enumerate(hist):
                    bin_range = f"{bins[i]}-{bins[i+1]}"
                    writer.writerow([bin_range, count])

        # Remove intermediate outputs
        os.remove(output_folder / f'{city_name_l}_elevation_3857.tif')
        os.remove(output_folder / f'{city_name_l}_slope_3857.tif')

        if not menu['elevation']:
            os.remove(output_folder / f'{city_name_l}_elevation.tif')

    # demographics
    if menu['demographics']:
        sexes = ['f', 'm']

        age_dict = {'children_under_5': [0, 1],
                    'youth': [15, 20],
                    'elderly_60_plus': range(60, 85, 5),
                    'reproductive_age': range(15, 50, 5),
                    'all_age_groups': [1] + list(range(0, 85, 5))}
        
        # aggregate total population and calculate sex ratio
        raster_to_add = []
        sex_dict = {s: [] for s in sexes}

        with open(output_folder / f'{city_name_l}_demographics.csv', 'w') as f:
            f.write('age_group,sex,population\n')

            for i in age_dict['all_age_groups']:
                for s in sexes:
                    raster_array, raster_meta = clipdata_demo(demo_folder / f'{city_inputs["country_iso3"].lower()}_{s}_{i}_2020_constrained.tif')
                    raster_array[raster_array == raster_meta['nodata']] = 0

                    if i == 0:
                        age_group_label = '0-1'
                    elif i == 1:
                        age_group_label = '1-4'
                    elif i == 80:
                        age_group_label = '80+'
                    else:
                        age_group_label = f'{i}-{i+4}'

                    f.write('%s,%s,%s\n' % (age_group_label, s, sum(sum(sum(raster_array)))))
                    
                    raster_to_add.append(raster_array)
                    sex_dict[s].append(raster_array)
        demo_total = sum(raster_to_add)
        raster_meta.update({'nodata': 0})
        with rasterio.open(output_folder / f"{city_name_l}_demo_total.tif", 'w', **raster_meta) as m:
            m.write(demo_total)
        with rasterio.open(output_folder / f"{city_name_l}_sex_ratio.tif", 'w', **raster_meta) as m:
            m.write(np.divide(sum(sex_dict['f']), sum(sex_dict['m'])))

        # aggregate age groups
        for group in age_dict:
            if group != 'all_age_groups':
                raster_to_add = []
                
                for i in age_dict[group]:
                    for s in sexes:
                        if not ((i == 'reproductive_age') and (s == 'm')):
                            raster_array, raster_meta = clipdata_demo(demo_folder / f'{city_inputs["country_iso3"].lower()}_{s}_{i}_2020_constrained.tif')
                            raster_array[raster_array == raster_meta['nodata']] = 0
                            raster_to_add.append(raster_array)
                
                if i == 'reproductive_age':
                    output_name = f"{city_name_l}_women_{group}.tif"
                else:
                    output_name = f"{city_name_l}_{group}.tif"
                raster_meta.update({'nodata': 0})
                with rasterio.open(output_folder / output_name, 'w', **raster_meta) as m:
                    m.write(sum(raster_to_add) / demo_total)

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
                print(f'data source for {r} does not exist in city or global inputs yaml')
