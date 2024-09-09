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
                    mosaic_list.append(f'{local_elev_folder}/{fn}')
            except:
                pass
    
    if mosaic_list:
        raster_pro.mosaic_raster(mosaic_list, local_elev_folder, f'{city_name_l}_elevation.tif')
        out_image, out_meta = raster_pro.raster_mask_file(f'{local_elev_folder}/{city_name_l}_elevation.tif', aoi_file.geometry)
        with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation.tif', "w", **out_meta) as dest:
            dest.write(out_image)
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.tif', f'{output_dir}/{city_name_l}_elevation.tif')
        with open(f"{local_output_dir}/{city_name_l}_elevation_source.txt", 'w') as f:
            f.write('FABDEM')
    else:
        import gee_fun
        from datetime import datetime as dt
        import time

        gee_fun.gee_elevation(city_name_l, aoi_file, cloud_bucket, output_dir)
        time0 = dt.now()
        while (dt.now()-time0).total_seconds() <= 60*60:
            if utils.download_blob(cloud_bucket, f"{output_dir}/{city_name_l}_elevation.tif", f'{local_output_dir}/{city_name_l}_elevation.tif'):
                with open(f"{local_output_dir}/{city_name_l}_elevation_source.txt", 'w') as f:
                    f.write('NASA SRTM Digital Elevation 30m')
                break
            time.sleep(30)
    
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_elevation_source.txt", f"{output_dir}/{city_name_l}_elevation_source.txt")

    contour_levels = contour(city_name_l, local_output_dir, cloud_bucket, output_dir)
    elevation_stats(city_name_l, local_output_dir, cloud_bucket, output_dir, contour_levels)

def contour(city_name_l, local_output_dir, cloud_bucket, output_dir):
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon
    import fiona
    import math
    import rasterio
    from affine import Affine
    import utils

    with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation.tif') as src:
        elevation_data = src.read(1)
        bounds = src.bounds
        transform = src.transform
        width = src.width
        height = src.height
    
    # Use the rasterio transform to map pixel coordinates to geographic coordinates
    # Get the bounding box
    min_x, min_y, max_x, max_y = bounds
    transform = Affine.from_gdal(min_x, (max_x - min_x) / width, 0, max_y, 0, (min_y - max_y) / height)

    # Define no-data value
    demNan = -9999

    # Get min and max elevation values
    demMax = elevation_data.max()
    demMin = elevation_data[elevation_data != demNan].min()
    demDiff = demMax - demMin

    # Generate contour lines
    # Determine contour intervals
    contourInt = 1
    if demDiff > 250:
        contourInt = math.ceil(demDiff / 500) * 10
    elif demDiff > 100:
        contourInt = 5
    elif demDiff > 50:
        contourInt = 2
    
    contourMin = math.floor(demMin / contourInt) * contourInt
    contourMax = math.ceil(demMax / contourInt) * contourInt
    if contourMin < demMin:
        contour_levels = range(contourMin + contourInt, contourMax + contourInt, contourInt)
    else:
        contour_levels = range(contourMin, contourMax + contourInt, contourInt)

    contours = plt.contourf(elevation_data, levels=contour_levels)

    # Create a list to hold all the contour polygons as shapely geometries
    contour_polygons = []

    # Iterate over all contour levels and their corresponding paths
    for collection, level in zip(contours.collections, contour_levels):
        for path in collection.get_paths():
            for polygon in path.to_polygons():
                if len(polygon) > 0:
                    # Convert polygon coordinates from pixel space to geographic coordinates
                    geographic_polygon = [
                        (transform * (x, y)) for x, y in polygon
                    ]
                    poly = Polygon(geographic_polygon)
                    contour_polygons.append((poly, level))

    # Optionally save to a shapefile using Fiona
    schema = {
        'geometry': 'Polygon',
        'properties': {'elevation': 'float'},
    }

    with fiona.open(f'{local_output_dir}/{city_name_l}_contours.gpkg', 'w', driver='GPKG', schema=schema, crs='EPSG:4326', layer='contours') as shpfile:
        for poly, elevation in contour_polygons:
            shpfile.write({
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [list(poly.exterior.coords)],
                },
                'properties': {'elevation': elevation},
            })

    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_contours.gpkg', f"{output_dir}/{city_name_l}_contours.gpkg")
    return range(contourMin, contourMax + contourInt, contourInt)

    # unused due to gdal containerization issue ########################################
    # contour_levels = raster_pro.contour(f'{local_output_dir}/{city_name_l}_elevation.tif', local_output_dir, city_name_l)
    # utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_contour.gpkg', f'{output_dir}/{city_name_l}_contour.gpkg')

def elevation_stats(city_name_l, local_output_dir, cloud_bucket, output_dir, contour_levels):
    import raster_pro
    import utils

    contour_levels = list(contour_levels)
    contour_bins = [contour_levels[int(((len(contour_levels) - 6) / 5 + 1) * i)] for i in range(6)]
    raster_pro.get_raster_histogram(f'{local_output_dir}/{city_name_l}_elevation.tif', contour_bins, f'{local_output_dir}/{city_name_l}_elevation.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.csv', f'{output_dir}/{city_name_l}_elevation.csv')
