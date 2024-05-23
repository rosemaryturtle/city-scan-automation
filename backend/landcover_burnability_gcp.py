# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml
from google.cloud import storage
# import os

# LOAD MENU #############################
# Set the environment variable in your code
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:/Users/Owner/OneDrive/Documents/Career/World Bank/CRP/other/google-cloud-city-scan-service-account-key.json"

# Initialize a storage client
storage_client = storage.Client()

# Define the bucket name, folder name, and file name
bucket_name = 'crp-city-scan'
input_dir = '01-user-input'
output_dir = '02-process-output'

# Get the bucket and blob (file) from Cloud Storage
bucket = storage_client.bucket(bucket_name)

# Parse the YAML content
menu = yaml.safe_load(bucket.blob(f'{input_dir}/menu.yml').download_as_string())

if menu['landcover_burn']:
    print('run landcover_burnability')
    
    import os
    import geopandas as gpd
    import rasterio.mask
    import rasterio
    from rasterio.io import MemoryFile
    import tempfile

    # SET UP ##############################################
    city_inputs = yaml.safe_load(bucket.blob(f'{input_dir}/city_inputs.yml').download_as_string())

    city_name_l = city_inputs['city_name'].replace(' ', '_').lower()

    # load global inputs, such as data sources that generally remain the same across scans
    with open("global_inputs.yml", 'r') as f:
        global_inputs = yaml.safe_load(f)

    # Read AOI shapefile --------
    print('read AOI shapefile')
    # transform the input shp to correct prj (epsg 4326)
    aoi_file = gpd.read_file(city_inputs['AOI_path']).to_crs(epsg = 4326)
    features = aoi_file.geometry


    # PROCESSING ########################################
    if not bucket.blob(f'{output_dir}/{city_name_l}_lc_burn.tif').exists():
        data_bucket = storage_client.bucket(global_inputs['data_bucket'])
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Download the GeoTIFF file to the temporary file
            data_bucket.blob(global_inputs['lc_burn_blob']).download_to_filename(temp_file.name)

            # Open the GeoTIFF file with rasterio
            with rasterio.open(temp_file.name) as src:
                # shapely presumes all operations on two or more features exist in the same Cartesian plane.
                out_image, out_transform = rasterio.mask.mask(
                    src, features, all_touched = True, crop = True)
                out_meta = src.meta.copy()

        out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})
        
        ls000 = [190, 200, 201, 202, 210, 220]
        ls016 = [151]
        ls033 = [12, 140, 152, 153]
        ls050 = [11, 82, 110, 150, 180]
        ls066 = [10, 20, 30, 40, 70, 71, 81, 90, 121, 130]
        ls083 = [50, 61, 80, 100, 120, 122, 160, 170]
        ls100 = [60, 62]

        output_input_dict = {0: ls000,
                            0.16: ls016,
                            0.33: ls033,
                            0.5: ls050,
                            0.66: ls066,
                            0.83: ls083,
                            1: ls100}

        for i in range(len(out_image[0])):
            for j in range(len(out_image[0, i])):
                for out_val in output_input_dict:
                    if out_image[0, i, j] in output_input_dict[out_val]:
                        out_image[0, i, j] = out_val
                        
        out_image[(out_image < 0) | (out_image > 1)] = 0
            
        # Use MemoryFile to create an in-memory GeoTIFF
        with MemoryFile() as memfile:
            with memfile.open(**out_meta) as dataset:
                dataset.write(out_image)

            # Upload the GeoTIFF file to the bucket from the in-memory file
            bucket.blob(f'{output_dir}/{city_name_l}_lc_burn.tif').upload_from_string(memfile.read(), content_type = 'image/tiff')
        
        # Delete the temp file
        os.unlink(temp_file.name)