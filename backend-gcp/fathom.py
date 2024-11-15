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
                if utils.upload_blob(data_bucket, f'{local_flood_folder}/{f[7:]}', f'{data_bucket_dir}/{f[7:]}', output=False):
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

    out_image = np.squeeze(np.maximum.reduce(raster_arrays).astype(np.uint8))
    out_meta.update(dtype = rasterio.uint8)

    with rasterio.open(output_raster, 'w', **out_meta) as dst:
        dst.write(out_image, 1)

def calculate_flood_wsf_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, flood_raster):
    import utils
    import raster_pro
    import rasterio
    import numpy as np

    # download wsf evolution raster
    if utils.download_blob_timed(cloud_bucket, f"{output_dir}/spatial/{city_name_l}_wsf_evolution_utm.tif", f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', 180*60, 60):
        # reproject flood raster to match wsf raster grid
        raster_pro.reproject_raster(f'{local_output_dir}/{flood_raster}', f'{local_output_dir}/{flood_raster[:-4]}_wsf.tif', target_raster_path=f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif')

        # computer zonal stats
        flood_stats = {}

        with rasterio.open(f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif') as wsf:
            wsf_array = wsf.read(1)
            pixelSizeX, pixelSizeY = wsf.res

            with rasterio.open(f'{local_output_dir}/{flood_raster[:-4]}_wsf.tif') as fld:
                flood_array = fld.read(1)
                for year in range(1985, 2016):
                    exposed_sqkm = np.count_nonzero(flood_array[wsf_array == year]) * pixelSizeX * pixelSizeY / 1e6
                    flood_stats[year] = exposed_sqkm + flood_stats.get(year - 1, 0)
        
        return flood_stats
    return

def calculate_flood_pop_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, flood_raster):
    import utils
    import rasterio
    import numpy as np
    from rasterio.warp import reproject, Resampling

    # download population raster
    if utils.download_blob_timed(cloud_bucket, f"{output_dir}/spatial/{city_name_l}_population.tif", f'{local_output_dir}/{city_name_l}_population.tif', 180*60, 60):
        # reproject flood raster to match population raster grid
        with rasterio.open(f'{local_output_dir}/{city_name_l}_population.tif') as target_raster:
            dst_crs = target_raster.crs  # Use the CRS from the target raster
            target_transform = target_raster.transform
            target_meta = target_raster.meta.copy()
        
        with rasterio.open(f'{local_output_dir}/{flood_raster}') as src_raster:
            # Create output raster metadata
            dst_meta = src_raster.meta.copy()
            dst_meta.update({
                'crs': dst_crs,
                'transform': target_transform,
                'width': target_meta['width'],
                'height': target_meta['height']
            })

            # Open the destination raster for writing
            with rasterio.open(f'{local_output_dir}/{flood_raster[:-4]}_pop.tif', 'w', **dst_meta) as dst_raster:
                # Reproject and write to the new file
                for i in range(1, src_raster.count + 1):
                    reproject(
                        source=rasterio.band(src_raster, i),
                        destination=rasterio.band(dst_raster, i),
                        src_transform=src_raster.transform,
                        src_crs=src_raster.crs,
                        dst_transform=target_transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.mode
                    )
        
        # computer dense population exposure
        with rasterio.open(f'{local_output_dir}/{city_name_l}_population.tif') as pop:
            pop_array = pop.read(1)
            pop_nodata = -99999
            pop_array = np.where(pop_array == pop_nodata, np.nan, pop_array)

            with rasterio.open(f'{local_output_dir}/{flood_raster[:-4]}_pop.tif') as fld:
                flood_array = fld.read(1)
            
            pop60 = np.nanpercentile(pop_array, 60)
            pop_array_60 = np.where(pop_array >= pop60, 1, 0)

            exposed_pop = np.count_nonzero(flood_array[pop_array_60 == 1]) / np.nansum(pop_array_60)
            return exposed_pop
    return

def calculate_flood_osm_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, poi, flood_raster):
    import geopandas as gpd
    import rasterio
    import utils

    # download and load osm shapefile
    if utils.download_blob_timed(cloud_bucket, f"{output_dir}/spatial/{city_name_l}_osm_{poi}.gpkg", f'{local_output_dir}/{city_name_l}_osm_{poi}.gpkg', 180*60, 60):
        osm_gdf = gpd.read_file(f'{local_output_dir}/{city_name_l}_osm_{poi}.gpkg', layer = poi)

        # Load the flood zone raster
        with rasterio.open(f'{local_output_dir}/{flood_raster}') as src:
            flood_data = src.read(1)  # Read the first band (assuming single-band raster)
            flood_transform = src.transform  # Get the affine transformation matrix

        # Function to check if a point is in a flood zone
        def is_in_flood_zone(point, flood_data, transform):
            # Convert point coordinates to row, col in raster space
            row, col = ~transform * (point.x, point.y)
            row, col = int(row), int(col)
            
            # Check if the point falls within the bounds of the raster
            if 0 <= row < flood_data.shape[0] and 0 <= col < flood_data.shape[1]:
                # Return True if the value at that location is greater than 0 (flood zone)
                return flood_data[row, col] > 0
            return False

        # Apply the function to each osm location
        osm_gdf['in_flood_zone'] = osm_gdf['geometry'].apply(lambda point: is_in_flood_zone(point, flood_data, flood_transform))

        # Calculate total number of locations and those in flood zones
        total_pois = len(osm_gdf)
        pois_in_flood_zone = osm_gdf['in_flood_zone'].sum()

        # Calculate percentage of pois in flood zones
        percentage_in_flood_zone = (pois_in_flood_zone / total_pois) * 100

        # Return results
        return total_pois, pois_in_flood_zone, percentage_in_flood_zone
    return

def calculate_flood_road_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, utm_crs, flood_raster):
    import geopandas as gpd
    import rasterio
    from rasterio.features import geometry_mask
    from shapely.geometry import LineString
    import utils

    # Step 1: Load the roads layer from the GeoPackage
    if utils.download_blob_timed(cloud_bucket, f"{output_dir}/spatial/{city_name_l}_major_roads.gpkg", f'{local_output_dir}/{city_name_l}_major_roads.gpkg', 180*60, 60):
        major_roads_gdf = gpd.read_file(f'{local_output_dir}/{city_name_l}_major_roads.gpkg', layer='major_roads').to_crs(utm_crs)

        # Step 2: Load the flood zone raster
        with rasterio.open(f'{local_output_dir}/{flood_raster}') as src:
            flood_data = src.read(1)  # Read first band (assuming single-band raster)
            flood_transform = src.transform  # Get affine transformation

        # Step 3: Function to clip a line to flood zones and calculate length
        def clip_line_to_flood_zone(line, flood_data, transform):
            # Convert line geometry to raster space and create a mask
            mask = geometry_mask([line], transform=transform, invert=True, out_shape=flood_data.shape)
            
            # Check if any part of the line overlaps with a flood zone (value > 0)
            if (flood_data[mask] > 0).any():
                # Create a polygon representing all flood zones in the raster
                flood_zone_mask = (flood_data > 0)
                flood_zone_polygons = []
                
                for shape, value in rasterio.features.shapes(flood_zone_mask.astype('uint8'), transform=transform):
                    if value == 1:
                        flood_zone_polygons.append(shape)
                
                # Convert polygons to GeoDataFrame for intersection
                flood_zones_gdf = gpd.GeoDataFrame(geometry=[LineString(p['coordinates']) for p in flood_zone_polygons], crs=major_roads_gdf.crs)
                
                # Clip the line by intersecting it with flood zones
                clipped_line = line.intersection(flood_zones_gdf.unary_union)
                
                # Return total length of clipped line if it intersects with any flood zone
                return clipped_line.length if not clipped_line.is_empty else 0
            
            return 0

        # Step 4: Apply clipping function to each major road segment and calculate total length in flood zones
        major_roads_gdf['flood_zone_length'] = major_roads_gdf['geometry'].apply(lambda line: clip_line_to_flood_zone(line, flood_data, flood_transform))

        # Calculate total length of major roads and those in flood zones
        total_major_road_length = major_roads_gdf.length.sum()
        length_in_flood_zones = major_roads_gdf['flood_zone_length'].sum()

        # Calculate percentage of major roads in flood zones
        percentage_in_flood_zones = (length_in_flood_zones / total_major_road_length) * 100

        # Return results
        return total_major_road_length, length_in_flood_zones, percentage_in_flood_zones
    return

