import os
from shutil import copyfile
import yaml

# Set the environment variable in your code
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:/Users/Owner/OneDrive/Documents/Career/World Bank/CRP/other/google-cloud-city-scan-service-account-key.json"

# load city inputs files, to be updated for each city scan
with open("../mnt/city-directories/01-user-input/city_inputs.yml", 'r') as f:
    city_inputs = yaml.safe_load(f)
city_name_l = city_inputs['city_name'].replace(' ', '_').replace("'", '').lower()

# make city directory
os.makedirs(f'mnt/{city_name_l}/01-user-input/AOI', exist_ok=True)
os.makedirs(f'mnt/{city_name_l}/02-process-output', exist_ok=True)
os.makedirs(f'mnt/{city_name_l}/03-render-output', exist_ok=True)

shp_suf = ['shp', 'shx', 'dbf', 'prj', 'sbn', 'sbx', 'fbn', 'fbx', 'ain', 'aih', 'ixs', 'mxs', 'atx', 'shp.xml', 'cpg', 'qix', 'idx']
for suf in shp_suf:
    orig_file = f'../mnt/city-directories/01-user-input/AOI/{city_inputs['AOI_shp_name']}.{suf}'
    if os.path.exists(orig_file):
        copyfile(orig_file, f'../mnt/city-directories/{city_name_l}/01-user-input/AOI/{city_name_l}.{suf}')

# TODO: make sure AOI is a polygon of an appropriate size
# TODO: if an AOI includes several polygons, make it a multipolygon

script_list = ["burned_area.py",
               'fwi.py',
               "gee_forest.py",
               "gee_landcover.py",
               "gee_lst_winter.py",
               "gee_lst.py",
               "gee_ndmi.py",
               "gee_ndvi.py",
               "gee_nightlight.py",
               "landcover_burnability.py",
               "osm_poi.py",
               "raster_processing.py",
               "road_network.py",
               "rwi.py",
               "soil_salinity.py",
               "contour_elev_stats.py",
               'slope.py',
               'flood_stats.py'
               ]

for s in script_list:
    with open(s) as f:
        exec(f.read())
