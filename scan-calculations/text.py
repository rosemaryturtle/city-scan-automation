# %%
import yaml

# %%
# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

# %%
if menu['all_stats']:
    import os
    import glob
    import math
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    from io import StringIO
    import requests
    from sklearn.preprocessing import MinMaxScaler
    from shapely.geometry import shape
    from shapely.ops import unary_union
    import pint
    import folium
    from pathlib import Path
    import matplotlib.pyplot as plt
    import requests
    import re
    import rasterio
    from rasterio.mask import mask
    from shapely.geometry import Point
    from fiona.crs import from_epsg
    from nbconvert import MarkdownExporter
    import nbformat
    import base64
    import pickle
    import plotly.graph_objects as go
    import osmnx as ox
    from shapely.geometry import box
    from matplotlib.lines import Line2D
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
    import contextily as cx
    import matplotlib.patheffects as pe
    from sklearn.preprocessing import robust_scale
    from sklearn.cluster import AgglomerativeClustering
    from rasterio.plot import show
    import plotly.express as px
    from shapely.geometry import shape
    from scipy.stats import linregress
    from rasterio.warp import reproject, Resampling
    from shapely.ops import transform
    from functools import partial
    import pyproj
    import warnings
    import plotly.offline as pyo
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import re
    import os
    from matplotlib.ticker import FuncFormatter
    from adjustText import adjust_text
    from matplotlib.ticker import ScalarFormatter
    import matplotlib.ticker as ticker
    import squarify
    import shutil
    #from pysal import lib
    #from pysal.explore import esda
    

# %% [markdown]
# ## Text begins

# %%
# SET UP ##############################################


# load global inputs, such as data sources that generally remain the same across scans

with open("../global_inputs.yml", 'r') as f:
    global_inputs = yaml.safe_load(f)
# run scan assembly and toolbox
%run 'scan_assembly.ipynb'
%run 'toolbox.ipynb'

# load city inputs files, to be updated for each city scan
with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
    city_inputs = yaml.safe_load(f)
city = city_inputs['city_name'].replace(' ', '_').lower()
country = city_inputs['country_name'].replace(' ', '_').lower()
print(f"city name: {city}")
print(f"country name:{country}")
aoi_file = gpd.read_file(os.path.join('..', city_inputs['AOI_path'])).to_crs(epsg=4326)
features = aoi_file.geometry
# Define output folder ---------
output_folder = Path('../mnt/city-directories/02-process-output')
render_folder = Path('../mnt/city-directories/03-render-output')
if not os.path.exists(output_folder):
    os.mkdir(output_folder)



# %% [markdown]
# ## City Subdistricts available?

# %%
#Intersect subdistricts to AOI - Is this necessary? We need ward level files
clip_extent = features.geometry.total_bounds
clip_box = box(*clip_extent)
lowest_admin_file = gpd.read_file(os.path.join('..', city_inputs['lowest_admin_shp'])).to_crs(epsg=4326)
lowest_admin_country = lowest_admin_file.geometry
lower_admin_level = lowest_admin_country.cx[clip_box.bounds[0]:clip_box.bounds[2], clip_box.bounds[1]:clip_box.bounds[3]]
#plot check
fig, ax = plt.subplots()
lower_admin_level.plot(ax=ax)
plt.title('Subdistricts')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.show()

print(f"city subdistricts are larger than {city}: Not available")

# %%
#Standard Units
def enumerate_items(source):
    print("/n")
    for ele in enumerate(source): 
        print(ele)

def list_df_columns(df):
    field_list = list(df)
    enumerate_items(field_list)
    return field_list

def percentage_formatter(x, pos):
    return f'{x * 100 :,.0f}'

def millions_formatter(x, pos):
    return f'{x / 1000000 :,.0f}'


def hundred_thousand_formatter(x, pos):
    return f'{x / 100000 :,.0f}'

def billions_formatter(x, pos):
    return f'{x / 1000000000 :,.0f}'


# %% [markdown]
# ## Lowest admin level available?

# %%
def get_lowest_admin_level():
    try:
        vector = features.reset_index()

        crs = 4326

        tags = {"boundary": "administrative"}

        minx, miny, maxx, maxy = vector.to_crs(epsg=4326).total_bounds

        all_admin_layers = ox.geometries.geometries_from_bbox(miny, maxy, minx, maxx, tags)

        lowest_admin_level = all_admin_layers["admin_level"].mode()[0]
        warnings.filterwarnings("ignore", message="Geometry is in a geographic CRS")

        vector_gdf = all_admin_layers[all_admin_layers['admin_level'] == lowest_admin_level]

        lowest_admin_level_name = "Settlement"

        sub_city_gdf = gpd.clip(vector_gdf.to_crs(crs), vector.to_crs(crs))

        vector_gdf.loc[:, "pre_clip_area"] = vector_gdf['geometry'].area

        sub_city_gdf.loc[:, "post_clip_area"] = sub_city_gdf['geometry'].area

        sub_city_gdf.loc[:, "pct_clip_area"] = (sub_city_gdf["post_clip_area"] / sub_city_gdf["pre_clip_area"]) * 100

        sub_city_gdf = sub_city_gdf[sub_city_gdf['pct_clip_area'] > 50]

        sub_city_gdf['name:en'] = sub_city_gdf['name:en'].str.strip().replace('', np.nan).fillna(sub_city_gdf['name'])
  
        sub_city_gdf = sub_city_gdf.to_crs(crs)

        ax = sub_city_gdf.plot(alpha=0.8,
                               facecolor='none',
                               edgecolor='black',
                               label=f"{city}",
                               missing_kwds={"color": "white", "edgecolor": "black", "label": "none"},
                               zorder=5)
        

        plt.show()
        
        print("Yes, it is available")
    except Exception as e:
        print("Not available")
        print(e)
    warnings.filterwarnings("ignore")
    
