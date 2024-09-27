# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['erosion']:
    print('run erosion')

    import os
    import geopandas as gpd
    from pathlib import Path
    from os.path import exists

    # SET UP #########################################
    # load city inputs files, to be updated for each city scan
    with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
        city_inputs = yaml.safe_load(f)

    city_name_l = city_inputs['city_name'].replace(' ', '_').replace("'", '').lower()

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


    # PROCESS DATA ##################################
    if not exists(output_folder / f'{city_name_l}_erosion_accretion' / f'{city_name_l}_erosion_accretion.shp'):
        # Buffer AOI ------------------
        xmin, ymin, xmax, ymax = aoi_file.total_bounds
        aoi_buff = aoi_file.buffer(max(xmax-xmin, ymax-ymin))
        features = aoi_buff.geometry

        # Read data --------------
        if global_inputs['erosion_source'] == "":
            real_nodes = gpd.read_file("C:/Users/Owner/OneDrive/Documents/Career/World Bank/CRP/Bangladesh LGCRRP/data/bangladesh_REAL_nodes.shp")
        else:
            real_nodes = gpd.read_file(global_inputs['erosion_source'])

        # Filter REAL data ----------------
        real_aoi = real_nodes[real_nodes.geometry.intersects(features.unary_union)]

        # Save nodes to shapefile ----------------
        if not os.path.exists(output_folder / f'{city_name_l}_erosion_accretion'):
            os.mkdir(output_folder / f'{city_name_l}_erosion_accretion')
        real_aoi.to_file(output_folder / f'{city_name_l}_erosion_accretion' / f'{city_name_l}_erosion_accretion.shp')