def process_fathom(aoi_file, city_name_l, local_data_dir, city_inputs, menu, aws_access_key_id, aws_secret_access_key, aws_bucket, data_bucket, data_bucket_dir, local_output_dir, cloud_bucket, output_dir):
    print('run process_fathom')
    
    import raster_pro
    import numpy as np
    import utils
    import pandas as pd
    from os.path import exists
    import rasterio

    # set parameters
    flood_threshold = city_inputs['flood']['threshold']
    flood_years = city_inputs['flood']['year']
    flood_ssps = city_inputs['flood']['ssp']
    flood_prob_cutoff = city_inputs['flood']['prob_cutoff']
    flood_types = ['coastal', 'fluvial', 'pluvial']
    osm_pois = None
    if ('osm_query' in city_inputs) and bool(city_inputs['osm_query']):
        osm_pois = city_inputs['osm_query']

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
    
    flood_wsf_stats = {}
    flood_pop_stats = {}
    flood_osm_stats = {}
    flood_road_stats = {}

    for ft in flood_types:
        if menu[f'flood_{ft}']:
            flood_wsf_stats[ft] = {}
            flood_pop_stats[ft] = {}
            flood_osm_stats[ft] = {}
            flood_road_stats[ft] = {}
            for year in flood_years:
                flood_wsf_stats[ft][year] = {}
                flood_osm_stats[ft][year] = {}
                if year <= 2020:
                    out_image_arrays = []
                    for rp in rps:
                        download_list = []
                        for lat in lat_tiles:
                            for lon in lon_tiles:
                                download_list.append(f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft]}-DEPTH-{year}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif")
                                downloaded_list = download_fathom_from_aws(download_list, aws_access_key_id, aws_secret_access_key, aws_bucket, local_flood_folder, data_bucket, data_bucket_dir)
                        if downloaded_list:
                            mosaic_file = f"{downloaded_list[0].split('/')[3]}.tif"
                            raster_pro.mosaic_raster(downloaded_list, local_flood_folder, mosaic_file)
                            out_image, out_meta = raster_pro.raster_mask_file(f'{local_flood_folder}/{mosaic_file}', buffer_aoi.geometry)
                            out_image, out_meta = apply_flood_threshold(out_image, out_meta, flood_threshold, rp_multipliers[rp])
                            out_image_arrays.append(out_image)
                    if out_image_arrays:
                        composite_flood_raster(out_image_arrays, out_meta, f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif')
                        raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif', f'{local_output_dir}/{city_name_l}_{ft}_{year}_utm.tif', dst_crs=utm_crs)

                        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif', f'{output_dir}/{city_name_l}_{ft}_{year}.tif')
                        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_utm.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_utm.tif')

                        flood_wsf_stats[ft][year] = calculate_flood_wsf_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_{ft}_{year}.tif')
                        flood_pop_stats[ft][year] = calculate_flood_pop_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_{ft}_{year}.tif')
                        flood_road_stats[ft][year] = calculate_flood_road_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, utm_crs, f'{city_name_l}_{ft}_{year}.tif')
                        if osm_pois is not None:
                            for poi in osm_pois:
                                flood_osm_stats[ft][year][poi] = calculate_flood_osm_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, poi, f'{city_name_l}_{ft}_{year}.tif')

                elif year > 2020:
                    flood_pop_stats[ft][year] = {}
                    flood_road_stats[ft][year] = {}
                    for ssp in flood_ssps:
                        out_image_arrays = []
                        for rp in rps:
                            download_list = []
                            for lat in lat_tiles:
                                for lon in lon_tiles:
                                    download_list.append(f"FATHOM/v2023/GLOBAL-1ARCSEC-NW_OFFSET-1in{rp}-{flood_type_folder_dict[ft]}-DEPTH-{year}-SSP{flood_ssp_labels[ssp]}-PERCENTILE50-v3.0/{lat.lower()}{lon.lower()}.tif")
                                    downloaded_list = download_fathom_from_aws(download_list, aws_access_key_id, aws_secret_access_key, aws_bucket, local_flood_folder, data_bucket, data_bucket_dir)
                            if downloaded_list:
                                mosaic_file = f"{downloaded_list[0].split('/')[3]}.tif"
                                raster_pro.mosaic_raster(downloaded_list, local_flood_folder, mosaic_file)
                                out_image, out_meta = raster_pro.raster_mask_file(f'{local_flood_folder}/{mosaic_file}', buffer_aoi.geometry)
                                out_image, out_meta = apply_flood_threshold(out_image, out_meta, flood_threshold, rp_multipliers[rp])
                                out_image_arrays.append(out_image)
                        if out_image_arrays:
                            composite_flood_raster(out_image_arrays, out_meta, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif', f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif', dst_crs=utm_crs)
                            
                            utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif', f'{output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}_utm.tif')
                            
                            flood_wsf_stats[ft][year][ssp] = calculate_flood_wsf_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            flood_pop_stats[ft][year][ssp] = calculate_flood_pop_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            flood_road_stats[ft][year][ssp] = calculate_flood_road_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, utm_crs, f'{city_name_l}_{ft}_{year}_ssp{ssp}.tif')
                            flood_osm_stats[ft][year][ssp] = {}
                            if osm_pois is not None:
                                for poi in osm_pois:
                                    flood_osm_stats[ft][year][ssp][poi] = calculate_flood_osm_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, poi, f'{city_name_l}_{ft}_{year}_ssp{ssp}.tif')

    # combine flood raster of different types
    flood_wsf_stats['comb'] = {}
    flood_pop_stats['comb'] = {}
    flood_osm_stats['comb'] = {}
    flood_road_stats['comb'] = {}

    for year in flood_years:
        flood_osm_stats['comb'][year] = {}
        if year <= 2020:
            comb_array = []
            for ft in flood_types:
                if exists(f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif'):
                    with rasterio.open(f'{local_output_dir}/{city_name_l}_{ft}_{year}.tif') as src:
                        comb_array.append(src.read(1))
                        out_meta = src.meta.copy()
            if comb_array:
                composite_flood_raster(comb_array, out_meta, f'{local_output_dir}/{city_name_l}_comb_{year}.tif')
                raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_comb_{year}.tif', f'{local_output_dir}/{city_name_l}_comb_{year}_utm.tif', dst_crs=utm_crs)

                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_comb_{year}.tif', f'{output_dir}/{city_name_l}_comb_{year}.tif')
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_comb_{year}_utm.tif', f'{output_dir}/{city_name_l}_comb_{year}_utm.tif')

                flood_wsf_stats['comb'][year] = calculate_flood_wsf_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_comb_{year}.tif')
                flood_pop_stats['comb'][year] = calculate_flood_pop_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_comb_{year}.tif')
                flood_road_stats['comb'][year] = calculate_flood_road_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, utm_crs, f'{city_name_l}_comb_{year}.tif')
                if osm_pois is not None:
                    for poi in osm_pois:
                        flood_osm_stats['comb'][year][poi] = calculate_flood_osm_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, poi, f'{city_name_l}_comb_{year}.tif')
        elif year > 2020:
            flood_wsf_stats['comb'][year] = {}
            flood_pop_stats['comb'][year] = {}
            flood_road_stats['comb'][year] = {}
            for ssp in flood_ssps:
                comb_array = []
                for ft in flood_types:
                    if exists(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif'):
                        with rasterio.open(f'{local_output_dir}/{city_name_l}_{ft}_{year}_ssp{ssp}.tif') as src:
                            comb_array.append(src.read(1))
                            out_meta = src.meta.copy()
                if comb_array:
                    composite_flood_raster(comb_array, out_meta, f'{local_output_dir}/{city_name_l}_comb_{year}_ssp{ssp}.tif')
                    raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_comb_{year}_ssp{ssp}.tif', f'{local_output_dir}/{city_name_l}_comb_{year}_ssp{ssp}_utm.tif', dst_crs=utm_crs)

                    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_comb_{year}_ssp{ssp}.tif', f'{output_dir}/{city_name_l}_comb_{year}_ssp{ssp}.tif')
                    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_comb_{year}_ssp{ssp}_utm.tif', f'{output_dir}/{city_name_l}_comb_{year}_ssp{ssp}_utm.tif')

                    flood_wsf_stats['comb'][year][ssp] = calculate_flood_wsf_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_comb_{year}_ssp{ssp}.tif')
                    flood_pop_stats['comb'][year][ssp] = calculate_flood_pop_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, f'{city_name_l}_comb_{year}_ssp{ssp}.tif')
                    flood_road_stats['comb'][year][ssp] = calculate_flood_road_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, utm_crs, f'{city_name_l}_comb_{year}_ssp{ssp}.tif')
                    flood_osm_stats['comb'][year][ssp] = {}
                    if osm_pois is not None:
                        for poi in osm_pois:
                            flood_osm_stats['comb'][year][ssp][poi] = calculate_flood_osm_stats(cloud_bucket, output_dir, local_output_dir, city_name_l, poi, f'{city_name_l}_comb_{year}_ssp{ssp}.tif')
    
    # save flood stats as csv and upload
    # wsf
    rows = []

    for ft in flood_wsf_stats:
        for year in flood_wsf_stats[ft]:
            if list(flood_wsf_stats[ft][year].values()):
                if isinstance(list(flood_wsf_stats[ft][year].values())[0], dict):
                    for ssp in flood_ssps:
                        for yr in range(1985, 2016):
                            rows.append([yr, f'{ft}_{year}_ssp{ssp}', flood_wsf_stats[ft][year][ssp][yr]])
                else:
                    for yr in range(1985, 2016):
                        rows.append([yr, f'{ft}_{year}', flood_wsf_stats[ft][year][yr]])

    df = pd.DataFrame(rows, columns=['year', 'type', 'exposed_built_up_sqkm'])
    df_pivot = df.pivot(index='year', columns='type', values='exposed_built_up_sqkm')

    df_pivot.to_csv(f'{local_output_dir}/{city_name_l}_flood_wsf.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_flood_wsf.csv', f'{output_dir}/{city_name_l}_flood_wsf.csv')

    # pop
    rows = []

    for ft in flood_pop_stats:
        for year in flood_pop_stats[ft]:
            if isinstance(flood_pop_stats[ft][year], (int, float)):
                rows.append([f'{ft}_{year}', flood_pop_stats[ft][year]])
            elif isinstance(flood_pop_stats[ft][year], dict):
                for ssp in flood_ssps:
                    rows.append([f'{ft}_{year}_ssp{ssp}', flood_pop_stats[ft][year][ssp]])
    
    df = pd.DataFrame(rows, columns=['type', 'exposed_dense_pop_pct'])

    df.to_csv(f'{local_output_dir}/{city_name_l}_flood_pop.csv', index=False)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_flood_pop.csv', f'{output_dir}/{city_name_l}_flood_pop.csv')

    # osm
    rows = []
    
    for ft in flood_osm_stats:
        for year in flood_osm_stats[ft]:
            if list(flood_osm_stats[ft][year].values()):
                if isinstance(list(flood_osm_stats[ft][year].values())[0], dict):
                    for ssp in flood_ssps:
                        for poi in osm_pois:
                            total_pois, pois_in_flood_zone, percentage_in_flood_zone = flood_osm_stats[ft][year][ssp][poi]
                            rows.append([poi, f'{ft}_{year}_ssp{ssp}', total_pois, pois_in_flood_zone, percentage_in_flood_zone])
                else:
                    for poi in osm_pois:
                        total_pois, pois_in_flood_zone, percentage_in_flood_zone = flood_osm_stats[ft][year][poi]
                        rows.append([poi, f'{ft}_{year}', total_pois, pois_in_flood_zone, percentage_in_flood_zone])

    df = pd.DataFrame(rows, columns=['poi', 'type', 'total_pois', 'pois_in_flood_zone', 'percentage_in_flood_zone'])

    df.to_csv(f'{local_output_dir}/{city_name_l}_flood_osm.csv', index=False)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_flood_osm.csv', f'{output_dir}/{city_name_l}_flood_osm.csv')

    # road
    rows = []

    for ft in flood_road_stats:
        for year in flood_road_stats[ft]:
            if isinstance(flood_road_stats[ft][year], tuple):
                total_major_road_length, length_in_flood_zones, percentage_in_flood_zones = flood_road_stats[ft][year]
                rows.append([f'{ft}_{year}', total_major_road_length, length_in_flood_zones, percentage_in_flood_zones])
            elif isinstance(flood_road_stats[ft][year], dict):
                for ssp in flood_ssps:
                    total_major_road_length, length_in_flood_zones, percentage_in_flood_zones = flood_road_stats[ft][year][ssp]
                    rows.append([f'{ft}_{year}_ssp{ssp}', total_major_road_length, length_in_flood_zones, percentage_in_flood_zones])
    
    df = pd.DataFrame(rows, columns=['type', 'total_major_road_meter', 'meter_in_flood_zones', 'percentage_in_flood_zones'])

    df.to_csv(f'{local_output_dir}/{city_name_l}_flood_road.csv', index=False)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_flood_road.csv', f'{output_dir}/{city_name_l}_flood_road.csv')
