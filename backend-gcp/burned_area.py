def burned_area(aoi_file, gf_dir, gf_blob_prefix, task_index, data_bucket, local_data_dir, local_output_dir, city_name_l, cloud_bucket, output_dir):
    print('run burned_area')

    import os
    import pandas as pd
    import geopandas as gpd
    import utils

    # SET PARAMETERS ################################
    task_index_range = range(1, 6)

    # Buffer AOI ------------------
    aoi_buff = aoi_file.buffer(1)  # 1 degree is about 111 km at the equator
    features = aoi_buff.geometry[0]

    # Set time period --------------
    years = range(2009 + task_index * 2, 2011 + task_index * 2)
    months = range(1, 13)

    # Make local data folder --------------
    local_gf_folder = f'{local_data_dir}/gf'
    os.makedirs(local_gf_folder, exist_ok=True)


    # PROCESS DATA ##################################
    df = pd.DataFrame(columns=['year', 'month', 'x', 'y'])

    for year in years:
        for month in months:
            # Filter GlobFire ----------------
            shp_names = [f'{gf_blob_prefix}{month}_{year}.{suf}' for suf in ['cpg', 'dbf', 'prj', 'shp', 'shx']]
            for f in shp_names:
                utils.download_blob(data_bucket, f'{gf_dir}/{f}', f'{local_gf_folder}/{f}')
            gf_shp = gpd.read_file(f'{local_gf_folder}/{gf_blob_prefix}{month}_{year}.shp')
            gf_aoi = gf_shp[gf_shp.intersects(features)]

            # Find centroids ----------------
            gf_aoi = gf_aoi[gf_aoi['Type'] == 'FinalArea'].centroid
            for i in gf_aoi:
                df.loc[len(df.index)] = [year, month, i.x, i.y]
            
            # Delete downloaded files -----------------
            for f in shp_names:
                os.remove(f'{local_gf_folder}/{f}')
    
    # Save dataframe to csv -----------------------
    df.to_csv(f'{local_output_dir}/{city_name_l}_globfire_centroids_{task_index}.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_globfire_centroids_{task_index}.csv', f'{output_dir}/{city_name_l}_globfire_centroids_{task_index}.csv')

    # Concatenate csv ------------------------
    if task_index == task_index_range[-1]:
        from datetime import datetime as dt
        import time
        from os.path import exists

        time0 = dt.now()
        while (dt.now()-time0).total_seconds() <= 120*60:
            download_gf_csv = [utils.download_blob(cloud_bucket, 
                                                   f"{output_dir}/tabular/{city_name_l}_globfire_centroids_{ti}.csv", 
                                                   f'{local_output_dir}/{city_name_l}_globfire_centroids_{ti}.csv',
                                                   check_exists=True) for ti in task_index_range]
            if all(download_gf_csv):
                print('all globfire centroids csv files downloaded')
                break
            time.sleep(60)
        
        concat_df = pd.concat([pd.read_csv(f'{local_output_dir}/{city_name_l}_globfire_centroids_{ti}.csv') for ti in task_index_range if exists(f'{local_output_dir}/{city_name_l}_globfire_centroids_{ti}.csv')])

        # Save centroids to geopackage ----------------
        gpd.GeoDataFrame(concat_df, geometry = gpd.points_from_xy(concat_df.x, concat_df.y, crs = 'EPSG:4326')).to_file(f'{local_output_dir}/{city_name_l}_globfire_centroids.gpkg', driver='GPKG', layer = 'burned_area')
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_globfire_centroids.gpkg', f'{output_dir}/{city_name_l}_globfire_centroids.gpkg')

        # Delete csv files -------------------------
        for ti in task_index_range:
            utils.delete_blob(cloud_bucket, f'{output_dir}/tabular/{city_name_l}_globfire_centroids_{ti}.csv')
