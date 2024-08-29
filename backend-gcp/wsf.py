def wsf(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir):
    import raster_pro
    import math
    import csv
    import utils
    import os
    import rasterio

    local_wsf_folder = f'{local_data_dir}/wsf'
    os.makedirs(local_wsf_folder, exist_ok=True)
    aoi_bounds = aoi_file.bounds

    wsf_file_list = []
    for i in range(len(aoi_bounds)):
        for x in range(math.floor(aoi_bounds.minx[i] - aoi_bounds.minx[i] % 2), math.ceil(aoi_bounds.maxx[i]), 2):
            for y in range(math.floor(aoi_bounds.miny[i] - aoi_bounds.miny[i] % 2), math.ceil(aoi_bounds.maxy[i]), 2):
                wsf_file_list.append(f'WSFevolution_v1_{x}_{y}')

    wsf_download_list = [f'https://download.geoservice.dlr.de/WSF_EVO/files/{f}/{f}.tif' for f in wsf_file_list]

    downloaded_list = raster_pro.download_raster(wsf_download_list, local_wsf_folder, data_bucket, data_bucket_dir='WSFevolution')
    raster_pro.mosaic_raster(downloaded_list, local_wsf_folder, f'{city_name_l}_wsf_evolution.tif')
    out_image, out_meta = raster_pro.raster_mask_file(f'{local_wsf_folder}/{city_name_l}_wsf_evolution.tif', aoi_file.geometry)
    with rasterio.open(f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', "w", **out_meta) as dest:
        dest.write(out_image)

    raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', utils.find_utm(aoi_file), f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif')
    area_dict = raster_pro.calculate_raster_area(f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', range(1985, 2016))
    # Calculate the cumulative built-up area
    cumulative_area = 0
    cumulative_dict = {}
    for year, area in sorted(area_dict.items()):
        area = area/1e6
        cumulative_area += area
        cumulative_dict[year] = cumulative_area

    # Write the cumulative data to a CSV file
    with open(f'{local_output_dir}/{city_name_l}_wsf_stats.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["year", "cumulative sq km"])
        for year, cumulative_area in cumulative_dict.items():
            writer.writerow([year, cumulative_area])

    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', f'{output_dir}/{city_name_l}_wsf_evolution.tif')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', f'{output_dir}/{city_name_l}_wsf_evolution_utm.tif')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_stats.csv', f'{output_dir}/{city_name_l}_wsf_stats.csv')