get_lowest_admin_level() 

      

# %% [markdown]
# ## Area of the city

# %%
area = calculate_aoi_area(features)
print(f"Area of the city of {city} is {area:2f} sq.km")

# %% [markdown]
# ## Koppen Climate

# %%
get_koeppen_classification()

# %% [markdown]
# ## Population in Oxford economics

# %%
city= city_inputs['city_name']
country= city_inputs['country_name']
in_oxford, oxford_full = check_city_in_oxford(city, country)

# %% [markdown]
# ## Population from citypopulation.de

# %%
csv_path=os.path.join(render_folder, 'pop.csv')
pop_growth = get_de_pop_growth(city, country)

if pop_growth is not None:
    pop_growth.to_csv(csv_path, index=False)
else:
    print(f"{city} population data could not be retrieved from CityPopulation.de. Try manual entry instead.")
get_de_pop_growth(city, country)

# %% [markdown]
# ### City Population Growth

# %%
main()

# %%
def calculate_growth(pop_growth):
    pop_1 = pop_growth.iloc[0]['Population']
    pop_last = pop_growth.iloc[-1]['Population']
    year_1 = pop_growth.iloc[0]['Year']
    year_last = pop_growth.iloc[-1]['Year']
    pct_growth = round(((pop_last - pop_1) / pop_1), 3)
    if year_last - year_1 > 0:
        avg_growth = ((1 + pct_growth) ** (1 / (year_last - year_1))) - 1
    else:
        avg_growth = 0  

    growth_message = (
        f"{city}'s population increased by {pct_growth:.1%} from "
        f"{pop_1:,} in {year_1} to {pop_last:,} in {year_last}, "
        f"at an average annual growth rate of {avg_growth:.1%} according to CityPopulaton.de"
    )
    
    return growth_message

try:
    growth_message = calculate_growth(pop_growth)
    print(growth_message)
except Exception as e:
    print(f"An error occurred while calculating growth text: {str(e)}, try manual method instead")

# %% [markdown]
# ## Benchmark cities 

# %%
city= city_inputs['city_name']
country= city_inputs['country_name']
bm_cities = find_benchmark_cities(city, country)
print(bm_cities)


# %%

countries = oxford_full['Country'].unique()

oxford_countries = oxford_full[oxford_full['Country'].isin(countries)]
oxford_countries = oxford_countries[(oxford_countries['Location'].str.contains("- Total")) | (oxford_countries['Country'].isin(countries))]

oxford_countries = oxford_countries.drop(columns=['Location'])

oxford_countries.head()

indicators = oxford_full[['Indicator']].drop_duplicates()

pop_dist_inds = indicators['Indicator'][(indicators['Indicator'].str.contains("Population")) & 
                                        (~indicators['Indicator'].isin(["Population 0-14", "Population 15-64", "Population 65+"]))].tolist()

emp_inds = indicators['Indicator'][indicators['Indicator'].str.contains("Employment")].tolist()

gva_inds = indicators['Indicator'][indicators['Indicator'].str.lower().str.contains("gross value added, real, us")].tolist()

extra_inds = ["Total population", "Employment - Total", "GDP, real, US$ - Total"]

# %% [markdown]
# ## Bechmark cities Manual

# %%
bm_cities_manual = city_inputs['bm_cities_manual']
combined_bm_cities = list(np.unique(bm_cities + bm_cities_manual))
bm_cities = [c for c in combined_bm_cities if c != city]
print(bm_cities)

# %%

oxford_pop_path = os.path.join(render_folder, 'oxford_pop.csv')
benchmark_pop_path = os.path.join(render_folder, 'pop_oxford_benchmark.csv')

oxford_full = pd.read_csv(global_inputs['oxford_global_source'])
oxford_locations = pd.read_csv(global_inputs['oxford_locations_source'])


filtered_oxford = oxford_full[oxford_full['Location'].isin([city] + bm_cities)]

if len(filtered_oxford) > 0:

    pop_oxford = filtered_oxford[
        filtered_oxford['Indicator'] == 'Total population'
    ].copy()

    pop_oxford['Group'] = np.where(pop_oxford['Location'] == city, city, 'Benchmark')
    pop_oxford['Group'] = pd.Categorical(pop_oxford['Group'], categories=[city, 'Benchmark'], ordered=True)


    pop_oxford = pop_oxford.melt(
        id_vars=['Group', 'Location', 'Country'],
        value_vars=[col for col in pop_oxford.columns if col.isdigit()],
        var_name='Year',
        value_name='Total population'
    ).pivot_table(
        values='Total population',
        index=['Group', 'Location', 'Country', 'Year'],
        aggfunc=np.sum
    ).reset_index()


    pop_oxford['Year'] = pop_oxford['Year'].astype(int)
    pop_oxford['Population'] = pop_oxford['Total population'] * 1000
    pop_oxford['Source'] = 'Oxford'
    pop_oxford['Method'] = 'Oxford'
    pop_oxford = pop_oxford[['Group', 'Location', 'Country', 'Year', 'Population', 'Source', 'Method']]
    pop_oxford = pop_oxford[pop_oxford['Year'] <= 2021].dropna(subset=['Population']).sort_values(by='Group')

    bm_areas = pd.read_csv(global_inputs['oxford_areas_source'])
    bm_areas['Location'] = bm_areas['Location'].str.title()

    if bm_areas.duplicated(subset=['Location']).any():
        raise ValueError("Multiple Oxford Economics cities have been matched with the same name")

    pop_oxford = pop_oxford.merge(bm_areas, on='Location', how='left')
