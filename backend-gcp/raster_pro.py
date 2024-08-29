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

        if utils.blob_exists(data_bucket, f'{data_bucket_dir}/{dl_file_name}'):
            utils.download_blob(data_bucket, f'{data_bucket_dir}/{dl_file_name}', f'{local_data_dir}/{dl_file_name}')
            downloaded_list.append(f'{local_data_dir}/{dl_file_name}')
        else:
            try:
                print(f'downloading {dl_file_name}')
                dl_file = requests.get(f)
                open(f'{local_data_dir}/{dl_file_name}', 'wb').write(dl_file.content)
                if utils.upload_blob(data_bucket, f'{local_data_dir}/{dl_file_name}', f'{data_bucket_dir}/{dl_file_name}'):
                    downloaded_list.append(f'{local_data_dir}/{dl_file_name}')
            except Exception as e:
                print(f'{dl_file} download exception: {e}')
    
    return downloaded_list

def mosaic_raster(mosaic_list, local_data_dir, mosaic_file):
    # mosaic or rename raster file(s) as needed
    import os
    import rasterio
    from rasterio.merge import merge

    if len(mosaic_list) > 1:
        try:
            mosaic, output = merge(mosaic_list)
            with rasterio.open(mosaic_list[0]) as src:
                output_meta = src.meta.copy()
            output_meta.update(
                {"driver": "GTiff",
                 "height": mosaic.shape[1],
                 "width": mosaic.shape[2],
                 "transform": output,
                }
            )
            with rasterio.open(f'{local_data_dir}/{mosaic_file}', 'w', **output_meta) as m:
                m.write(mosaic)
        except MemoryError:
            print('MemoryError when merging raster files:')
            print(mosaic_list)
            print('Try downloading raw files from cloud storage and using GIS for merging.')
    elif len(mosaic_list) == 1:
        os.rename(mosaic_list[0], f'{local_data_dir}/{mosaic_file}')

def reproject_raster(input_raster, dst_crs, output_raster):
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling

    with rasterio.open(input_raster) as src:
        transform, width, height = calculate_default_transform(src.crs, dst_crs, src.width, src.height, *src.bounds)
        out_meta = src.meta.copy()
        out_meta.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(output_raster, 'w', **out_meta) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)

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

def contour(elev_raster, local_output_dir, city_name_l):
    print('run contour')

    from osgeo import osr, ogr, gdal
    import math

    # Open the elevation raster
    rasterDs = gdal.Open(str(elev_raster))
    rasterBand = rasterDs.GetRasterBand(1)
    proj = osr.SpatialReference(wkt=rasterDs.GetProjection())

    # Get elevation data as a numpy array
    elevArray = rasterBand.ReadAsArray()

    # Define no-data value
    demNan = -9999

    # Get min and max elevation values
    demMax = elevArray.max()
    demMin = elevArray[elevArray != demNan].min()
    demDiff = demMax - demMin

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
    contourLevels = range(contourMin, contourMax + contourInt, contourInt)
    
    # Create contour shapefile
    contourPath = f'{local_output_dir}/{city_name_l}_contour.gpkg'
    contourDs = ogr.GetDriverByName("GPKG").CreateDataSource(contourPath)
    contourShp = contourDs.CreateLayer('contour', proj)

    # Define fields for ID and elevation
    fieldDef = ogr.FieldDefn("ID", ogr.OFTInteger)
    contourShp.CreateField(fieldDef)
    fieldDef = ogr.FieldDefn("elev", ogr.OFTReal)
    contourShp.CreateField(fieldDef)

    # Generate contours
    for level in contourLevels:
        gdal.ContourGenerate(rasterBand, level, level, [], 1, demNan, contourShp, 0, 1)

    # Clean up
    contourDs.Destroy()

    # Return contour levels for elevation_stats
    return contourLevels

def slope(elev_raster, cloud_bucket, output_dir, city_name_l, local_output_dir):
    print('run slope')

    import os
    import utils
    import richdem as rd
    from google.api_core.exceptions import NotFound

    if not os.path.exists(elev_raster):
        try:
            utils.download_blob(cloud_bucket, f'{output_dir}/{city_name_l}_elevation.tif', elev_raster)
        except NotFound:
            print('no elevation raster file exists')
            return

    # Reproject elevation raster to a projected coordinate system
    reproject_raster(elev_raster, 'EPSG:3857', f'{local_output_dir}/{city_name_l}_elevation_3857.tif')

    # Calculate slope
    elev = rd.LoadGDAL(f'{local_output_dir}/{city_name_l}_elevation_3857.tif')
    slope = rd.TerrainAttribute(elev, attrib = 'slope_degrees')
    rd.SaveGDAL(f'{local_output_dir}/{city_name_l}_slope_3857.tif', slope)

    # Reproject slope raster to WGS84
    reproject_raster(f'{local_output_dir}/{city_name_l}_slope_3857.tif', 'EPSG:4326', f'{local_output_dir}/{city_name_l}_slope.tif')

    # Remove intermediate outputs
    try:
        os.remove(f'{local_output_dir}/{city_name_l}_elevation_3857.tif')
        os.remove(f'{local_output_dir}/{city_name_l}_slope_3857.tif')
    except:
        pass
    