import os
import yaml
import utils
import geopandas as gpd
from datetime import datetime as dt
import aoi_helper
from google.cloud import firestore
from google.cloud import run_v2
import logging

########################################################
# CONFIGS ##############################################
########################################################

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def trigger_job2(project_id, region, job2_name, execution_id):
    """Trigger job2 with error handling"""
    try:
        client = run_v2.JobsClient()
        request = {
            "name": f"projects/{project_id}/locations/{region}/jobs/{job2_name}",
            "override_environment_vars": {
                "PARENT_EXECUTION_ID": execution_id
            }
        }
        operation = client.run_job(request=request)
        logger.info(f"Successfully triggered job2: {job2_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to trigger job2: {e}")
        return False

def update_completion_counter(counter_ref, task_count, db):
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
    # def update_counter(transaction, ref):
    #     snapshot = ref.get(transaction=transaction)
    #     if not snapshot.exists:
    #         transaction.set(ref, {
    #             'count': 1,
    #             'task_count': task_count
    #         })
    #         return 1
    #     current = snapshot.get('count', 0)
    #     transaction.update(ref, {'count': current + 1})
    #     return current + 1

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

        city_name = city_inputs['city_name']
        city_name_l = city_inputs['city_name'].replace(' ', '_').replace("'", "").lower()

        if city_inputs.get('AOI_shp_name', None):
            utils.download_aoi(cloud_bucket, input_dir, city_inputs['AOI_shp_name'], local_aoi_dir)
            aoi_file = gpd.read_file(f"{local_aoi_dir}/{city_inputs['AOI_shp_name']}.shp").to_crs(epsg = 4326)
        else:
            if not os.path.exists(f"{local_aoi_dir}/{city_name_l}.shp"):
                ucdb_gpkg = "ucdb.gpkg"
                utils.download_blob(data_bucket, global_inputs['ucdb_blob'], ucdb_gpkg, check_exists=True)
                
                city_boundary_gdf = aoi_helper.get_city_boundary(city_name, ucdb_gpkg, data_bucket, global_inputs, local_data_dir)
                aoi_helper.save_to_shp(city_boundary_gdf, f"{local_aoi_dir}/{city_name_l}.shp")

                print(f"Boundary successfully saved for {city_name}.")

                aoi_file = gpd.read_file(f"{local_aoi_dir}/{city_name_l}.shp")

        features = aoi_file.geometry

        # Load menu
        print('Load menu')
        with open('menu.yml', 'r') as f:
            menu = yaml.safe_load(f)

        # Checks country based on which country aoi_file overlaps with the most
        country_iso3, country_name, country_name_l = aoi_helper.find_country(data_bucket, global_inputs, local_data_dir, aoi_file = aoi_file)

        # Update directories and make a copy of city inputs and menu in city-specific directory
        if city_inputs.get('prev_run_date', None) is not None:
            city_dir = f"{city_inputs['prev_run_date']}-{country_name_l}-{city_name_l}"
            # check if this directory exists on google cloud storage; if not, print message and exit
            if not utils.check_dir_exists(cloud_bucket, city_dir):
                print(f"Directory {city_dir} does not exist in the {cloud_bucket} bucket. Please check prev_run_date in city_inputs.yml.")
                exit()
        else:
            city_dir = f"{dt.now().strftime('%Y-%m')}-{country_name_l}-{city_name_l}"
        input_dir = f'{city_dir}/{input_dir}'
        output_dir = f'{city_dir}/{output_dir}'
        utils.upload_blob(cloud_bucket, 'city_inputs.yml', f'{input_dir}/city_inputs.yml', output = False)
        utils.upload_blob(cloud_bucket, 'menu.yml', f'{input_dir}/menu.yml', output = False)

        aoi_files = [f for f in os.listdir(local_aoi_dir) if os.path.isfile(os.path.join(local_aoi_dir, f))]
        for f in aoi_files:
            utils.upload_blob(cloud_bucket, f"{local_aoi_dir}/{f}", f"{input_dir}/AOI/{f}", output = False, check_exists=True)


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
                import raster_pro
                import requests

                local_demo_folder = f'{local_data_dir}/demographics'
                os.makedirs(local_demo_folder, exist_ok=True)

                wp_file_json = requests.get(f"https://www.worldpop.org/rest/data/age_structures/ascic_2020?iso3={country_iso3}").json()
                wp_file_list = wp_file_json['data'][0]['files']

                raster_pro.download_raster(wp_file_list, local_demo_folder, data_bucket, data_bucket_dir='WorldPop age structures')

                sexes = ['f', 'm']

                with open(f'{local_output_dir}/{city_name_l}_demographics.csv', 'w') as f:
                    f.write('age_group,sex,population\n')

                    for i in [1] + list(range(0, 85, 5)):
                        for s in sexes:
                            out_image, out_meta = raster_pro.raster_mask_file(f'{local_demo_folder}/{country_iso3.lower()}_{s}_{i}_2020_constrained.tif', features)
                            out_image[out_image == out_meta['nodata']] = 0

                            if i == 0:
                                age_group_label = '0-1'
                            elif i == 1:
                                age_group_label = '1-4'
                            elif i == 80:
                                age_group_label = '80+'
                            else:
                                age_group_label = f'{i}-{i+4}'
                            
                            f.write('%s,%s,%s\n' % (age_group_label, s, sum(sum(sum(out_image)))))
                
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_demographics.csv', f'{output_dir}/{city_name_l}_demographics.csv')
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
                wsf.wsf(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir)
        elif task_index == 9:
            if menu['elevation']:  # processing time: 6m
                import elevation
                elevation.elevation(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir)

            if menu['slope']:  # processing time: 20s
                import raster_pro
                raster_pro.slope(aoi_file, f'{local_output_dir}/{city_name_l}_elevation_buf.tif', cloud_bucket, output_dir, city_name_l, local_output_dir)
                raster_pro.get_raster_histogram(f'{local_output_dir}/{city_name_l}_slope.tif', [0, 2, 5, 10, 20, 90], f'{local_output_dir}/{city_name_l}_slope.csv')
                utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_slope.csv', f'{output_dir}/{city_name_l}_slope.csv')
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
        elif task_index == 16:
            if menu['forest']:  # processing time (all GEE): 1m
                import gee_fun
                gee_fun.gee_forest(city_name_l, aoi_file, cloud_bucket, output_dir)

            if menu['green']:
                import gee_fun
                gee_fun.gee_ndxi(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, index_type = 'ndvi')

            if menu['landcover']:
                import gee_fun
                gee_fun.gee_landcover(city_name_l, aoi_file, local_output_dir, cloud_bucket, output_dir)
                utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_lc.csv", f'{output_dir}/{city_name_l}_lc.csv')

            if menu['lst_summer']:
                import gee_fun
                gee_fun.gee_lst(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, season = 'summer')

            if menu['lst_winter']:
                import gee_fun
                gee_fun.gee_lst(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, season = 'winter')

            if menu['ndmi']:
                import gee_fun
                gee_fun.gee_ndxi(city_name_l, aoi_file, local_output_dir, city_inputs['first_year'], city_inputs['last_year'], data_bucket, cloud_bucket, output_dir, index_type = 'ndmi')

            if menu['nightlight']:
                import gee_fun
                gee_fun.gee_nightlight(city_name_l, aoi_file, cloud_bucket, output_dir)
            
            # TODO: Check outputs exist before closing task
        # TODO: Add a step to copy the user provided data in 01-user-input/ to the city directory

        # Update completion counter
        completed_tasks = update_completion_counter(counter_ref, task_count, db)
        logger.info(f"Task {task_index} completed. Total completed: {completed_tasks}/{task_count}")

        # If all tasks are done, trigger job2
        if completed_tasks == task_count:
            logger.info("All tasks completed. Triggering job2...")
            if trigger_job2(project_id, region, job2_name, execution_id):
                logger.info("Job2 triggered successfully")
            else:
                logger.error("Failed to trigger job2")

    except Exception as e:
        logger.error(f"Task {task_index} failed: {e}")
        raise  # Re-raise to ensure Cloud Run marks the task as failed

if __name__ == "__main__":
    main()