else:
    pop_oxford = pd.DataFrame({
        'Group': pd.Categorical([], categories=[city, 'Benchmark'], ordered=True),
        'Location': pd.Series(dtype='str'),
        'Country': pd.Series(dtype='str'),
        'Year': pd.Series(dtype='int'),
        'Population': pd.Series(dtype='float'),
        'Source': pd.Series(dtype='str'),
        'Method': pd.Series(dtype='str')
    })

pop_oxford.to_csv(oxford_pop_path, index=False)

benchmark_2021 = pop_oxford[(pop_oxford['Group'] == 'Benchmark') & (pop_oxford['Year'] == 2021)]

benchmark_2021.to_csv(benchmark_pop_path, index=False)





# %% [markdown]
# ## Population Density Manual

# %%
city = "Guìyáng"
def plot_population_density(pop_manual_path):
    pop_manual = pd.read_csv(pop_manual_path)

    density = pop_manual.loc[pop_manual.groupby('Location')['Year'].idxmax()]

    
    density['Population'] = pd.to_numeric(density['Population'], errors='coerce')
    density['Area_km'] = pd.to_numeric(density['Area_km'], errors='coerce')

    
    density['Density'] = density['Population'] / density['Area_km']
    density = density.dropna(subset=['Population', 'Density'])
    density = density.sort_values(by='Density', ascending=False)

    
    if city in density['Location'].values:
        city_pop_density = density.loc[density['Location'] == city, 'Density'].values[0]
    else:
        raise ValueError(f"City '{city}' not found in the dataset.")

    
    hues = {'Benchmark': 'darkgrey', city: '#000000'}

    
    plt.figure(figsize=(8.5, 6), dpi=300)
    sns.scatterplot(data=density, x='Population', y='Density', hue='Group', palette=hues, legend=False)

    texts = []
    for i, row in density.iterrows():
        texts.append(plt.text(row['Population'], row['Density'], row['Location'], fontsize=9))

    
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', lw=0.5),
                expand_text=(2, 1.05),  
                only_move={'points': 'xy', 'texts': 'xy'},  
                lim=1000)

    plt.ylim(0, None)
    plt.title(f'Population density of {city} and benchmark cities')
    plt.xlabel('Population')
    plt.ylabel('Population density, people per km²')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    
    plt.savefig(Path(render_folder) / f"{city.lower().replace(' ', '_')}-pop-density.png", dpi=300,bbox_inches='tight')
    plt.show()

    # Plotly 
    fig = px.scatter(density, x='Population', y='Density', color='Group', 
                     color_discrete_map=hues,
                     labels={'Population': 'Population', 'Density': 'Population density, people per km²'},
                     log_x=False, log_y=False,
                     hover_name="Location")
    fig.update_layout(
    autosize=True,
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=-0.2,
        xanchor="center",
        x=0.5
    ),
        yaxis=dict(
        range=[0, None]  
    )
    )

    fig.write_html(Path(render_folder) / f"{city.lower().replace(' ', '_')}-pop-density-plotly.html",full_html=False, include_plotlyjs='cdn')
    fig.show()
plot_population_density("../mnt/city-directories/01-user-input/pop_manual.csv")

# %%
city = city_inputs['city_name']
country = city_inputs['country_name']
try:
    oxford_full = pd.read_csv(global_inputs['oxford_global_source'])
    if city in oxford_full['Location'].values:
        create_national_shares_plot()
    else:
        print("City is not in oxford economics")
except Exception as e:
    print(f"An error occurred: {e}")

# %%
try:
    oxford_full = pd.read_csv(global_inputs['oxford_global_source'])
    if city in oxford_full['Location'].values:
        oxford_pop_growth_plot()
    else:
        print("City is not in oxford economics")
except Exception as e:
    print(f"An error occurred: {e}")


# %%
if city in oxford_full['Location'].values:
        oxford_emp_growth_plot()
else:
        print("City is not in oxford economics")

# %%
if city in oxford_full['Location'].values:
        oxford_gdp_growth_plot()
else:
        print("City is not in oxford economics")



# %%
if city in oxford_full['Location'].values:
        oxford_emp_gva_shares_plot()
else:
        print("City is not in oxford economics")


# %%
if city in oxford_full['Location'].values:
        oxford_gva_inequality_plot()
else:
        print("City is not in oxford economics")

# %% [markdown]
# ## Population distribution by age and sex

# %%
city = city_inputs['city_name'].replace(' ', '_').lower()
country = city_inputs['country_name'].replace(' ', '_').lower()
age_stats()

# %%
#Text option 1 - Delta and Range

def find_highest_lowest_pixel_value_path(raster_path):
    try:
        with rasterio.open(raster_path) as src:
            raster_data = src.read(1)
            highest_value = round(raster_data.max(), 2)
            lowest_value = round(raster_data[raster_data > 0].min(), 2) 
            print(f"Values range from {lowest_value:.2f} units to {highest_value:.2f} units")

            return highest_value, lowest_value
        
    except Exception as e:
        print("Error:", e)
        return None, None

