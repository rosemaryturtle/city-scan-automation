def burned_area(aoi_file, gf_folder, data_bucket, local_data_dir, local_output_dir, city_name_l, cloud_bucket, output_dir):
    print('run burned_area')

    import os
    import pandas as pd
    import geopandas as gpd
    import utils

    # SET PARAMETERS ################################
    # Buffer AOI ------------------
    aoi_buff = aoi_file.buffer(1)  # 1 degree is about 111 km at the equator
    features = aoi_buff.geometry[0]

    # Set time period --------------
    years = range(2011, 2021)
    months = range(1, 13)

    # Make local data folder --------------
    local_gf_folder = f'{local_data_dir}/gf'
    os.makedirs(local_gf_folder, exist_ok=True)


    # PROCESS DATA ##################################
    df = pd.DataFrame(columns=['year', 'month', 'x', 'y'])

    for year in years:
        for month in months:
            print(f'year: {year}, month: {month}')
            
            # Filter GlobFire ----------------
            shp_names = [f'MODIS_BA_GLOBAL_1_{month}_{year}.{suf}' for suf in ['cpg', 'dbf', 'prj', 'shp', 'shx']]
            for f in shp_names:
                utils.download_blob(data_bucket, f'{gf_folder}/{f}', f'{local_gf_folder}/{f}')
            gf_shp = gpd.read_file(f'{local_gf_folder}/MODIS_BA_GLOBAL_1_{month}_{year}.shp')
            gf_aoi = gf_shp[gf_shp.intersects(features)]

            # Find centroids ----------------
            gf_aoi = gf_aoi[gf_aoi['Type'] == 'FinalArea'].centroid
            for i in gf_aoi:
                df.loc[len(df.index)] = [year, month, i.x, i.y]
            
            # Delete downloaded files -----------------
            for f in shp_names:
                os.remove(f'{local_gf_folder}/{f}')
    
    # Save centroids to geopackage ----------------
    gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y, crs = 'EPSG:4326')).to_file(f'{local_output_dir}/{city_name_l}_globfire_centroids.gpkg', driver='GPKG', layer = 'burned_area')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_globfire_centroids.gpkg', f'{output_dir}/{city_name_l}_globfire_centroids.gpkg')