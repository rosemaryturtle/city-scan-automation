import osmnx as ox
import networkx as nx
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import pickle
import utils
import sys
from os.path import exists

# FUNCTIONS ###################################
def get_polygon(aoi_file):
    boundary_poly = aoi_file

    polygons = [i for i in boundary_poly.geometry]
    
    return polygons  # Return the list of polygons

def get_graph(city_name_l, aoi_file, local_output_dir):
    print(f'Fetching graph data for {city_name_l}')
    
    polygons = get_polygon(aoi_file)  # Get a list of polygons
    polygons = [poly.buffer(0) for poly in polygons]  # Apply buffer to each polygon
    
    try:
        with open(f'{local_output_dir}/{city_name_l}', 'rb') as f:
            G = pickle.load(f)  # Load the graph from the pickle file
        print('Graph loaded from pickle file')
        return G  # Return the loaded graph immediately
    except FileNotFoundError:
        print("No pickle file found, retrieving new graph via OSMNX")
        G_list = []
        
        for poly in polygons:
            if poly.geom_type == 'Polygon':  # Single polygon
                print("Processing a polygon...")
                try:
                    G_part = ox.graph_from_polygon(poly, network_type='drive')
                    G_list.append(G_part)
                except ox._errors.InsufficientResponseError:
                    print(f"No roads found in this polygon, skipping...")
                except ValueError as e:
                    print(f"ValueError: {e}, skipping this polygon...")
            elif poly.geom_type == 'MultiPolygon':  # Handle any nested MultiPolygons
                for p in poly.geoms:
                    print("Processing a polygon in multipolygon...")
                    try:
                        G_part = ox.graph_from_polygon(p, network_type='drive')
                        G_list.append(G_part)
                    except ox._errors.InsufficientResponseError:
                        print(f"No roads found in this polygon, skipping...")
                    except ValueError as e:
                        print(f"ValueError: {e}, skipping this polygon...")

        if not G_list:
            print("No graphs created from polygons, skipping graph creation.")
            return None  # If no graphs were created, return None

        # Combine all subgraphs into one graph
        G = nx.compose_all(G_list)
    
        print('Writing graph file')
        with open(f'{local_output_dir}/{city_name_l}', 'wb') as f:
            pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
    
        return G  # Return the newly created graph

def get_centrality_stats(G, city_name_l, aoi_file, local_output_dir):
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
        extended_stats = ox.extended_stats(G, bc = True)
        dat = pd.DataFrame.from_dict(extended_stats)
        dat.to_csv(f'{local_output_dir}/{city_name_l}_road_network_extended_stats.csv')
    except Exception as e:
        print('Exception Occurred', e)

def get_centrality(G, city_name_l, aoi_file, local_output_dir, centrality_type = "edge"):
    # centrality_type can be either node, edge, or both

    if G is not None:
        nnodes = G.number_of_nodes()
        max_nodes = 50000

        # Check if the graph is already directed before converting
        if not G.is_directed():
            G = nx.DiGraph(G)
        
        if centrality_type == "node" or centrality_type == "both": 
            print('Getting node centrality')
            node_centrality = nx.betweenness_centrality(G)
            nx.set_node_attributes(G, node_centrality, 'node_centrality')
        
        if centrality_type == "edge" or centrality_type == "both": 
            print('Getting edge centrality')
            try:
                if nnodes > max_nodes:
                    edge_centrality = nx.edge_betweenness_centrality(G, k=max_nodes)
                else:
                    edge_centrality = nx.edge_betweenness_centrality(G)
            except Exception as e:
                print(f"An error occurred: {e}")
                sys.stdout.flush()  # Flush to ensure the log is captured

            # Set edge attributes
            nx.set_edge_attributes(G, edge_centrality, 'edge_centrality')

            # new_edge_centrality = {}

            # for u,v in edge_centrality:
            #     new_edge_centrality[(u,v)] = edge_centrality[u,v]
                
            # nx.set_edge_attributes(G, new_edge_centrality, 'edge_centrality')
        
        print('Saving output gdf')
        
        # Convert back to MultiDiGraph if needed
        if not isinstance(G, nx.MultiDiGraph):
            G = nx.MultiDiGraph(G)

        graph_gpkg = f'{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg'
        ox.save_graph_geopackage(G, filepath = graph_gpkg)
        
        print('Getting basic stats')
        
        basic_stats = ox.basic_stats(G)
        dat = pd.DataFrame.from_dict(basic_stats)
        dat.to_csv(f'{local_output_dir}/{city_name_l}_road_network_basic_stats.csv')
        
        get_centrality_stats(G, city_name_l, aoi_file, local_output_dir)
        
    return

def get_network_plots(G, city_name_l, aoi_file, local_output_dir):
    if G is not None:
        fig, ax = ox.plot_graph(G, bgcolor = '#ffffff', node_color = '#336699', node_zorder = 2, node_size = 5, show = False)
        fig.savefig(f'{local_output_dir}/{city_name_l}_network_plot.png', dpi = 300)
        
    return

def plot_radar(G, city_name_l, aoi_file, local_output_dir):
    if G is not None:
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

def filter_major_roads(G, local_output_dir, city_name_l):
    if G is not None:
        # Ensure G is a MultiDiGraph
        if not isinstance(G, nx.MultiDiGraph):
            G = nx.MultiDiGraph(G)
        
        graph_gpkg = f'{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg'
        if not exists(graph_gpkg):
            ox.save_graph_geopackage(G, filepath = graph_gpkg)

        roads_gdf = gpd.read_file(f'{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg', layer='edges')

        # Filter for major roads based on keywords in the 'highway' attribute
        major_road_keywords = ['primary', 'trunk', 'motorway', 'primary_link', 'trunk_link', 'motorway_link']

        # Filter for major roads using a lambda function
        major_roads_gdf = roads_gdf[roads_gdf['highway'].apply(lambda highway_value: any(keyword in highway_value for keyword in major_road_keywords))]

        major_roads_gdf.to_file(f'{local_output_dir}/{city_name_l}_major_roads.gpkg', driver='GPKG', layer = 'major_roads')

def road_network(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir, centrality_type = 'edge'):
    print('run road_network')

    # download and project a street network
    G = get_graph(city_name_l, aoi_file, local_output_dir)
    
    # filter for major roads
    filter_major_roads(G, local_output_dir, city_name_l)

    # upload major roads for faster flood calculation
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_major_roads.gpkg", f"{output_dir}/{city_name_l}_major_roads.gpkg")

    # calculate either 'node' centrality, 'edge' centrality, or 'both'
    get_centrality(G, city_name_l, aoi_file, local_output_dir, centrality_type)

    # plot the road network
    get_network_plots(G, city_name_l, aoi_file, local_output_dir)

    # generate the road bearing polar plots
    plot_radar(G, city_name_l, aoi_file, local_output_dir)

    # upload local outputs
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_nodes_and_edges.gpkg", f"{output_dir}/{city_name_l}_nodes_and_edges.gpkg")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_network_extended_stats.csv", f"{output_dir}/{city_name_l}_road_network_extended_stats.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_network_basic_stats.csv", f"{output_dir}/{city_name_l}_road_network_basic_stats.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_network_plot.png", f"{output_dir}/{city_name_l}_network_plot.png")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_bearings.csv", f"{output_dir}/{city_name_l}_road_bearings.csv")
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_road_radar_plot.png", f"{output_dir}/{city_name_l}_road_radar_plot.png")