# %%
#Text option 1 - Delta and Range
def find_highest_lowest_pixel_value(raster_data):
    try:
        valid_values = raster_data[~np.isnan(raster_data)].flatten()
        highest_value = round(np.nanmax(valid_values), 2)
        lowest_value = round(np.nanmin(valid_values), 2)
        print(f"Values range from {lowest_value:.2f} units to {highest_value:.2f} units")

        return highest_value, lowest_value
    
    except Exception as e:
        print("Error:", e)
        return None, None



# %%
def find_highest_lowest_pixel_value_path(raster_path):
    try:
        with rasterio.open(raster_path) as src:
            raster_data = src.read(1) 
        valid_values = raster_data[~np.isnan(raster_data)].flatten()
        highest_value = round(np.nanmax(valid_values), 2)
        lowest_value = round(np.nanmin(valid_values), 2)
        print(f"Values range from {lowest_value:.2f} units to {highest_value:.2f} units")

        return highest_value, lowest_value
    
    except Exception as e:
        print("Error:", e)
        return None, None

# %%
# def create_raster_clusters(raster_data, n_clusters=5):
#     try:
#         # Open the raster file
#         with rasterio.open(raster_path) as src:
#             raster_data = src.read(1)
#             transform = src.transform
#             meta = src.meta
        
#         # Load the shapefile
#         features = aoi_file.geometry
        
#         # Ensure the shapefile is in the same CRS as the raster
#         if features.crs != meta['crs']:
#             features = features.to_crs(meta['crs'])
        
#         # Convert shapefile geometries to mask
#         geometries = [shape(geom) for geom in features.geometry]
#         mask = geometry_mask(geometries, transform=transform, invert=True, out_shape=raster_data.shape)

#         # Apply the mask to the raster data
#         masked_raster_data = np.where(mask, raster_data, np.nan)

#         # Flatten and prepare data for clustering
#         flat_data = masked_raster_data.flatten()
#         valid_data = flat_data[~np.isnan(flat_data)]  # Remove NaNs

#         if valid_data.size == 0:
#             raise ValueError("No valid data available for clustering.")
        
#         # Prepare data for clustering
#         flat_data_reshaped = valid_data.reshape(-1, 1)

#         # Perform clustering
#         clustering = AgglomerativeClustering(n_clusters=n_clusters).fit(flat_data_reshaped)
#         cluster_labels = np.full(raster_data.shape, fill_value=-1, dtype=int)
#         cluster_labels[~np.isnan(masked_raster_data)] = clustering.labels_

#         return cluster_labels

#     except Exception as e:
#         print("Error:", e)
#         return None

# def plot_cluster_labels_plotly(cluster_labels):
#     if cluster_labels is not None:
#         fig = px.imshow(cluster_labels, color_continuous_scale='viridis')
#         fig.update_layout(
#             xaxis_title='Column Index',
#             yaxis_title='Row Index',
#             legend_title='Cluster'
#         )
#         fig.show()
#     else:
#         print("No cluster labels to plot.")

# # Example usage
# raster_path = os.path.join(output_folder, f"{city}_population.tif")
# cluster_labels = create_raster_clusters(raster_path)
# if cluster_labels is not None:
#     plot_cluster_labels_plotly(cluster_labels)


# %%
# def create_raster_clusters(raster_path, n_clusters=5):
#     try:
#         # Open the raster file
#         with rasterio.open(raster_path) as src:
#             raster_data = src.read(1)
#             transform = src.transform
#             meta = src.meta
        
#         # Load the shapefile
#         features = aoi_file.geometry
        
#         # Ensure the shapefile is in the same CRS as the raster
#         if features.crs != meta['crs']:
#             features = features.to_crs(meta['crs'])
        
#         # Convert shapefile geometries to mask
#         geometries = [shape(geom) for geom in features.geometry]
#         mask = geometry_mask(geometries, transform=transform, invert=True, out_shape=raster_data.shape)

#         # Apply the mask to the raster data
#         masked_raster_data = np.where(mask, raster_data, np.nan)

#         # Flatten and prepare data for clustering
#         flat_data = masked_raster_data.flatten()
#         valid_data = flat_data[~np.isnan(flat_data)]  # Remove NaNs

#         if valid_data.size == 0:
#             raise ValueError("No valid data available for clustering.")
        
#         # Prepare data for clustering
#         flat_data_reshaped = valid_data.reshape(-1, 1)

#         # Perform clustering
#         clustering = AgglomerativeClustering(n_clusters=n_clusters).fit(flat_data_reshaped)
#         cluster_labels = np.full(raster_data.shape, fill_value=-1, dtype=int)
#         cluster_labels[~np.isnan(masked_raster_data)] = clustering.labels_

#         return cluster_labels

#     except Exception as e:
#         print("Error:", e)
#         return None

# def plot_cluster_labels_plotly(cluster_labels):
#     if cluster_labels is not None:
#         fig = px.imshow(cluster_labels, color_continuous_scale='viridis')
#         fig.update_layout(
#             xaxis_title='Column Index',
#             yaxis_title='Row Index',
#             legend_title='Cluster'
#         )
#         fig.show()
#     else:
#         print("No cluster labels to plot.")

# # Example usage
# raster_path = os.path.join(output_folder, f"{city}_population.tif")
# cluster_labels = create_raster_clusters(raster_path)
# if cluster_labels is not None:
#     plot_cluster_labels_plotly(cluster_labels)

# %%
# def get_raster_cluster_labels(raster_path,n_clusters=5):
#     try:
#         # Open the raster file
#         with rasterio.open(raster_path) as src:
#             raster_data = src.read(1)
#             transform = src.transform
#             meta = src.meta

#         # Load the shapefile
#         features = aoi_file.geometry
        
