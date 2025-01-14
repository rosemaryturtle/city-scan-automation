import os
from google.cloud import storage
from os.path import exists

def download_blob(bucket_name, source_blob_name, destination_file_name, check_exists = False):
    """Downloads a blob from the bucket."""
    if check_exists:
        if exists(destination_file_name):
            print(f"File {destination_file_name} already exists.")
            return True
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    if blob.exists():
        blob.download_to_filename(destination_file_name)
        print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")
        return True
    print(f"Blob {source_blob_name} does not exist.")
    return False

def upload_blob(bucket_name, source_file_name, destination_blob_name, output = True, check_exists = False):
    """Uploads a file to the bucket."""
    if exists(source_file_name):
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        if output:
            # Mapping of file extensions to folder names
            folder_map = {
                ('.tif', '.gpkg'): 'spatial',
                ('.csv', '.txt'): 'tabular',
                ('.png'): 'images'
            }

            # Default folder name for other file types
            default_folder = 'other'

            # Get the folder name based on file extension
            for extensions, folder_name in folder_map.items():
                if any(destination_blob_name.endswith(ext) for ext in extensions):
                    target_folder = folder_name
                    break
            else:
                target_folder = default_folder

            # Construct the new destination_blob_name
            destination_blob_name = f'{os.path.dirname(destination_blob_name)}/{target_folder}/{os.path.basename(destination_blob_name)}'

        blob = bucket.blob(destination_blob_name)
        if check_exists:
            if blob.exists():
                print(f"File {destination_blob_name} already exists.")
                return
        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
        return True
    print(f"File {source_file_name} does not exist.")
    return False

def read_blob_to_memory(bucket_name, blob_name):
    """Reads a blob from Google Cloud Storage directly into memory."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()

def download_aoi(bucket_name, input_dir, aoi_shp_name, destination_dir):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=f"{input_dir}/AOI/{aoi_shp_name}.")
    os.makedirs(destination_dir, exist_ok=True)
    downloaded_list = []
    for blob in blobs:
        fn = f"{destination_dir}/{blob.name.split('/')[-1]}"
        blob.download_to_filename(fn)
        downloaded_list.append(fn)
    print(f"AOI {aoi_shp_name} downloaded to {destination_dir}.")
    return downloaded_list

def find_utm(aoi_file):
    import math
    from shapely.ops import unary_union

    # automatically find utm zone
    avg_lng = unary_union(aoi_file.geometry).centroid.x

    # calculate UTM zone from avg longitude to define CRS to project to
    utm_zone = math.floor((avg_lng + 180) / 6) + 1
    utm_crs = f"+proj=utm +zone={utm_zone} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"

    return utm_crs

def list_blobs_with_prefix(bucket_name, prefix, delimiter=None):
    """Lists all the blobs in the bucket that begin with the prefix.

    This can be used to list all blobs in a "folder", e.g. "public/".

    The delimiter argument can be used to restrict the results to only the
    "files" in the given "folder". Without the delimiter, the entire tree under
    the prefix is returned. For example, given these blobs:

        a/1.txt
        a/b/2.txt

    If you specify prefix ='a/', without a delimiter, you'll get back:

        a/1.txt
        a/b/2.txt

    However, if you specify prefix='a/' and delimiter='/', you'll get back
    only the file directly under 'a/':

        a/1.txt

    As part of the response, you'll also get back a blobs.prefixes entity
    that lists the "subfolders" under `a/`:

        a/b/
    """

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix, delimiter=delimiter)
    
    return blobs
    # Note: The call returns a response only when the iterator is consumed.
    # print("Blobs:")
    # for blob in blobs:
    #     print(blob.name)

    # if delimiter:
    #     print("Prefixes:")
    #     for prefix in blobs.prefixes:
    #         print(prefix)

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    print(f"Blob {blob_name} deleted.")

def download_blob_timed(bucket_name, source_blob_name, destination_file_name, time_limit, attempt_interval, check_exists = False):
    from datetime import datetime as dt
    import time

    time0 = dt.now()
    while (dt.now()-time0).total_seconds() <= time_limit:
        if download_blob(bucket_name, source_blob_name, destination_file_name, check_exists):
            return True
        time.sleep(attempt_interval)
    
    return False
