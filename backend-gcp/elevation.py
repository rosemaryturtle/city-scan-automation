def elevation(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir):
    import raster_pro
    import zipfile
    import os
    import rasterio
    import utils

    # download
    local_elev_folder = f'{local_data_dir}/elev'
    os.makedirs(local_elev_folder, exist_ok=True)

    lat_tiles_big = raster_pro.tile_finder(aoi_file, 'lat', 10)
    lon_tiles_big = raster_pro.tile_finder(aoi_file, 'lon', 10)
    lat_tiles_small = raster_pro.tile_finder(aoi_file, 'lat', 1)
    lon_tiles_small = raster_pro.tile_finder(aoi_file, 'lon', 1)

    elev_download_dict = {}
    for lat in lat_tiles_big:
        for lon in lon_tiles_big:
            file_name = f'{lat}{lon}-{raster_pro.fabdem_tile_end_matcher(lat)}{raster_pro.fabdem_tile_end_matcher(lon)}_FABDEM_V1-2.zip'

            # unzip downloads
            for lat1 in lat_tiles_small:
                for lon1 in lon_tiles_small:
                    file_name1 = f'{lat1}{lon1}_FABDEM_V1-2.tif'
                    elev_download_dict[file_name1] = file_name

    elev_download_list = [f'https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/{fn}' for fn in list(elev_download_dict.values())]
    downloaded_list = raster_pro.download_raster(list(set(elev_download_list)), local_elev_folder, data_bucket, data_bucket_dir='FABDEM')
    mosaic_list = []

    # unzip and mosaic as needed
    for fn in elev_download_dict:
        if f'{local_elev_folder}/{elev_download_dict[fn]}' in downloaded_list:
            try:
                with zipfile.ZipFile(f'{local_elev_folder}/{elev_download_dict[fn]}', 'r') as z:
                    z.extract(fn, local_elev_folder)
                    mosaic_list.append(fn)
            except:
                pass
    
    if mosaic_list:
        raster_pro.mosaic_raster(mosaic_list, local_elev_folder, f'{city_name_l}_elevation.tif')
        out_image, out_meta = raster_pro.raster_mask_file(f'{local_elev_folder}/{city_name_l}_elevation.tif', aoi_file.geometry)
        with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation.tif', "w", **out_meta) as dest:
            dest.write(out_image)
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.tif', f'{output_dir}/{city_name_l}_elevation.tif')
        with open(f"{local_output_dir}/elevation_source.txt", 'w') as f:
            f.write('FABDEM')
    else:
        import gee_fun
        gee_fun.gee_elevation(city_name_l, aoi_file, cloud_bucket, output_dir)
        utils.download_blob(cloud_bucket, f"{output_dir}/{city_name_l}_elevation.tif", f'{local_output_dir}/{city_name_l}_elevation.tif')
        with open(f"{local_output_dir}/elevation_source.txt", 'w') as f:
            f.write('NASA SRTM Digital Elevation 30m')
    
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/elevation_source.txt", f"{output_dir}/elevation_source.txt")
    
    contour_levels = raster_pro.contour(f'{local_output_dir}/{city_name_l}_elevation.tif', local_output_dir, city_name_l)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_contour.gpkg', f'{output_dir}/{city_name_l}_contour.gpkg')

    contour_levels = list(contour_levels)
    contour_bins = [contour_levels[int(((len(contour_levels) - 6) / 5 + 1) * i)] for i in range(6)]
    raster_pro.get_raster_histogram(f'{local_output_dir}/{city_name_l}_elevation.tif', contour_bins, f'{local_output_dir}/{city_name_l}_elevation.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.csv', f'{output_dir}/{city_name_l}_elevation.csv')