#         # Ensure the shapefile is in the same CRS as the raster
#         if features.crs != meta['crs']:
#             features = features.to_crs(meta['crs'])
        
#         # Convert shapefile geometries to mask
#         geometries = [shape(geom) for geom in features.geometry]
#         mask = geometry_mask(geometries, transform=transform, invert=True, out_shape=raster_data.shape)

#         # Apply the mask to the raster data
#         masked_raster_data = np.where(mask, raster_data, np.nan)

#         # Flatten the masked raster data
#         flat_data = masked_raster_data.flatten()
#         valid_data = flat_data[~np.isnan(flat_data)]  # Remove NaNs

#         if valid_data.size == 0:
#             raise ValueError("No valid data available for clustering.")
        
#         # Prepare data for clustering
#         flat_data_reshaped = valid_data.reshape(-1, 1)

#         # Perform agglomerative clustering
#         clustering = AgglomerativeClustering(n_clusters=n_clusters).fit(flat_data_reshaped)
#         cluster_labels = np.full(raster_data.shape, fill_value=-1, dtype=int)
#         cluster_labels[~np.isnan(masked_raster_data)] = clustering.labels_

#         return cluster_labels, transform

#     except Exception as e:
#         print("Error:", e)
#         return None, None

# # Example usage
# raster_path = os.path.join(output_folder, f"{city}_population.tif")
# cluster_labels, transform = get_raster_cluster_labels(raster_path)
# if cluster_labels is not None:
#     plot_cluster_labels_plotly(cluster_labels)

# %%
# from rasterio.crs import CRS

# # Define the Affine transformation matrix
# affine_transform = transform

# # Define the EPSG code for the CRS
# epsg_code = 4326 

# # Create a CRS object
# crs = CRS.from_epsg(epsg_code)

# %%
# def get_cluster_boundaries(cluster_labels, transform):
#     # Get unique cluster labels
#     unique_labels = np.unique(cluster_labels)

#     # Initialize a list to store cluster boundary polygons
#     cluster_polygons = []

#     # Iterate over each unique cluster label
#     for label in unique_labels:
#         # Create a mask for pixels with the current label
#         mask = cluster_labels == label

#         # Get the indices of non-zero elements in the mask
#         nonzero_indices = np.argwhere(mask)

#         # Calculate the bounding box of the cluster
#         min_row, min_col = np.min(nonzero_indices, axis=0)
#         max_row, max_col = np.max(nonzero_indices, axis=0)

#         # Calculate the bounding box coordinates
#         minx, miny = transform * (min_col, min_row)
#         maxx, maxy = transform * (max_col, max_row)

#         # Create the bounding box polygon
#         geom = box(minx, miny, maxx, maxy)

#         # Transform the polygon to the desired CRS
#         geom = gpd.GeoSeries(geom, crs=crs).to_crs(crs)

#         # Add the polygon to the list
#         cluster_polygons.append(geom[0])  # Take the first element

#     # Combine all polygons into a GeoDataFrame
#     cluster_gdf = gpd.GeoDataFrame({'cluster_label': unique_labels}, geometry=cluster_polygons, crs=crs)

#     return cluster_gdf

# cluster_gdf = get_cluster_boundaries(cluster_labels, transform)

# %%
# def describe_cluster_location(cluster_gdf, aoi_file):
#     # Get the centroid of the city
#     city_centroid = shape(aoi_file.geometry.centroid.iloc[0])
        
#     # Get the centroid of the cluster with the highest value
#     highest_cluster = cluster_gdf[cluster_gdf['cluster_label'] == cluster_gdf['cluster_label'].max()]['geometry'].centroid.values[0]
#     # Get the centroid of the cluster with the lowest value
#     lowest_cluster = cluster_gdf[cluster_gdf['cluster_label'] == cluster_gdf['cluster_label'].min()]['geometry'].centroid.values[0]
    
#     # Determine the location of the clusters
#     highest_location = "north" if highest_cluster.y > city_centroid.y else "south"
#     lowest_location = "north" if lowest_cluster.y > city_centroid.y else "south"
    
#     if highest_cluster.x > city_centroid.x:
#         highest_location += " east"
#     elif highest_cluster.x < city_centroid.x:
#         highest_location += " west"
        
#     if lowest_cluster.x > city_centroid.x:
#         lowest_location += " east"
#     elif lowest_cluster.x < city_centroid.x:
#         lowest_location += " west"
        
#     # Check if the centroids are within a range of the city centroid 
#     center_range = 0.2  
#     center_clusters = cluster_gdf[cluster_gdf['geometry'].apply(lambda geom: abs(geom.centroid.x - city_centroid.x) < center_range and abs(geom.centroid.y - city_centroid.y) < center_range)]
    
#     if len(center_clusters) > 0:
#         if cluster_gdf['cluster_label'].max() == center_clusters['cluster_label'].max():
#             highest_location = "center"
#         else:
#             center_location = "center"
    
#     # Print statements describing cluster locations
#     print(f"The cluster with the highest value is located in the {highest_location} of the city.")
#     print(f"The cluster with the lowest value is located in the {lowest_location} of the city.")





# %%
# #Text option 4 - OLS
# #Bit tricky but might be fun
# if menu['summer_lst']:  
#     summer_path = os.path.join(output_folder, city + '_summer.tif')
#     with rasterio.open(summer_path) as src:
#         summer_data = src.read(1)
#         summer_data = np.nan_to_num(summer_data, nan=0) 
#         transform = src.transform
# def pixelwise_regression(pop_path, summer_path):
#     try:
#         # Open population raster
#         with rasterio.open(pop_path) as pop_src:
#             pop_data = pop_src.read(1)
#             pop_profile = pop_src.profile

