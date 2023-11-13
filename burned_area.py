# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['burned_area']:
    import os
    import geopandas as gpd
    from pathlib import Path

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs, such as data sources that generally remain the same across scans
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Read AOI shapefile --------
    # transform the input shp to correct prj (epsg 4326)
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)
    features = aoi_file.geometry

    # Define output folder ---------
    output_folder = Path('output')

    if not os.path.exists(output_folder):
        os.mkdir(output_folder)


    # SET PARAMETERS ################################
    # Set data folder --------------
    data_folder = Path(r"C:\Users\Owner\Documents\Career\World Bank\CRP\data\GlobFire")

    # Buffer AOI ------------------
    aoi_buff = aoi_file.buffer(1)  # 1 degree is about 111 km at the equator

    # Set time period ------------
    years = range(2011, 2021)
    months = range(1, 13)


    # PROCESS DATA ##################################
    for year in years:
        for month in months:
            shp_name = f'MODIS_BA_GLOBAL_1_{month}_{year}.shp'
            gf_shp = gpd.read_file(data_folder / shp_name)
            gf_aoi = gf_shp.intersects(aoi_buff)
            
            
