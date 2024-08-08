# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['flood_coastal'] or menu['flood_fluvial'] or menu['flood_pluvial']:
    import boto3
    import os
    import math
    import yaml
    import geopandas as gpd
    from os.path import exists
    from pathlib import Path

    # SET UP ##############################################

    # load city inputs files, to be updated for each city scan
    with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
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
    aoi_bounds = aoi_file.bounds

    # Define output folder ---------
    output_folder = Path('../mnt/city-directories/02-process-output')

    os.makedirs(output_folder, exist_ok=True)
    
    # Read AWS credentials ------------
    with open("../../../other/fathom_aws_credentials.yml") as f:
        aws_cred = yaml.safe_load(f)


    # DOWNLOAD ###########################################
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
            print('tile_finder function error')
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

    bucket_name = 'wbg-geography01'
    download_path = global_inputs['fathom_path']

    # Prepare flood data (coastal, fluvial, pluvial) ---------------------
    print('download fathom')
    flood_folder= Path(download_path)
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
    rasters_download=[]
    aws_rasters_download=[]
    aws_dict= {}
    if not len(flood_prob_cutoff) == 2:
        err_msg = '2 cutoffs required for flood'
    else:
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
            # raw data folder
            flood_type_folder_dict = {
                                    'coastal': 'COASTAL_UNDEFENDED',
                                    # 'coastal': 'COASTAL_DEFENDED',
                                    'fluvial': 'FLUVIAL_UNDEFENDED',
                                    'pluvial': 'PLUVIAL_DEFENDED'}
                        
        for ft in ['coastal', 'fluvial', 'pluvial']:
            if menu[f'flood_{ft}']:                
                for year in flood_years:
                    if year <= 2020:
                        for rp in rps:
                            # identify tiles and merge as needed
                            for lat in lat_tiles:
                                for lon in lon_tiles:
                                    raster_file_name = f"{year}/1in{rp}/1in{rp}-{flood_type_folder_dict[ft].replace('_', '-')}-{year}_{lat.lower()}{lon.lower()}.tif"
                                    aws_raster_file_name = f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft].replace('_', '-')}-DEPTH-{year}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif"
                                    if not exists(flood_folder / raster_file_name):
                                        rasters_download.append(raster_file_name)
                                        aws_rasters_download.append(aws_raster_file_name)
                                        aws_dict[aws_raster_file_name]=raster_file_name
                    elif year > 2020:
                        for ssp in flood_ssps:
                            for rp in rps:
                                for lat in lat_tiles:
                                    for lon in lon_tiles:
                                        raster_file_name = f"{year}/SSP{flood_ssp_labels[ssp]}/1in{rp}/1in{rp}-{flood_type_folder_dict[ft].replace('_', '-')}-{year}-SSP{flood_ssp_labels[ssp]}_{lat.lower()}{lon.lower()}.tif"
                                        aws_raster_file_name = f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft].replace('_', '-')}-DEPTH-{year}-SSP{flood_ssp_labels[ssp]}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif"
                                        if not exists(flood_folder / raster_file_name):
                                            rasters_download.append(raster_file_name)
                                            aws_rasters_download.append(aws_raster_file_name)
                                            aws_dict[aws_raster_file_name]=raster_file_name
    
    # insert aws credentials 
    aws_access_key_id=aws_cred['aws_access_key_id']
    aws_secret_access_key=aws_cred['aws_secret_access_key']
    bucket_name='wbg-geography01'

    def download_fathom_from_bucket(bucket_name, aws_access_key_id, aws_secret_access_key, download_path, aws_dict):
        #initiate s3 resource
        s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        # select bucket
        my_bucket = s3.Bucket(bucket_name)
        bucket = s3.Bucket(name=bucket_name)
        for key, value in aws_dict.items():
            fathom_raster_dir=value.split('/')[:-1]
            fathom_raster=value.split('/')[-1]
            fathom_flood_type=fathom_raster.split('-')
            fathom_flood_type=fathom_flood_type[1:3]
            fathom_flood_type='_'.join(fathom_flood_type)
            fathom_raster_dir= '/'.join(fathom_raster_dir)
            fathom_raster_dir=f'{download_path}/{fathom_flood_type}/{fathom_raster_dir}'
            os.makedirs(fathom_raster_dir, exist_ok=True)
            if not exists(f'{fathom_raster_dir}/{fathom_raster}'):
                prefix=key
                for obj in bucket.objects.filter(Prefix=prefix):
                    # file_name = obj.key.split("/")[-2] # getting the file name of the S3 object
                    my_bucket.download_file(obj.key, f'{fathom_raster_dir}/{fathom_raster}')
    download_fathom_from_bucket(bucket_name, aws_access_key_id, aws_secret_access_key, download_path, aws_dict)