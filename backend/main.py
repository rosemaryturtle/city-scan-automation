import os
import yaml
import utils
import geopandas as gpd
from datetime import datetime as dt
import aoi_helper
from google.cloud import firestore
from google.cloud import run_v2
import logging
import time

########################################################
# CONFIGS ##############################################
########################################################

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_job2(project_id, region, job2_name, execution_id, GCS_CITY_DIR):
    # Create a client
    client = run_v2.JobsClient()

    # Define the job name
    job_name = f"projects/{project_id}/locations/{region}/jobs/{job2_name}"
    # job_name = "projects/YOUR_PROJECT_ID/locations/YOUR_LOCATION/jobs/YOUR_JOB_NAME"

    # Define environment variable overrides
    env_vars = [
        run_v2.EnvVar(name="PARENT_EXECUTION_ID", value=execution_id),
        run_v2.EnvVar(name="GCS_CITY_DIR", value=GCS_CITY_DIR)
    ]

    # Create container overrides
    container_override = run_v2.RunJobRequest.Overrides.ContainerOverride(
        env=env_vars
    )

    # Create the overrides object
    overrides = run_v2.RunJobRequest.Overrides(
        container_overrides=[container_override]
    )

    # Construct the request
    request = run_v2.RunJobRequest(
        name=job_name,
        overrides=overrides,
    )

    try:
        # Execute the job
        operation = client.run_job(request=request)
        print(f"Successfully triggered job2: {job2_name}")
        response = operation.result()  # Wait for the operation to complete
        print(f"Job executed successfully: {response}")
    except Exception as e:
        print(f"Failed to execute job: {e}")