#         # Open summer LST raster and reproject to match population raster
#         with rasterio.open(summer_path) as summer_src:
#             summer_data = summer_src.read(1)
#             summer_profile = summer_src.profile

#             # Reproject summer LST raster to match population raster
#             pop_data_resampled = np.zeros_like(summer_data)
#             reproject(
#                 source=pop_data,
#                 destination=pop_data_resampled,
#                 src_transform=pop_src.transform,
#                 src_crs=pop_src.crs,
#                 dst_transform=summer_src.transform,
#                 dst_crs=summer_src.crs,
#                 resampling=Resampling.bilinear
#             )

#         # Flatten the arrays
#         summer_flat = summer_data.flatten()
#         pop_flat = pop_data_resampled.flatten()

#         # Perform pixel-wise linear regression
#         slope, intercept, r_value, p_value, std_err = linregress(pop_flat, summer_flat)

#         # Check if p-value is significant
#         if np.isnan(p_value):
#             print("Regression is not significant. Results may not be reliable.")

#         return slope, intercept, r_value, p_value, std_err

#     except Exception as e:
#         print("Error:", e)
#         return None, None, None, None, None
        



# %% [markdown]
# ## Population Density

# %%
# #Iterate
if menu['population']:  
     pop_path = os.path.join(output_folder, f"{city}_population.tif")
     with rasterio.open(pop_path) as src:
         pop_data = src.read(1)
         pop_data[pop_data == -9999] = np.nan
         pop_data = np.nan_to_num(pop_data, nan=0)
         transform = src.transform  

#     create_raster_clusters(pop_data, n_clusters=5)
#     plot_cluster_labels_plotly(cluster_labels)
#     if cluster_labels is not None:
#         print("Cluster labels shape:", cluster_labels.shape)
#         pop_cluster_gdf = get_cluster_boundaries(cluster_labels, transform)
#         pop_cluster = describe_cluster_location(pop_cluster_gdf, aoi_file)
#         pop_cluster
#    find_highest_lowest_pixel_value_path(pop_path)
#     pixelwise_regression(pop_path, summer_path)

# %% [markdown]
# ## Economic Activity

# %%
if menu['raster_processing']:  
     raster_path = os.path.join(output_folder, f"{city}_avg_rad_sum.tif")
     with rasterio.open(raster_path) as src:
         rad_data = src.read(1)
         rad_data[rad_data == -9999] = np.nan
         rad_data = np.nan_to_num(rad_data, nan=0) 
        
         transform = src.transform
#     rad_cluster_labels = create_raster_clusters(rad_data, n_clusters=5)
#     plot_cluster_labels_plotly(rad_cluster_labels)
#     if cluster_labels is not None:
#         print("Cluster labels shape:", rad_cluster_labels.shape)
#         rad_cluster_gdf = get_cluster_boundaries(rad_cluster_labels, transform)
#         rad_cluster = describe_cluster_location(rad_cluster_gdf, aoi_file)
#         rad_cluster
     find_highest_lowest_pixel_value(rad_data)

# %% [markdown]
# ## Change in Economic Activity 

# %%
# if menu['raster_processing']:  
#     raster_path = os.path.join(output_folder, city + '_linfit.tif')
#     with rasterio.open(raster_path) as src:
#         linfit_data = src.read(1)
#         linfit_data[linfit_data == -9999] = np.nan
#         linfit_data = np.nan_to_num(linfit_data, nan=0) 
#         transform = src.transform
#     linfit_cluster_labels = create_raster_clusters(linfit_data, n_clusters=5)
#     plot_cluster_labels_plotly(linfit_cluster_labels)
#     if cluster_labels is not None:
#         print("Cluster labels shape:", linfit_cluster_labels.shape)
#         linfit_cluster_gdf = get_cluster_boundaries(linfit_cluster_labels, transform)
#         linfit_cluster = describe_cluster_location(linfit_cluster_gdf, aoi_file)
#         linfit_cluster
#     find_highest_lowest_pixel_value(linfit_data)

# %% [markdown]
# ## Urban Extent and Change

# %%
wsf_stats()

# %% [markdown]
# ## Land Cover

# %%
lc_stats()

# %% [markdown]
# ## Photovoltaic Power Potential

# %%
extract_monthly_stats()

# %% [markdown]
# ## Land Surface Temperature

# %%

if menu['summer_lst']:  
    raster_path = os.path.join(output_folder, city + '_summer.tif')
    with rasterio.open(raster_path) as src:
        summer_data = src.read(1)
        summer_data[summer_data == -9999] = np.nan
        summer_data = np.nan_to_num(summer_data, nan=0) 
        nonzero_values = summer_data[(summer_data != 0) & (~np.isnan(summer_data))]

    if len(nonzero_values) > 0:
        lowest_value = np.min(nonzero_values)
        min_value = np.min(nonzero_values)
        max_value = np.max(nonzero_values)
        print(f"Values range from {min_value:.2f} to {max_value:.2f}")
    else:
        print("There are no non-zero values in the summer data.")


# %% [markdown]
# ## Green Spaces

# %%
if menu['green']:  
    NDVI_path = os.path.join(output_folder, city + '_NDVI_Annual.tif')
    with rasterio.open(NDVI_path) as src:
        NDVI_data = src.read(1)
        NDVI_data = np.nan_to_num(NDVI_data, nan=0) 
    find_highest_lowest_pixel_value(NDVI_data)

