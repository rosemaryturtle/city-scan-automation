# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['road_network']:
    import osmnx as ox
    import networkx as nx
    import pandas as pd
    import numpy as np
    from shapely.ops import unary_union
    import geopandas as gpd
    import os
    import matplotlib.pyplot as plt
    import pickle
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
    

    # GET GRAPH #####################################    
    poly = unary_union([i for i in features]).buffer(0)
    
    try:
        with open(output_folder / f'{city_name_l}_osm_roads.pickle', 'rb') as f:
            G = pickle.load(f)
        val = 1
    except FileNotFoundError:
        print("no pickle file found, retrieving new graph via OSMNX")
        G = ox.graph_from_polygon(poly, network_type = 'drive')
        val = 0
        
    print('Writing graph file')
    
    if val != 1:
        # for networkX ver 3
        with open(output_folder / f'{city_name_l}_osm_roads.pickle', 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)


    # DEFINE FUNCTIONS ##############################
    # def get_centrality_stats():
    #     try:
    #         edges = gpd.read_file(output_folder / f"{city_name_l}_edges.shp")
            
    #         if 'edge_centr' in edges.columns:
    #             df = pd.DataFrame()
    #             df['edge_centr'] = edges.edge_centr.astype(float)
    #             df['edge_centr_avg'] = np.nansum(df.edge_centr.values)/len(df.edge_centr)
    #             df.to_csv(output_folder / f"{city_name_l}_roads_extended_stats.csv")
    #     except FileNotFoundError:
    #         print("Edges file doesn't exist. Running edge_centrality function.")
    #         extended_stats = ox.extended_stats(G, bc = True)
    #         dat = pd.DataFrame.from_dict(extended_stats)
    #         dat.to_csv(output_folder / f"{city_name_l}_roads_extended_stats.csv")
        # except Exception as e:
        #     print('Exception Occurred', e)
    
    def get_centrality(centrality_type = "both"):
        # centrality_type can be either node, edge, or both
        
        # download and project a street network
        
        G1 = nx.DiGraph(G)
        
        if centrality_type == "node" or centrality_type == "both": 
        
            print('Getting node centrality')
            node_centrality = nx.betweenness_centrality(G1)

            nx.set_node_attributes(G1, node_centrality, 'node_centrality')
        
        if centrality_type == "edge" or centrality_type == "both": 
            print('Getting edge centrality')
            # edge closeness centrality: convert graph to a line graph so edges become nodes and vice versa
            edge_centrality = nx.edge_betweenness_centrality(G1)

            new_edge_centrality = {}

            for u, v in edge_centrality:
                new_edge_centrality[(u, v)] = edge_centrality[u, v]
                
            nx.set_edge_attributes(G1, new_edge_centrality, 'edge_centrality')
        
        print('Saving output gdf')
        
        G2 = nx.MultiDiGraph(G1)
        
        if centrality_type == "node":
            ox.save_graph_geopackage(G2, filepath = output_folder / f'{city_name_l}_roads_MultiDiGraph.gpkg')
        elif centrality_type == "edge":
            ox.save_graph_geopackage(G2, filepath = output_folder / f'{city_name_l}_roads_MultiDiGraph.gpkg')
        else:
            ox.save_graph_geopackage(G2, filepath = output_folder / f'{city_name_l}_roads_MultiDiGraph.gpkg')
        
        print('saved multidigraph')
        
        # print('Getting basic stats')
        
        # basic_stats = ox.basic_stats(G2)
        # dat = pd.DataFrame.from_dict(basic_stats)
        # dat.to_csv(output_folder / f'{city_name_l}_roads_basic_stats.csv')
        
        # get_centrality_stats()
        
        return

    def get_network_plots():
        print('get_network_plots')

        fig, ax = ox.plot_graph(G, bgcolor = '#ffffff', node_color = '#336699', node_zorder = 2, node_size = 5)
        
        fig.savefig(output_folder / f'{city_name_l}_network_plot.png', dpi = 300)
        
        return
    
    def plot_radar():
        try:
            if G.graph['crs'].is_projected:
                raise Exception("Graph seems to be projected, bearings will not generated if x and y are not in decimal degrees")
        except:
            print("graph seems to be unprojected, this is ok, continue")
            
        G3 = ox.add_edge_bearings(G)
        
        bearings = pd.Series([data.get('bearing', np.nan) for u, v, k, data in G3.edges(keys = True, data = True)])
        
        # save bearings as csv
        bearings.to_csv(output_folder / f'{city_name_l}_bearings.csv')
        
        fig = plt.figure()  # an empty figure with no axes
        ax = fig.add_subplot(1, 1, 1, projection = 'polar')

        polar_plot(ax, bearings)
        
        # plt.show()
        
        fig.savefig(output_folder / f'{city_name_l}_radar_plot.png', dpi = 300)
        # plt.close() 
        
        return
    
    def count_and_merge(n, bearings):
        # make twice as many bins as desired, then merge them in pairs
        # prevents bin-edge effects around common values like 0° and 90°
        n = n * 2
        bins = np.arange(n + 1) * 360 / n
        count, _ = np.histogram(bearings, bins=bins)
        
        # move the last bin to the front, so that 0° to 5° and 355° to 360° will be binned together
        count = np.roll(count, 1)
        return count[::2] + count[1::2]

    # function to draw a polar histogram for a set of edge bearings
    # This function was adopted from an OSMNX example: https://github.com/gboeing/osmnx-examples/blob/9583920c08558662ef77d99529f13df757015172/notebooks/17-street-network-orientations.ipynb
    def polar_plot(ax, bearings, n = 36, title = ''):
        bins = np.arange(n + 1) * 360 / n

        count = count_and_merge(n, bearings)
        _, division = np.histogram(bearings, bins = bins)
        frequency = count / count.sum()
        division = division[0:-1]
        width = 2 * np.pi / n

        ax.set_theta_zero_location('N')
        ax.set_theta_direction('clockwise')

        x = division * np.pi / 180
        bars = ax.bar(x, height = frequency, width = width, align = 'center', bottom = 0, zorder = 2,
                    color = '#003366', edgecolor = 'k', linewidth = 0.5, alpha = 0.7)
        
        ax.set_ylim(top = frequency.max())
        
        title_font = {'family': 'DejaVu Sans', 'size': 24, 'weight': 'bold'}
        xtick_font = {'family': 'DejaVu Sans', 'size': 10, 'weight': 'bold', 'alpha': 1.0, 'zorder': 3}
        ytick_font = {'family': 'DejaVu Sans', 'size': 9, 'weight': 'bold', 'alpha': 0.2, 'zorder': 3}
        
        ax.set_title(title.upper(), y = 1.05, fontdict = title_font)
        
        ax.set_yticks(np.linspace(0, max(ax.get_ylim()), 5))
        yticklabels = ['{:.2f}'.format(y) for y in ax.get_yticks()]
        yticklabels[0] = ''
        ax.set_yticklabels(labels=yticklabels, fontdict=ytick_font)
        
        xticklabels = ['N', '', 'E', '', 'S', '', 'W', '']
        ax.set_xticks(ax.get_xticks())
        ax.set_xticklabels(labels = xticklabels, fontdict = xtick_font)
        ax.tick_params(axis = 'x', which = 'major', pad = -2)
    
    def main(centrality_type = "both"):
        
        # calculate either 'node' centrality, 'edge' centrality, or 'both'
        get_centrality(centrality_type = centrality_type)
        
        # plot the road network
        get_network_plots()
        
        # generate the road bearing polar plots
        plot_radar()
    

    # RUN MAIN FUNCTION #############################
    main(centrality_type = "edge")