# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['cover_image']:
    import osmnx as ox
    import geopandas as gpd
    import os
    import math
    from pathlib import Path
    ox.config(log_console = True, use_cache = True)

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
    

    # COVER IAMGE PARAMETERS #####################################
    zoom = 4
    network_type = 'drive'
    bldg_color = 'orange'
    dpi = 300
    default_width = 1
    street_widths = {'secondary': 1, 'primary': 1}


    # MAKE IMAGE #######################################

    # def get_network_plus_building_footprints_plot(zoom = 1, network_type = 'drive', bldg_color = 'orange', dpi = 300, default_width = 1, street_widths = None):
    # fp = os.path.abspath(output_folder) + f'/{city_name_l}_network_plus_building_footprints.png'
    fp = os.path.abspath(output_folder) + f'/{city_name_l}_network_building_footprints.png'
    
    # Find centroid
    centroid = features.centroid
    x = centroid[0].coords.xy[0][0]
    y = centroid[0].coords.xy[1][0]
    
    # Find UTM
    utm_zone = math.floor((x + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    
    # Find polygon length to set dist
    poly = features.to_crs(crs = utm_crs)
    length = poly.length[0] / 2 / zoom
    # print('distance:', length)

    gdf = ox.geometries.geometries_from_point((y, x), {'building': True}, dist = length)
    
    # figsize is in inches and can be adjusted to increase the size of the figure
    fig, ax = ox.plot_figure_ground(point = (y, x), figsize = (14, 14), dist = length, 
                                    network_type = network_type, 
                                    default_width = default_width,
                                    street_widths = street_widths, 
                                    save = False, show = True, close = True)
    
    fig, ax = ox.plot_footprints(gdf, ax = ax, 
                                 filepath = fp, 
                                 color = bldg_color, dpi = dpi, 
                                 save = True, show = False, close = True)