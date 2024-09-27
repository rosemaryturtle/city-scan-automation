import osmnx as ox
import networkx as nx
# import nx_parallel as nxp
import pandas as pd
import numpy as np
from shapely.ops import unary_union
import geopandas as gpd
import matplotlib.pyplot as plt
import pickle
import utils
import sys
import gc
import os

# FUNCTIONS ###################################
def get_polygon(aoi_file):
    boundary_poly = aoi_file

    pol = [i for i in boundary_poly.geometry]
    boundary_poly = unary_union(pol)
        
    return boundary_poly

def get_graph(city_name_l, aoi_file, local_output_dir):
    print(f'Fetching graph data for {city_name_l}')
    
    poly = get_polygon(aoi_file)
    poly = poly.buffer(0)
    
    try:
        with open(f'{local_output_dir}/{city_name_l}', 'rb') as f:
            G = pickle.load(f)
    
        val = 1
    except FileNotFoundError:
        print("no pickle file found, retrieving new graph via OSMNX")
        G = ox.graph_from_polygon(poly, network_type = 'drive')
        val = 0
    
    print('Writing graph file')
    
    if val != 1:
        with open(f'{local_output_dir}/{city_name_l}', 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
    
    return G

def get_centrality_stats(city_name_l, aoi_file, local_output_dir):
    try:
        edges = gpd.read_file(f"{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg", layer = 'edges')
        if 'edge_centrality' in edges.columns:
            edges = edges.rename(columns={'edge_centrality': 'edge_centr'})
        
        if 'edge_centr' in edges.columns:
            df = pd.DataFrame()
            df['edge_centr'] = edges.edge_centr.astype(float)
            df['edge_centr_avg'] = np.nansum(df.edge_centr.values)/len(df.edge_centr)
            df.to_csv(f"{local_output_dir}/{city_name_l}_road_network_extended_stats.csv")
    except FileNotFoundError:
        print("Edges file doesn't exist. Running edge_centrality function.")
        # G = get_graph(G)
        G = get_graph(city_name_l, aoi_file, local_output_dir)
        extended_stats = ox.extended_stats(G, bc = True)
        dat = pd.DataFrame.from_dict(extended_stats)
        dat.to_csv(f'{local_output_dir}/{city_name_l}_road_network_extended_stats.csv')
    except Exception as e:
        print('Exception Occurred', e)

def get_centrality(city_name_l, aoi_file, local_output_dir, centrality_type = "edge"):
    # centrality_type can be either node, edge, or both
    
    # download and project a street network
    G = get_graph(city_name_l, aoi_file, local_output_dir)
    nnodes = G.number_of_nodes()
    max_nodes = 50000

    G = nx.DiGraph(G)
    
    if centrality_type == "node" or centrality_type == "both": 
        print('Getting node centrality')
        node_centrality = nx.betweenness_centrality(G)

        nx.set_node_attributes(G, node_centrality, 'node_centrality')
    
    if centrality_type == "edge" or centrality_type == "both": 
        print('Getting edge centrality')
        # edge closeness centrality: convert graph to a line graph so edges become nodes and vice versa
        try:
            if nnodes > max_nodes:
                edge_centrality = nx.edge_betweenness_centrality(G, k=max_nodes)
            else:
                edge_centrality = nx.edge_betweenness_centrality(G)
        except Exception as e:
            print(f"An error occurred: {e}")
            sys.stdout.flush()  # Flush to ensure the log is captured

        new_edge_centrality = {}

        for u,v in edge_centrality:
            new_edge_centrality[(u,v)] = edge_centrality[u,v]
            
        nx.set_edge_attributes(G, new_edge_centrality, 'edge_centrality')
    
    print('Saving output gdf')
    
    G = nx.MultiDiGraph(G)
    graph_gpkg = f'{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg'
    ox.save_graph_geopackage(G, filepath = graph_gpkg)
    # os.makedirs(output_folder_s / f'{city_name_l}_edges', exist_ok=True)
    # os.makedirs(output_folder_s / f'{city_name_l}_nodes', exist_ok=True)
    # gpd.read_file(graph_gpkg, layer = 'edges').to_file(output_folder_s / f'{city_name_l}_edges' / f'{city_name_l}_edges.shp')
    # gpd.read_file(graph_gpkg, layer = 'nodes').to_file(output_folder_s / f'{city_name_l}_nodes' / f'{city_name_l}_nodes.shp')        
    
    print('Getting basic stats')
    
    basic_stats = ox.basic_stats(G)
    dat = pd.DataFrame.from_dict(basic_stats)
    dat.to_csv(f'{local_output_dir}/{city_name_l}_road_network_basic_stats.csv')
    
    get_centrality_stats(city_name_l, aoi_file, local_output_dir)
    
    return

def get_network_plots(city_name_l, aoi_file, local_output_dir):
    G = get_graph(city_name_l, aoi_file, local_output_dir)
    
    fig, ax = ox.plot_graph(G, bgcolor = '#ffffff', node_color = '#336699', node_zorder = 2, node_size = 5, show = False)
    
    fig.savefig(f'{local_output_dir}/{city_name_l}_network_plot.png', dpi = 300)
    
    return 

def plot_radar(city_name_l, aoi_file, local_output_dir):
    G = get_graph(city_name_l, aoi_file, local_output_dir)
    
    try:
        if G.graph['crs'].is_projected:
            raise Exception("Graph seems to be projected, bearings will not generated if x and y are not in decimal degrees")
    except Exception:
        print("graph seems to be unprojected, this is ok, continue")
        
    G = ox.add_edge_bearings(G)
    
    bearings = pd.Series([data.get('bearing', np.nan) for u, v, k, data in G.edges(keys=True, data=True)])
    
    # save bearings as csv
    bearings.to_csv(f'{local_output_dir}/{city_name_l}_road_bearings.csv')
    
    fig = plt.figure()  # an empty figure with no axes
    ax = fig.add_subplot(1, 1, 1, projection='polar')

    polar_plot(ax, bearings)
    
    fig.savefig(f'{local_output_dir}/{city_name_l}_road_radar_plot.png', dpi = 300)
    
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

def polar_plot(ax, bearings, n = 36, title = ''):

    bins = np.arange(n + 1) * 360 / n

    count = count_and_merge(n, bearings)
    _, division = np.histogram(bearings, bins=bins)
    frequency = count / count.sum()
    division = division[0:-1]
    width = 2 * np.pi / n
    
    ax.set_theta_zero_location('N')
    ax.set_theta_direction('clockwise')

    x = division * np.pi / 180
    ax.bar(x, height=frequency, width=width, align='center', bottom=0, zorder=2,
            color='#003366', edgecolor='k', linewidth=0.5, alpha=0.7)

    ax.set_ylim(top=frequency.max())
    
    title_font = {'family':'DejaVu Sans', 'size':24, 'weight':'bold'}
    xtick_font = {'family':'DejaVu Sans', 'size':10, 'weight':'bold', 'alpha':1.0, 'zorder':3}
    ytick_font = {'family':'DejaVu Sans', 'size': 9, 'weight':'bold', 'alpha':0.2, 'zorder':3}
    
    ax.set_title(title.upper(), y=1.05, fontdict=title_font)
    
    ax.set_yticks(np.linspace(0, max(ax.get_ylim()), 5))
    yticklabels = ['{:.2f}'.format(y) for y in ax.get_yticks()]
    yticklabels[0] = ''
    ax.set_yticklabels(labels=yticklabels, fontdict=ytick_font)
    
    xticklabels = ['N', '', 'E', '', 'S', '', 'W', '']
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels(labels=xticklabels, fontdict=xtick_font)
    ax.tick_params(axis='x', which='major', pad=-2)

def road_network(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir, centrality_type = 'edge'):
    print('run road_network')
    # calculate either 'node' centrality, 'edge' centrality, or 'both'
    get_centrality(city_name_l, aoi_file, local_output_dir, centrality_type)

    # plot the road network
    get_network_plots(city_name_l, aoi_file, local_output_dir)

    # generate the road bearing polar plots
    plot_radar(city_name_l, aoi_file, local_output_dir)

    # upload local outputs
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg", f"{output_dir}/{city_name_l}_nodes_and_edges.gpkg")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_network_extended_stats.csv", f"{output_dir}/{city_name_l}_road_network_extended_stats.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_network_basic_stats.csv", f"{output_dir}/{city_name_l}_road_network_basic_stats.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_network_plot.png", f"{output_dir}/{city_name_l}_network_plot.png")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_bearings.csv", f"{output_dir}/{city_name_l}_road_bearings.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_radar_plot.png", f"{output_dir}/{city_name_l}_road_radar_plot.png")

    # free up memory
    if os.path.exists(f'{local_output_dir}/{city_name_l}'):
        os.remove(f'{local_output_dir}/{city_name_l}')
    gc.collect()

# aoi_file = gpd.read_file("C:/Users/Owner/OneDrive/Documents/Career/World Bank/CRP/Africa Flood Risk Workshop/shapefile/Cape_Town.shp").to_crs(epsg = 4326)
# city_name_l = 'cape_town'
# local_output_dir = '.'

# get_centrality(city_name_l, aoi_file, local_output_dir)