# %% [markdown]
# ## Elevation

# %%
elev_stats()

# %% [markdown]
# ## Slope

# %%
if menu['slope']:  
    slope_path = os.path.join(output_folder, city + '_slope.tif')
    with rasterio.open(slope_path) as src:
        slope_data = src.read(1)
        slope_data[slope_data == -9999] = np.nan
        slope_data = np.nan_to_num(slope_data, nan=0) 
        transform = src.transform
    #slope_cluster_labels = create_raster_clusters(slope_data, n_clusters=5)
    #plot_cluster_labels_plotly(slope_cluster_labels)
    #if cluster_labels is not None:
        #print("Cluster labels shape:", slope_cluster_labels.shape)
        #slope_cluster_gdf = get_cluster_boundaries(slope_cluster_labels, transform)
        #slope_cluster = describe_cluster_location(slope_cluster_gdf, aoi_file)
        #slope_cluster
    find_highest_lowest_pixel_value(slope_data)

# %%
slope_stats()

# %% [markdown]
# ## NDMI

# %%
if menu['ndmi']:  
    NDMI_path = os.path.join(output_folder, city + '_NDMI_Annual.tif')
    with rasterio.open(NDMI_path) as src:
        NDMI_data = src.read(1)
        NDMI_data = np.nan_to_num(NDMI_data, nan=0) 
    find_highest_lowest_pixel_value(NDMI_data)

# %% [markdown]
# ## Flooding 

# %%
flood_timeline()

# %% [markdown]
# ### Pluvial and OSM

# %%
get_pu_am()
#get_pu_roads()

# %% [markdown]
# ### Pluvial Flooding and WSF

