def raster_mask_bytes(raster_bytes, features):
    import rasterio.mask
    from rasterio.io import MemoryFile

    with MemoryFile(raster_bytes) as memfile:
        with memfile.open() as src:
            out_image, out_transform = rasterio.mask.mask(
                src, features, all_touched = True, crop = True)
            out_meta = src.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})

    return out_image, out_meta

def raster_mask_file(raster_file, features):
    import rasterio
    import rasterio.mask

    with rasterio.open(raster_file) as src:
        out_image, out_transform = rasterio.mask.mask(
            src, features, all_touched = True, crop = True)
        out_meta = src.meta.copy()

    out_meta.update({"driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform})

    return out_image, out_meta

def tile_finder(aoi_file, direction, tile_size = 1):
    import math

    aoi_bounds = aoi_file.bounds

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
        exit()

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

def coord_converter(coord):
    if coord[0] in ['N', 'E']:
        return int(coord[1:])
    elif coord[0] in ['S', 'W']:
        return int(coord[1:])*(-1)
    else:
        print('invalid input to coord_converter')
        return

def fabdem_big_tile_matcher(small_tile_lat, small_tile_lon):
    small_tile_lat = coord_converter(small_tile_lat)
    small_tile_lon = coord_converter(small_tile_lon)
    
    import math

    big_tile_lat = math.floor(small_tile_lat/10) * 10
    big_tile_lon = math.floor(small_tile_lon/10) * 10

    big_tile_lat = f'{"S" if big_tile_lat < 0 else "N"}{str(abs(big_tile_lat)).zfill(2)}'
    big_tile_lon = f'{"W" if big_tile_lon < 0 else "E"}{str(abs(big_tile_lon)).zfill(3)}'

    return big_tile_lat, big_tile_lon

def fabdem_tile_end_matcher(tile_starter):
    if tile_starter == 'S10':
        return 'N00'
    elif tile_starter == 'W010':
        return 'E000'
    elif tile_starter[0] == 'N' or tile_starter[0] == 'E':
        return f'{tile_starter[0]}{str(int(tile_starter[1:]) + 10).zfill(len(tile_starter) - 1)}'
    elif tile_starter[0] == 'S' or tile_starter[0] == 'W':
        return f'{tile_starter[0]}{str(int(tile_starter[1:]) - 10).zfill(len(tile_starter) - 1)}'
    else:
        print('fabdem_tile_end_matcher function error')
        print('Invalid input. How did this happen?')

def download_raster(download_list, local_data_dir, data_bucket, data_bucket_dir):
    # download requested raster file(s) and return a list of downloaded raster file(s)
    if not download_list:
        print('download_raster function error: download_list is empty')
        exit()

    import requests
    import utils
    
    downloaded_list = []

    for f in download_list:
        dl_file_name = f.split('/')[-1]

        if utils.download_blob(data_bucket, f'{data_bucket_dir}/{dl_file_name}', f'{local_data_dir}/{dl_file_name}'):
            downloaded_list.append(f'{local_data_dir}/{dl_file_name}')
        else:
            try:
                print(f'downloading {dl_file_name}')
                dl_file = requests.get(f)
                if dl_file.status_code == 200:
                    open(f'{local_data_dir}/{dl_file_name}', 'wb').write(dl_file.content)
                    if utils.upload_blob(data_bucket, f'{local_data_dir}/{dl_file_name}', f'{data_bucket_dir}/{dl_file_name}', type='data'):
                        downloaded_list.append(f'{local_data_dir}/{dl_file_name}')
                else:
                    print(f"Failed to download. HTTP status code: {dl_file.status_code}")
            except Exception as e:
                print(f'{dl_file} download exception: {e}')
    
    return downloaded_list

def mosaic_raster(mosaic_list, local_output_dir, mosaic_file, method = 'first'):
    # mosaic or rename raster file(s) as needed
    import os
    import rasterio
    from rasterio.merge import merge

    if len(mosaic_list) > 1:
        try:
            mosaic, output = merge(mosaic_list, method = method)
            with rasterio.open(mosaic_list[0]) as src:
                output_meta = src.meta.copy()
            output_meta.update(
                {"driver": "GTiff",
                 "height": mosaic.shape[1],
                 "width": mosaic.shape[2],
                 "transform": output,
                }
            )
            with rasterio.open(f'{local_output_dir}/{mosaic_file}', 'w', **output_meta) as m:
                m.write(mosaic)
        except MemoryError:
            print('MemoryError when merging raster files:')
            print(mosaic_list)
            print('Try downloading raw files from cloud storage and using GIS for merging.')
    elif len(mosaic_list) == 1:
        os.rename(mosaic_list[0], f'{local_output_dir}/{mosaic_file}')

def reproject_raster(src_raster_path, dst_raster_path, dst_crs=None, target_raster_path=None):
    """
    Reproject a raster to a new CRS, with an option to match the grid to a target raster.
    
    Parameters:
        src_raster_path (str): Path to the input raster.
        dst_raster_path (str): Path to the output raster.
        dst_crs (str, optional): The target CRS (e.g., 'EPSG:4326'). Ignored if target_raster_path is provided.
        target_raster_path (str, optional): Path to the target raster to match the CRS and grid.
    
    Raises:
        ValueError: If neither dst_crs nor target_raster_path is provided.
    """

    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    # Check if both dst_crs and target_raster_path are None
    if dst_crs is None and target_raster_path is None:
        raise ValueError("Either 'dst_crs' or 'target_raster_path' must be specified.")
    
    # If target_raster_path is provided, use its CRS and transform
    if target_raster_path:
        with rasterio.open(target_raster_path) as target_raster:
            dst_crs = target_raster.crs  # Use the CRS from the target raster
            target_transform = target_raster.transform
            target_meta = target_raster.meta.copy()

    # Open the source raster
    with rasterio.open(src_raster_path) as src_raster:
        
        # If we are not matching a target raster, calculate the default transform
        if not target_raster_path:
            transform, width, height = calculate_default_transform(
                src_raster.crs, dst_crs, src_raster.width, src_raster.height, *src_raster.bounds)
        else:
            # Use the target raster's transform (i.e., match its grid)
            transform = target_transform
            width = target_meta['width']
            height = target_meta['height']

        # Create output raster metadata
        dst_meta = src_raster.meta.copy()
        dst_meta.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        # Open the destination raster for writing
        with rasterio.open(dst_raster_path, 'w', **dst_meta) as dst_raster:
            # Reproject and write to the new file
            for i in range(1, src_raster.count + 1):
                reproject(
                    source=rasterio.band(src_raster, i),
                    destination=rasterio.band(dst_raster, i),
                    src_transform=src_raster.transform,
                    src_crs=src_raster.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest
                )

def get_raster_histogram(input_raster, bins, output_csv):
    import rasterio
    import numpy as np
    import csv

    with rasterio.open(input_raster) as src:
        # Read raster data
        raster_data = src.read(1)
        
        # Calculate histogram
        hist, _ = np.histogram(raster_data, bins=bins)
        
        # Write bins and hist to a CSV file
        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Bin', 'Count'])
            for i, count in enumerate(hist):
                bin_range = f"{bins[i]}-{bins[i+1]}"
                writer.writerow([bin_range, count])

def calculate_raster_area(input_raster, value_list):
    import rasterio
    import numpy as np

    with rasterio.open(input_raster) as src:
        pixelSizeX, pixelSizeY = src.res
        array = src.read()

        value_dict = {}
        for v in value_list:
            value_dict[v] = np.count_nonzero(array == v) * pixelSizeX * pixelSizeY

        return value_dict

def slope(aoi_file, elev_raster, cloud_bucket, output_dir, city_name_l, local_output_dir):
    print('run slope')

    import os
    import utils
    import rasterio
    import numpy as np

    if not os.path.exists(elev_raster):
        if not utils.download_blob_timed(cloud_bucket, f'{output_dir}/spatial/{city_name_l}_elevation_buf.tif', elev_raster, 30*60, 60):
            return
    
    # Reproject elevation raster to a projected coordinate system
    reproject_raster(elev_raster, f'{local_output_dir}/{city_name_l}_elevation_3857.tif', 'EPSG:3857')

    with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation_3857.tif') as src:
        elevation = src.read(1)
        transform = src.transform
        crs = src.crs
        profile = src.profile

    # Define pixel size (assumed square pixels for simplicity)
    pixel_size_x = transform[0]
    pixel_size_y = -transform[4]

    # Calculate the gradient (difference) in the x and y directions with padding
    padded_elevation = np.pad(elevation, 1, mode='edge')
    dy, dx = np.gradient(padded_elevation, pixel_size_y, pixel_size_x)

    # Remove the padding after calculation
    dy = dy[1:-1, 1:-1]
    dx = dx[1:-1, 1:-1]

    # Calculate the slope in degrees
    slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180 / np.pi)

    # Update the profile for the output slope raster
    profile.update(dtype=rasterio.float32, count=1, compress='lzw')

    # Save the slope array to a new raster file
    with rasterio.open(f'{local_output_dir}/{city_name_l}_slope_3857.tif', 'w', **profile) as dst:
        dst.write(slope.astype(np.float32), 1)

    # Reproject slope raster to WGS84
    reproject_raster(f'{local_output_dir}/{city_name_l}_slope_3857.tif', f'{local_output_dir}/{city_name_l}_slope_4326.tif', 'EPSG:4326')

    # Mask slope raster with AOI
    out_image, out_meta = raster_mask_file(f'{local_output_dir}/{city_name_l}_slope_4326.tif', aoi_file.geometry)
    with rasterio.open(f'{local_output_dir}/{city_name_l}_slope.tif', 'w', **out_meta) as dest:
        dest.write(out_image)

    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_slope.tif', f'{output_dir}/{city_name_l}_slope.tif')
    utils.delete_blob(cloud_bucket, f'{output_dir}/spatial/{city_name_l}_elevation_buf.tif')
    