def update_completion_counter(counter_ref, db):
    """Update completion counter with transaction and return completion status"""
    @firestore.transactional
    def update_counter(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        
        # Check if the document exists
        if not snapshot.exists:
            transaction.set(ref, {'count': 1})
            return 1
        
        # Use to_dict() and provide a default value for 'count'
        data = snapshot.to_dict() or {}
        current = data.get('count', 0)
        
        transaction.update(ref, {'count': current + 1})
        return current + 1

    transaction = db.transaction()
    return update_counter(transaction, counter_ref)

def main():
    # Get environment variables
    task_index = int(os.getenv('CLOUD_RUN_TASK_INDEX', 0))
    task_count = int(os.getenv('CLOUD_RUN_TASK_COUNT', 1))
    execution_id = os.getenv('CLOUD_RUN_EXECUTION')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'city-scan-gee-test')
    region = os.getenv('CLOUD_RUN_REGION', 'us-central1')
    job2_name = os.getenv('JOB2_NAME', 'frontend')
    city_name = os.getenv('city_name', None)
    
    if not all([execution_id, project_id, region]):
        raise ValueError("Missing required environment variables")

    logger.info(f"Starting task {task_index} of {task_count} (Execution: {execution_id})")

    try:
        # Initialize Firestore
        db = firestore.Client()
        counter_ref = db.collection('job_executions').document(execution_id)

        # Configure the directories
        print('Configure the directories')
        with open("config.yaml", 'r') as f:
            config = yaml.safe_load(f)

        cloud_bucket = config['cloud']['bucket']
        data_bucket = config['cloud']['data_bucket']
        input_dir = config['cloud']['input_dir']
        output_dir = config['cloud']['output_dir']
        render_dir = config['cloud']['render_dir']
        local_aoi_dir = config['local']['aoi_dir']
        local_data_dir = config['local']['data_dir']
        local_output_dir = config['local']['output_dir']

        os.makedirs(local_aoi_dir, exist_ok=True)
        os.makedirs(local_data_dir, exist_ok=True)
        os.makedirs(local_output_dir, exist_ok=True)

        # Download the city inputs and the menu YAML files
        print('Download the city inputs and the menu YAML files')
        utils.download_blob(cloud_bucket, f"{input_dir}/city_inputs.yml", 'city_inputs.yml')
        utils.download_blob(cloud_bucket, f"{input_dir}/global_inputs.yml", 'global_inputs.yml')
        utils.download_blob(cloud_bucket, f"{input_dir}/menu.yml", 'menu.yml')

        # Load global inputs, such as data sources that generally remain the same across scans
        print('Load global inputs')
        with open("global_inputs.yml", 'r') as f:
            global_inputs = yaml.safe_load(f)

        # Download the AOI and get city name
        print('Download the AOI and get city name')
        with open('city_inputs.yml', 'r') as f:
            city_inputs = yaml.safe_load(f)

        if city_name is None:
            city_name = city_inputs['city_name']
        city_name_l = city_name.replace(' ', '_').replace("'", "").lower()
        country_iso3, country_name, country_name_l = None, None, None

        if city_inputs.get('AOI_shp_name', None):
            utils.download_aoi(cloud_bucket, input_dir, city_inputs['AOI_shp_name'], local_aoi_dir)
            aoi_file = gpd.read_file(f"{local_aoi_dir}/{city_inputs['AOI_shp_name']}.shp").to_crs(epsg = 4326)
        else:
            if not os.path.exists(f"{local_aoi_dir}/{city_name_l}.shp"):
                ucdb_gpkg = "ucdb.gpkg"
                utils.download_blob(data_bucket, global_inputs['ucdb_blob'], ucdb_gpkg, check_exists=True)
                
                city_boundary_gdf, country_iso3, country_name, country_name_l = aoi_helper.get_city_boundary(city_name, ucdb_gpkg, data_bucket, global_inputs['countries_shp_dir'], global_inputs['countries_shp_blob'], local_data_dir)
                aoi_helper.save_to_shp(city_boundary_gdf, f"{local_aoi_dir}/{city_name_l}.shp")

                print(f"Boundary successfully saved for {city_name}.")

                aoi_file = gpd.read_file(f"{local_aoi_dir}/{city_name_l}.shp")

        features = aoi_file.geometry

        # Load menu
        print('Load menu')
        with open('menu.yml', 'r') as f:
            menu = yaml.safe_load(f)

        # Checks country based on which country aoi_file overlaps with the most
        country_name = country_name or city_inputs.get('country_name', None)
        if country_name is not None:
            country_name_l = country_name.replace(' ', '_').replace("'", "").lower()
        if country_name_l is None:
            country_iso3, country_name, country_name_l = aoi_helper.find_country(data_bucket, global_inputs['countries_shp_dir'], global_inputs['countries_shp_blob'], local_data_dir, aoi_file = aoi_file)

        # Update directories and make a copy of city inputs and menu in city-specific directory
        if city_inputs.get('prev_run_date', None) is not None:
            city_dir = f"{city_inputs['prev_run_date']}-{country_name_l}-{city_name_l}"
            # check if this directory exists on google cloud storage; if not, print message and exit
            if not utils.check_dir_exists(cloud_bucket, city_dir):
                print(f"Directory {city_dir} does not exist in the {cloud_bucket} bucket. Please check prev_run_date in city_inputs.yml.")
                exit(1)
        else:
            city_dir = f"{dt.now().strftime('%Y-%m')}-{country_name_l}-{city_name_l}"
        input_dir = f'{city_dir}/{input_dir}'
        output_dir = f'{city_dir}/{output_dir}'
        render_dir = f'{city_dir}/{render_dir}'
        utils.upload_blob(cloud_bucket, 'city_inputs.yml', f'{input_dir}/city_inputs.yml', type='input')
        utils.upload_blob(cloud_bucket, 'menu.yml', f'{input_dir}/menu.yml', type='input')

        aoi_files = [f for f in os.listdir(local_aoi_dir) if os.path.isfile(os.path.join(local_aoi_dir, f))]
        for f in aoi_files:
            utils.upload_blob(cloud_bucket, f"{local_aoi_dir}/{f}", f"{input_dir}/AOI/{f}", type='input', check_exists=True)

        # Configure plot fonts
        font_dict = {
            'family': 'system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, '
                    '"Noto Sans", "Liberation Sans", sans-serif, "Apple Color Emoji", '
                    '"Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"',
            'size': 12,  
            'color': 'black'  
        }


        ########################################################
        # RUN COMPONENTS #######################################
        ########################################################
        if task_index == 0:
            if menu['accessibility']:  # processing time: 40m
                import accessibility
                accessibility.accessibility(aoi_file, city_inputs, local_output_dir, city_name_l, cloud_bucket, output_dir)
        elif task_index in range(1, 6):
            if menu['burned_area']:  # processing time: 1h
                import burned_area
                burned_area.burned_area(aoi_file, global_inputs['burned_area_dir'], global_inputs['burned_area_blob_prefix'], task_index, data_bucket, local_data_dir, local_output_dir, city_name_l, cloud_bucket, output_dir)
        elif task_index == 6:
            if menu['demographics']:  # processing time: 19m
                import demographics
                demographics.demographics(local_data_dir, local_output_dir, data_bucket, cloud_bucket, city_name_l, country_iso3, features, output_dir)
                demographics.demo_plot(city_name, city_name_l, render_dir, font_dict, local_output_dir, cloud_bucket, output_dir)
        elif task_index == 7:
            if menu['population']:  # processing time: 20s
                import raster_pro
                import requests
                import rasterio

                local_pop_folder = f'{local_data_dir}/pop'
                os.makedirs(local_pop_folder, exist_ok=True)

                wp_file_json = requests.get(f"https://hub.worldpop.org/rest/data/pop/cic2020_100m?iso3={country_iso3}").json()
                wp_file_list = wp_file_json['data'][0]['files']

                downloaded_list = raster_pro.download_raster(wp_file_list, local_pop_folder, data_bucket, data_bucket_dir='WorldPop')
                raster_pro.mosaic_raster(downloaded_list, local_pop_folder, f'{city_name_l}_population.tif')
                out_image, out_meta = raster_pro.raster_mask_file(f'{local_pop_folder}/{city_name_l}_population.tif', features)
                with rasterio.open(f'{local_output_dir}/{city_name_l}_population.tif', "w", **out_meta) as dest:
                    dest.write(out_image)
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_population.tif', f'{output_dir}/{city_name_l}_population.tif')
        elif task_index == 8:
            if menu['wsf']:  # processing time: 30s
                import wsf
                wsf.wsf(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict)
        elif task_index == 9:
            if menu['elevation']:  # processing time: 6m
                import elevation
                elevation.elevation(aoi_file, local_data_dir, data_bucket, city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict)

            if menu['slope']:  # processing time: 20s
                import raster_pro
                from elevation import plot_slope_stats
                raster_pro.slope(aoi_file, f'{local_output_dir}/{city_name_l}_elevation_buf.tif', cloud_bucket, output_dir, city_name_l, local_output_dir)
                raster_pro.get_raster_histogram(f'{local_output_dir}/{city_name_l}_slope.tif', [0, 2, 5, 10, 20, 90], f'{local_output_dir}/{city_name_l}_slope.csv')
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_slope.csv', f'{output_dir}/{city_name_l}_slope.csv')
                plot_slope_stats(city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict)
        elif task_index == 10:
            if menu['flood_coastal'] or menu['flood_fluvial'] or menu['flood_pluvial']:  # processing time (2020 + 1 SSP): 13m
                import fathom
                
                with open('fathom_aws_credentials.yml', 'r') as f:
                    fathom_aws_credentials = yaml.safe_load(f)
                    aws_access_key_id = fathom_aws_credentials['aws_access_key_id']
                    aws_secret_access_key = fathom_aws_credentials['aws_secret_access_key']
                aws_bucket = global_inputs['fathom_aws_bucket']
                
                fathom.process_fathom(aoi_file, city_name_l, local_data_dir, city_inputs, menu, aws_access_key_id, aws_secret_access_key, aws_bucket, data_bucket, 'Fathom', local_output_dir, cloud_bucket, output_dir)
        elif task_index == 11:
            if menu['fwi']:  # processing time: 5m
                import fwi
                fwi.fwi(aoi_file, local_data_dir, data_bucket, city_inputs['fwi_first_year'], city_inputs['fwi_last_year'], global_inputs['fwi_dir'], global_inputs['fwi_blob_prefix'], local_output_dir, city_name_l, cloud_bucket, output_dir)
        elif task_index == 12:
            if menu['landcover_burn']:  # processing time: 40s
                import landcover_burnability
                landcover_burnability.landcover_burn(city_name_l, aoi_file, data_bucket, global_inputs['lc_burn_blob'], local_output_dir, cloud_bucket, output_dir)
        elif task_index == 13:
            if menu['road_network']:  # processing time: 12h
                import road_network
                road_network.road_network(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir)
        elif task_index == 14:
            if menu['rwi']:  # processing time: 50s
                import rwi
                rwi.rwi(global_inputs['rwi_dir'], global_inputs['rwi_blob_suffix'], country_iso3, data_bucket, local_data_dir, aoi_file, local_output_dir, city_name_l, cloud_bucket, output_dir)
        elif task_index == 15:
            for i in ['air', 'landslide', 'liquefaction', 'solar']:  # processing time: 1m
                if menu[i]:
                    import rasterio
                    import raster_pro
                    import gc

                    raster_bytes = utils.read_blob_to_memory(data_bucket, global_inputs[f'{i}_blob'])
                    out_image, out_meta = raster_pro.raster_mask_bytes(raster_bytes, features)
                    with rasterio.open(f'{local_output_dir}/{city_name_l}_{i}.tif', "w", **out_meta) as dest:
                        dest.write(out_image)

                    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_{i}.tif", f"{output_dir}/{city_name_l}_{i}.tif")

                    del raster_bytes
                    gc.collect()
            
            if menu['solar']:
                import solar
                solar.plot_solar(cloud_bucket, local_data_dir, data_bucket, global_inputs['solar_graph_blob'], features, city_name_l, local_output_dir, output_dir, render_dir, font_dict)
        elif task_index == 16:
            import gee_fun
            gee_outputs = []

            if menu['forest']:  # processing time (all GEE): 1m
                gee_outputs += gee_fun.gee_forest(city_name_l, aoi_file, cloud_bucket, output_dir)

            if menu['green']:
                gee_outputs += gee_fun.gee_ndxi(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, index_type = 'ndvi')

            if menu['landcover']:
                gee_outputs += gee_fun.gee_landcover(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir)
                utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_lc.csv", f'{output_dir}/{city_name_l}_lc.csv')
                gee_fun.gee_landcover_stats(cloud_bucket, city_name, city_name_l, local_output_dir, output_dir, render_dir, font_dict)

            if menu['lst_summer']:
                gee_outputs += gee_fun.gee_lst(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, season = 'summer')

            if menu['lst_winter']:
                gee_outputs += gee_fun.gee_lst(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, season = 'winter')

            if menu['ndmi']:
                gee_outputs += gee_fun.gee_ndxi(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, index_type = 'ndmi')

            if menu['nightlight']:
                gee_outputs += gee_fun.gee_nightlight(city_name_l, aoi_file, cloud_bucket, output_dir)
            
            for blob in gee_outputs:
                # Check every blob exists and only move on to the next blob if the current blob exists
                while not utils.check_blob_exists(cloud_bucket, blob):
                    time.sleep(60)
            print('All GEE outputs are ready.')
        elif task_index == 17:
            if menu['basic_info']:
                import basic_info

                basic_info_dict = {
                    'country': country_name,
                    'aoi_area': basic_info.calculate_aoi_area(aoi_file),
                    'koeppen': basic_info.get_koeppen_classification(features, data_bucket, global_inputs['koeppen_blob'], local_data_dir)
                }

                with open(f'{local_output_dir}/{city_name_l}_basic_info.yml', 'w') as f:
                    yaml.dump(basic_info_dict, f)
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_basic_info.yml', f'{output_dir}/{city_name_l}_basic_info.yml')
        elif task_index == 18:
            if menu['oe_plot']:
                import oe_plot
                oe_plot.oe_plot(data_bucket, cloud_bucket, global_inputs['oe_dir'], global_inputs['oe_locations_blob'], global_inputs['oegc_blob'], global_inputs['countries_shp_blob'], local_data_dir, 
                                country_name, country_name_l, city_name, city_name_l, city_inputs.get('alternate_city_name', None), local_output_dir, output_dir, render_dir, font_dict)
        elif task_index == 19:
            if menu['earthquake']:
                import earthquake_event
                earthquake_event.plot_earthquake_event(features, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict)
        elif task_index == 20:
            if menu['flood_event']:
                import flood_event
                flood_event.plot_flood_event(data_bucket, cloud_bucket, global_inputs['flood_archive_dir'], global_inputs['flood_archive_blob'], features, local_data_dir, local_output_dir, city_name_l, output_dir, render_dir, font_dict)
        elif task_index == 21:
            if menu['ghs_population']:
                import ghs_population
                ghs_population.ghs_population(aoi_file,city_inputs, local_output_dir, city_name_l, global_inputs['ghsl_bucket'],cloud_bucket, output_dir, global_inputs['ghsl_blob'])
        elif task_index == 22:
            if menu['ghs_builtup']:
                import ghs_builtup
                ghs_builtup.ghs_builtup(aoi_file,city_inputs, local_output_dir, city_name_l, global_inputs['ghsl_bucket'],cloud_bucket, output_dir, global_inputs['ghsl_blob'])
                ghs_builtup.ghs_builtup_overtime(aoi_file, city_inputs, local_output_dir, city_name_l, global_inputs['ghsl_bucket'], cloud_bucket, output_dir, global_inputs['ghsl_blob'], threshold=1200)

            
        # TODO: Add a step to copy the user provided data in 01-user-input/ to the city directory

        # Update completion counter
        completed_tasks = update_completion_counter(counter_ref, db)
        logger.info(f"Task {task_index} completed. Total completed: {completed_tasks}/{task_count}")

        # If all tasks are done, trigger job2
        if completed_tasks == task_count:
            logger.info("All tasks completed. Triggering job2...")
            if trigger_job2(project_id, region, job2_name, execution_id, city_dir):
                logger.info("Job2 triggered successfully")
            else:
                logger.error("Failed to trigger job2")

    except Exception as e:
        logger.error(f"Task {task_index} failed: {e}")
        raise  # Re-raise to ensure Cloud Run marks the task as failed

if __name__ == "__main__":
    main()