# %%
stats_by_year = get_pu_wsf()
if stats_by_year is not None:
    years = list(stats_by_year.keys())
    areas = list(stats_by_year.values())

    cumulative_areas = np.cumsum(areas)

    cumulative_stats_by_year = dict(zip(years, cumulative_areas))

    years_to_plot = sorted(years)  
    areas_to_plot = [cumulative_stats_by_year.get(year, np.nan) for year in years_to_plot]

    plt.figure(figsize=(8, 8))
    plt.plot(years_to_plot, areas_to_plot, marker='o', linestyle='-')
    plt.title('Areas exposed to surface water flooding')
    plt.xlabel('Year')
    plt.ylabel('Exposed area in sq.km')
    plt.grid(True)
    plt.tight_layout()
    render_path = os.path.join(render_folder, f"{city}_pu_wsf.png")
    plt.savefig(render_path)
    plt.close()
    print(f"PNG saved to {render_path}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_to_plot, y=areas_to_plot, mode='lines+markers', name='Cumulative Flooded Area'))
    fig.update_layout(xaxis_title='Year',
                      yaxis_title='Exposed area (sq.km)',
                      yaxis=dict(range=[0, max(areas_to_plot) * 1.1]))
    fig.show()
    fig.write_html(render_path.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')

wsf_stats_file = Path(output_folder / f"{city}_wsf_stats.csv")  
wsf = pd.read_csv(wsf_stats_file)
total_built_up_area = wsf['cumulative sq km'].iloc[-1]

if 2015 in stats_by_year:
    flooded_area_2015 = np.cumsum([stats_by_year[year] for year in years if year <= 2015])[-1]
    if total_built_up_area != 0:
        percentage_2015 = (flooded_area_2015 / total_built_up_area)*100
        print(f"As of 2015, {flooded_area_2015:.2f} sq.km of the city’s built-up area ({percentage_2015:.2f}%) was exposed to surface water flooding.")
    else:
        print("The city is not exposed to surface water flooding.")
else:
    print("No flooding data available for 2015.")



# %% [markdown]
# ### Pluvial and Population

# %%
get_pu_pop_norm()

# %% [markdown]
# ### Fluvial and OSM

# %%
get_fu_am()
#get_fu_roads()

# %% [markdown]
# ### Fluvial and WSF

# %%
stats_by_year = get_fu_wsf()
if stats_by_year is not None:
    years = list(stats_by_year.keys())
    areas = list(stats_by_year.values())

    cumulative_areas = np.cumsum(areas)

    cumulative_stats_by_year = dict(zip(years, cumulative_areas))

    years_to_plot = sorted(years)
    areas_to_plot = [cumulative_stats_by_year.get(year, np.nan) for year in years_to_plot]

    plt.figure(figsize=(8, 8))
    plt.plot(years_to_plot, areas_to_plot, marker='o', linestyle='-')
    plt.title('Area exposed to River Flooding')
    plt.xlabel('Year')
    plt.ylabel('Exposed area in sq.km')
    plt.grid(True)
    plt.tight_layout()
    render_path = os.path.join(render_folder, f"{city}_fu_wsf.png")
    plt.savefig(render_path)
    plt.close()
    print(f"PNG saved to {render_path}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_to_plot, y=areas_to_plot, mode='lines+markers', name='Area exposed to River Flooding'))
    fig.update_layout(xaxis_title='Year',
                      yaxis_title='Exposed area in sq.km',
                      yaxis=dict(range=[0, max(areas_to_plot) * 1.1]))
    fig.show()
    fig.write_html(render_path.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')

    wsf_stats_file = Path(output_folder / f"{city}_wsf_stats.csv")  
    wsf = pd.read_csv(wsf_stats_file)
    total_built_up_area_2015 = wsf['cumulative sq km'].iloc[-1]
    total_built_up_area_1985 = wsf['cumulative sq km'].iloc[0]
    flooded_area_2015 = np.cumsum([stats_by_year[year] for year in years if year <= 2015])[-1]
    if total_built_up_area != 0:
        percentage_2015 = (flooded_area_2015 / total_built_up_area_2015) * 100
        print(f"In 2015, {flooded_area_2015:.2f} sq.m of the city’s cumulative built-up area ({percentage_2015:.2f}%) was exposed to fluvial flooding.")
    else:
        print("The city is not exposed to fluvial flooding.")

    flooded_area_1985 = np.cumsum([stats_by_year[year] for year in years if year <= 1985])[-1] if 1985 in stats_by_year else 0
    if total_built_up_area != 0:
        percentage_1985 = (flooded_area_1985 / total_built_up_area_1985) * 100
        print(f"In 1985, {flooded_area_1985:.2f} sq.m of the city’s cumulative built-up area ({percentage_1985:.2f}%) was exposed to fluvial flooding.")
    else:
        print("The city was not exposed to fluvial flooding.")
else:
    print("No areas calculated.")
    




# %% [markdown]
# ### Fluvial and Population

# %%
get_fu_pop_norm()

# %% [markdown]
# ## Combined Flooding

# %% [markdown]
# ### Combined Flooding and WSF

# %%
#comb and wsf
stats_by_year = get_comb_wsf()
if stats_by_year is not None:
    years = list(stats_by_year.keys())
    areas = list(stats_by_year.values())

    cumulative_areas = np.cumsum(areas)

    cumulative_stats_by_year = dict(zip(years, cumulative_areas))

    years_to_plot = sorted(years)  
    areas_to_plot = [cumulative_stats_by_year.get(year, np.nan) for year in years_to_plot]

    plt.figure(figsize=(8, 8))
    plt.plot(years_to_plot, areas_to_plot, marker='o', linestyle='-')
    plt.title('Area exposed to Combined Flooding')
    plt.xlabel('Year')
    plt.ylabel('Exposed area in sq.km')
    plt.grid(True)
    plt.tight_layout()
    render_path = os.path.join(render_folder, f"{city}_comb_wsf.png")
    plt.savefig(render_path)
    plt.close()
    print(f"PNG saved to {render_path}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years_to_plot, y=areas_to_plot, mode='lines+markers', name='Area exposed to River Flooding'))
    fig.update_layout(xaxis_title='Year',
                      yaxis_title='Exposed area in sq.km',yaxis=dict(range=[0, max(areas_to_plot) * 1.1]))
    fig.show()
    fig.write_html(render_path.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')

    wsf_stats_file = Path(output_folder / f"{city}_wsf_stats.csv")  
    wsf = pd.read_csv(wsf_stats_file)
    total_built_up_area_2015 = wsf['cumulative sq km'].iloc[-1]
    total_built_up_area_1985 = wsf['cumulative sq km'].iloc[0]
    flooded_area_2015 = np.cumsum([stats_by_year[year] for year in years if year <= 2015])[-1]
    if total_built_up_area != 0:
        percentage_2015 = (flooded_area_2015 / total_built_up_area_2015) * 100
        print(f"In 2015, {flooded_area_2015:.2f} sq.km of the city’s cumulative built-up area ({percentage_2015:.2f}%) was exposed to combined flooding.")
    else:
        print("The city is not exposed to combined flooding.")
    flooded_area_1985 = np.cumsum([stats_by_year[year] for year in years if year <= 1985])[-1] if 1985 in stats_by_year else 0
    if total_built_up_area != 0:
        percentage_1985 = (flooded_area_1985 / total_built_up_area_1985) * 100
        print(f"In 1985, {flooded_area_1985:.2f} sq.km of the city’s cumulative built-up area ({percentage_1985:.2f}%) was exposed to combined flooding.")
    else:
        print("The city was not exposed to combined flooding.")
else:
    print("No areas calculated.")

# %% [markdown]
# ### Combined flooding and Population

# %%
get_comb_pop_norm()

# %% [markdown]
# ### Combined flooding and Infrastructure

# %%
get_comb_am()

# %% [markdown]
# ## Earthquake

# %%
get_earthquake_timeline()

# %%

def export_outputs_to_markdown(notebook_path, render_folder, output_path, city):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook_content = nbformat.read(f, as_version=4)
    
    # Initialize the Markdown exporter
    markdown_exporter = MarkdownExporter()
    markdown_exporter.exclude_input = True  
    markdown_output, resources = markdown_exporter.from_notebook_node(notebook_content)
    markdown_output_path = os.path.join(render_folder, output_path)
    with open(markdown_output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_output)

    base_dir = render_folder
    print(f"Base directory for organizing files: {base_dir}")
    plots_folder = os.path.join(base_dir, "plots")
    html_folder = os.path.join(plots_folder, "html")
    png_folder = os.path.join(plots_folder, "png")
    
    print(f"Creating folders:\n- {plots_folder}\n- {html_folder}\n- {png_folder}")

    os.makedirs(html_folder, exist_ok=True)
    os.makedirs(png_folder, exist_ok=True)

    for file in os.listdir(base_dir):
        if file.endswith(".html"):
            shutil.move(os.path.join(base_dir, file), os.path.join(html_folder, file))
            print(f"Moved {file} to {html_folder}")
        elif file.endswith(".png"):
            shutil.move(os.path.join(base_dir, file), os.path.join(png_folder, file))
            print(f"Moved {file} to {png_folder}")

input_notebook_path = "text.ipynb"
output_markdown_path = f"{city}_output_notebook.md"

export_outputs_to_markdown(input_notebook_path, render_folder, output_markdown_path, city)



