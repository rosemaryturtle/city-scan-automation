def landcover_burn(city_name_l, aoi_file, data_bucket, blob_name, local_output_dir, cloud_bucket, output_dir):
    print('run landcover_burnability')
    
    import rasterio
    import gc
    import utils
    import raster_pro

    # PROCESSING ########################################
    # Read AOI ---------------------
    features = aoi_file.geometry
    
    # Process data -----------------
    print('process data')
    # Read raster and shapefile into memory
    raster_bytes = utils.read_blob_to_memory(data_bucket, blob_name)

    out_image, out_meta = raster_pro.raster_mask_bytes(raster_bytes, features)

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
                    
    # out_image[(out_image < 0) | (out_image > 1)] = 0
    
    # Write output raster --------------------------
    print('write output raster')
    with rasterio.open(f"{local_output_dir}/{city_name_l}_lc_burn.tif", "w", **out_meta) as dst:
        dst.write(out_image)

    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_lc_burn.tif", f"{output_dir}/{city_name_l}_lc_burn.tif")

    # Clear memory -------------------
    del raster_bytes
    gc.collect()