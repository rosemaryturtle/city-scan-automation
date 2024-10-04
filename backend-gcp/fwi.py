def fwi(aoi_file, local_data_dir, data_bucket, fwi_first_year, fwi_last_year, fwi_source, local_output_dir, city_name_l, cloud_bucket, output_dir):
    print('run fwi')
    
    import os
    import pandas as pd
    import geopandas as gpd
    import rasterio.mask
    import rasterio
    from shapely.geometry import box
    import glob
    import numpy as np
    from rasterio.crs import CRS
    import utils
    import raster_pro

    # PARAMETERS #######################################
    aoi_buff = aoi_file.buffer(2).total_bounds
    features = gpd.GeoDataFrame({'geometry': box(*aoi_buff)}, index = [0], crs = CRS.from_epsg(4326)).geometry

    local_fwi_folder = f'{local_data_dir}/fwi'
    os.makedirs(local_fwi_folder, exist_ok=True)


    # PROCESSING ###################################
    fwi_raster_dict = {}

    # download FWI dataset ---------------------------
    for blob in utils.list_blobs_with_prefix(data_bucket, f'{fwi_source}/'):
        utils.download_blob(data_bucket, blob.name, f"{local_fwi_folder}/{blob.name.split('/')[-1]}")

    # clip raster and store in dict --------------------
    for year in range(fwi_first_year, fwi_last_year + 1):
        for r in glob.glob(f"{local_fwi_folder}/FWI.GEOS-5.Daily.Default.{year}*.tif"):
            out_image, out_meta = raster_pro.raster_mask_file(r, features)
            
            if np.nansum(out_image) != 0:
                fwi_raster_dict[r.split('.')[-2][-9:]] = out_image
            
    q99_raster = np.nanpercentile(list(fwi_raster_dict.values()), 98.6, axis = 0)

    with rasterio.open(f'{local_output_dir}/{city_name_l}_fwi.tif', 'w', **out_meta) as dest:
        dest.write(q99_raster)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_fwi.tif', f'{output_dir}/{city_name_l}_fwi.tif')
    
    # calculate 95th percentile FWI by week -------------------
    fwi_val_dict = {}

    for i in fwi_raster_dict:
        fwi_val_dict[i] = fwi_raster_dict[i].flatten().tolist()

    df = pd.DataFrame(list(fwi_val_dict.items()), columns=['date_str', 'fwi'])
    df['date'] = pd.to_datetime(df['date_str'], format='%Y%m%d')
    df['week'] = df['date'].dt.isocalendar().week
    df = df.explode('fwi', ignore_index=True)
    week_95th = df.groupby('week').agg(pctile_95 = ('fwi', lambda x: np.nanpercentile(x, 95)))

    week_95th.to_csv(f'{local_output_dir}/{city_name_l}_fwi.csv', index=True)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_fwi.csv', f'{output_dir}/{city_name_l}_fwi.csv')

    # delete data files ------------
    for year in range(fwi_first_year, fwi_last_year + 1):
        for r in glob.glob(f"{local_fwi_folder}/FWI.GEOS-5.Daily.Default.{year}*.tif"):
            os.remove(r)