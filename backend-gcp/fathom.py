def set_flood_folder(local_data_dir):
    import os

    local_flood_folder = f'{local_data_dir}/flood'
    os.makedirs(local_flood_folder, exist_ok=True)
    return local_flood_folder

def download_fathom_from_aws(download_list, aws_access_key_id, aws_secret_access_key, aws_bucket, local_flood_folder, data_bucket, data_bucket_dir):
    # download requested raster file(s) and return a list of downloaded raster file(s)
    if not download_list:
        print('download_raster function error: download_list is empty')
        exit()

    import boto3
    import utils
    import os
    
    downloaded_list = []

    # initiate s3 resource
    s3 = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    # select bucket
    bucket = s3.Bucket(name=aws_bucket)

    for f in download_list:
        os.makedirs(os.path.dirname(f'{local_flood_folder}/{f[7:]}'), exist_ok=True)
        if utils.download_blob(data_bucket, f'{data_bucket_dir}/{f[7:]}', f'{local_flood_folder}/{f[7:]}'):
            downloaded_list.append(f'{local_flood_folder}/{f[7:]}')
        else:
            try:
                for obj in bucket.objects.filter(Prefix = f):
                    bucket.download_file(obj.key, f'{local_flood_folder}/{f[7:]}')
                if utils.upload_blob(data_bucket, f'{local_flood_folder}/{f[7:]}', f'{data_bucket_dir}/{f[7:]}'):
                    downloaded_list.append(f'{local_flood_folder}/{f[7:]}')
            except Exception as e:
                print(f'{f} download exception: {e}')

    return downloaded_list

def apply_flood_threshold(out_image, out_meta, flood_threshold, multiplier):
    import numpy as np

    out_image[out_image == out_meta['nodata']] = 0
    out_image[out_image < flood_threshold] = 0
    out_image[out_image >= flood_threshold] = 1
    out_image = np.asarray(out_image)
    out_image = out_image * multiplier

    out_meta.update({'nodata': 0})

    return out_image, out_meta

def composite_flood_raster(raster_arrays, out_meta, output_raster):
    import numpy as np
    import rasterio

    out_image = np.maximum.reduce(raster_arrays).astype(np.uint8)
    out_meta.update(dtype = rasterio.uint8)
    
    with rasterio.open(output_raster, 'w', **out_meta) as dst:
        dst.write(out_image)

def process_fathom(aoi_file, city_name_l, local_data_dir, city_inputs, menu, aws_access_key_id, aws_secret_access_key, aws_bucket, data_bucket, data_bucket_dir, local_output_dir, cloud_bucket, output_dir):
    print('run process_fathom')
    
    import raster_pro
    import numpy as np
    import utils
    import os

    # set parameters
    flood_threshold = city_inputs['flood']['threshold']
    flood_years = city_inputs['flood']['year']
    flood_ssps = city_inputs['flood']['ssp']
    flood_prob_cutoff = city_inputs['flood']['prob_cutoff']

    rps = [10, 100, 1000, 20, 200, 5, 50, 500]
    flood_ssp_labels = {1: '1_2.6', 2: '2_4.5', 3: '3_7.0', 5: '5_8.5'}
    flood_type_folder_dict = {'coastal': 'COASTAL-UNDEFENDED',
                              'fluvial': 'FLUVIAL-UNDEFENDED',
                              'pluvial': 'PLUVIAL-DEFENDED'}
    if not len(flood_prob_cutoff) == 2:
        print('exactly 2 cutoffs required for flood')
        exit()
    
    local_flood_folder = set_flood_folder(local_data_dir)
    
    # find relevant tiles
    aoi_bounds = aoi_file.bounds
    buffer_aoi = aoi_file.buffer(np.nanmax([aoi_bounds.maxx - aoi_bounds.minx, aoi_bounds.maxy - aoi_bounds.miny]))
    lat_tiles = raster_pro.tile_finder(buffer_aoi, 'lat')
    lon_tiles = raster_pro.tile_finder(buffer_aoi, 'lon')
    utm_crs = utils.find_utm(aoi_file)
    
    # translate the annual probability cutoffs to bins of return periods
    rp_multipliers = {}
    for rp in rps:
        annual_prob = 1/rp*100
        if annual_prob < flood_prob_cutoff[0]:
            rp_multipliers[rp] = 1
        elif annual_prob >= flood_prob_cutoff[0] and annual_prob <= flood_prob_cutoff[1]:
            rp_multipliers[rp] = 2
        elif annual_prob > flood_prob_cutoff[1]:
            rp_multipliers[rp] = 3
                    
    for ft in ['coastal', 'fluvial', 'pluvial']:
        if menu[f'flood_{ft}']:                
            for year in flood_years:
                if year <= 2020:
                    out_image_arrays = []
                    for rp in rps:
                        download_list = []
                        for lat in lat_tiles:
                            for lon in lon_tiles:
                                download_list.append(f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft]}-DEPTH-{year}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif")
                                downloaded_list = download_fathom_from_aws(download_list, aws_access_key_id, aws_secret_access_key, aws_bucket, local_flood_folder, data_bucket, data_bucket_dir)
                        mosaic_file = f"{downloaded_list[0].split('/')[3]}.tif"
                        raster_pro.mosaic_raster(downloaded_list, local_flood_folder, mosaic_file)
                        out_image, out_meta = raster_pro.raster_mask_file(f'{local_flood_folder}/{mosaic_file}', buffer_aoi.geometry)
                        out_image, out_meta = apply_flood_threshold(out_image, out_meta, flood_threshold, rp_multipliers[rp])
                        out_image_arrays.append(out_image)
                    if out_image_arrays:
                        composite_flood_raster(out_image_arrays, out_meta, f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif')
                        raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif', utm_crs, f'{local_output_dir}/{city_name_l}_{ft}_{year}_utm.tif')
                        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif', f'{output_dir}/{city_name_l}_{ft}_{year}.tif')
                        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_utm.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_utm.tif')
                        os.remove(f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif')
                        os.remove(f'{local_output_dir}/{city_name_l}_{ft}_{year}_utm.tif')
                elif year > 2020:
                    for ssp in flood_ssps:
                        out_image_arrays = []
                        for rp in rps:
                            download_list = []
                            for lat in lat_tiles:
                                for lon in lon_tiles:
                                    download_list.append(f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft]}-DEPTH-{year}-SSP{flood_ssp_labels[ssp]}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif")
                                    downloaded_list = download_fathom_from_aws(download_list, aws_access_key_id, aws_secret_access_key, aws_bucket, local_flood_folder, data_bucket, data_bucket_dir)
                            mosaic_file = f"{downloaded_list[0].split('/')[3]}.tif"
                            raster_pro.mosaic_raster(downloaded_list, local_flood_folder, mosaic_file)
                            out_image, out_meta = raster_pro.raster_mask_file(f'{local_flood_folder}/{mosaic_file}', buffer_aoi.geometry)
                            out_image, out_meta = apply_flood_threshold(out_image, out_meta, flood_threshold, rp_multipliers[rp])
                            out_image_arrays.append(out_image)
                        if out_image_arrays:
                            composite_flood_raster(out_image_arrays, out_meta, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif', utm_crs, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif')
                            utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif')
                            os.remove(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            os.remove(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif')