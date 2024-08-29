import os
from google.cloud import storage
from os.path import exists

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    if exists(source_file_name):
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to {destination_blob_name}.")
        return True
    else:
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
    for blob in blobs:
        blob.download_to_filename(f"{destination_dir}/{blob.name.split('/')[-1]}")
    print(f"AOI {aoi_shp_name} downloaded to {destination_dir}.")

def blob_exists(bucket_name, blob_name):
    """Checks if a blob exists."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.exists()

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