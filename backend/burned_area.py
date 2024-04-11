# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['burned_area']:
    print('run burned_area')
    
    import os
    import pandas as pd
    import geopandas as gpd
    from pathlib import Path
    from os.path import exists

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs, such as data sources that generally remain the same across scans
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Read AOI shapefile --------
    # transform the input shp to correct prj (epsg 4326)
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)

    # Define output folder ---------
    output_folder = Path('../mnt/city-directories/02-process-output')

    if not exists(output_folder):
        os.mkdir(output_folder)


    # SET PARAMETERS ################################
    # Set data folders --------------
    gf_folder = Path(global_inputs['burned_area_source'])

    # Buffer AOI ------------------
    aoi_buff = aoi_file.buffer(1)  # 1 degree is about 111 km at the equator
    features = aoi_buff.geometry[0]

    # Set time period --------------
    years = range(2011, 2021)
    months = range(1, 13)


    # PROCESS DATA ##################################
    if not exists(output_folder / f'{city_name_l}_globfire_centroids' / f'{city_name_l}_globfire_centroids.shp'):
        df = pd.DataFrame(columns=['year', 'month', 'x', 'y'])

        for year in years:
            for month in months:
                print(f'year: {year}, month: {month}')
                
                # Filter GlobFire ----------------
                shp_name = f'MODIS_BA_GLOBAL_1_{month}_{year}.shp'
                gf_shp = gpd.read_file(gf_folder / shp_name)
                gf_aoi = gf_shp[gf_shp.intersects(features)]

                # Find centroids ----------------
                gf_aoi = gf_aoi[gf_aoi['Type'] == 'FinalArea'].centroid
                for i in gf_aoi:
                    df.loc[len(df.index)] = [year, month, i.x, i.y]
        
        # Save centroids to shapefile ----------------
        if not os.path.exists(output_folder / f'{city_name_l}_globfire_centroids'):
            os.mkdir(output_folder / f'{city_name_l}_globfire_centroids')
        gpd.GeoDataFrame(df, geometry = gpd.points_from_xy(df.x, df.y)).to_file(output_folder / f'{city_name_l}_globfire_centroids' / f'{city_name_l}_globfire_centroids.shp', crs = 'EPSG:4326')
