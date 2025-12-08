# import
import time
import os
import geopandas as gpd
import pandas as pd
import requests
import rasterio
from rasterio.mask import mask
import yaml
from config.paths import INPUTS, OUTPUTS
from utils.aoi_module import find_country
from datetime import datetime as dt

# import logging setup
from utils.log_module import setup_logger
logger = setup_logger(__name__)

# read input files
city_inputs_path = INPUTS / "city_inputs.yml"
with open(city_inputs_path) as f:
    city_inputs = yaml.safe_load(f)
city_name = city_inputs['city_name'].replace(' ', '_').replace("'", "").lower()

# load AOI
aoi_path = INPUTS / f"AOI/{city_inputs['AOI_shp_name']}.shp"
aoi = gpd.read_file(aoi_path).to_crs(4326)
logger.info(f'successfully load AOI from: {aoi_path}')
# get country iso3 and country name
country_iso3, country_name = find_country(aoi=aoi)

# Update directories and make a copy of city inputs and menu in city-specific directory
if city_inputs.get('prev_run_date', None) is not None:
    cityscan_id = f"{city_inputs['prev_run_date']}-{country_name}-{city_name}"
else:
    cityscan_id = f"{dt.now().strftime('%Y-%m')}-{country_name}-{city_name}"
logger.info(f'working on {cityscan_id}')

# generate output directory and folders
input_dir = OUTPUTS / f'{cityscan_id}/01-user-input'
output_dir = OUTPUTS / f'{cityscan_id}/02-process-output'
render_dir = OUTPUTS / f'{cityscan_id}/03-render-output'
os.makedirs(input_dir, exist_ok=True)
os.makedirs(f'{output_dir}/images/', exist_ok=True)
os.makedirs(f'{output_dir}/spatial/', exist_ok=True)
os.makedirs(f'{output_dir}/tabular/', exist_ok=True)
os.makedirs(render_dir, exist_ok=True)

# Load menu file
menu_path = INPUTS / "menu.yml"
menu = yaml.safe_load(open(menu_path))


########################################################
################ RUN TASKS COMPONENTS ##################
########################################################

# Import task modules
from tasks.population_worldpop import datacollection as wp_collect
from tasks.population_worldpop import dataanalysis as wp_analysis
from tasks.population_worldpop import datavisualization as wp_vis

if menu.get("population"):
    logger.info("Running WorldPop population workflow...")
    pop_array, pop_meta = wp_collect.datacollection(aoi=aoi, city_name=city_name, country_iso3=country_iso3, output_dir=output_dir, return_raster=True)
    wp_analysis.compute_stats(city_name=city_name, output_dir=output_dir, clipped_image=pop_array, clipped_meta=pop_meta, return_df=False)
    wp_vis.plot_rastermap(city_name=city_name, output_dir=output_dir, clipped_image=pop_array, clipped_meta=pop_meta)
    wp_vis.plot_histogram(city_name=city_name, output_dir=output_dir, clipped_image=pop_array, clipped_meta=pop_meta)
    logger.info("Done with population WorldPop analysis")








