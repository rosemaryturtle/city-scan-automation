def rwi(rwi_source, country_iso3, data_bucket, local_data_dir, aoi_file, local_output_dir, city_name_l, cloud_bucket, output_dir):
    print('run rwi')
    
    import os
    import pandas as pd
    import geopandas as gpd
    from pyquadkey2.quadkey import QuadKey
    from pyquadkey2.quadkey import TileAnchor, QuadKey
    from shapely.geometry import Polygon
    import utils

    # PROCESS RWI DATA ################################
    rwi_data = f"{country_iso3}_relative_wealth_index.csv"
    
    if utils.download_blob(data_bucket, f'{rwi_source}/{rwi_data}', f'{local_data_dir}/{rwi_data}'):
        FB_QKdata = pd.read_csv(f'{local_data_dir}/{rwi_data}')
        # change quadkey format to str
        FB_QKdata["quadkey1"] = FB_QKdata["quadkey"].astype('str')
        # fill 13 digit quadkeys with 0 before the QK
        FB_QKdata['quadkey1'] = FB_QKdata['quadkey1'].apply(lambda x: x.zfill(14))
        # take column with quadkeys and transform it to list and then to QuadKey object
        fb_qk = FB_QKdata["quadkey1"].tolist()
        FB_QK = [QuadKey(i) for i in fb_qk]

        # locate the four corners of QuadKey tiles
        SW = []
        NE = []
        SE = []
        NW = []

        for i in FB_QK:
            #south west point
            sw = i.to_geo(anchor=TileAnchor.ANCHOR_SW)
            SW.append(sw) 
            #north west point
            ne = i.to_geo(anchor=TileAnchor.ANCHOR_NE)
            NE.append(ne) 
            #south east point 
            se = i.to_geo(anchor=TileAnchor.ANCHOR_SE)
            SE.append(se)
            #north west point 
            nw = i.to_geo(anchor=TileAnchor.ANCHOR_NW)
            NW.append(nw)
        
        # flip lat and lon for tile corner coordinates
        swFinal = [(i[1], i[0]) for i in SW]
        neFinal = [(i[1], i[0]) for i in NE]
        seFinal = [(i[1], i[0]) for i in SE]
        nwFinal = [(i[1], i[0]) for i in NW]

        # generate Polygon object based on four corner coordinates
        tiledata = [Polygon([nw, sw, se, ne]) for sw, ne, se, nw in zip(swFinal, neFinal, seFinal, nwFinal)]

        # create GeoDataFrame with Polygons
        gdf = gpd.GeoDataFrame(geometry = tiledata, crs = "epsg:4326")

        # add QuadKeys to gdf
        gdf['quadkey'] = FB_QK

        # change type of quadkey column to str
        gdf["quadkey"] = gdf["quadkey"].astype('str')

        # merge gdf and fb data
        gdf = gdf.merge(FB_QKdata, left_on = 'quadkey', right_on = 'quadkey1', how = 'inner')

        # export to shapefile
        gdf_aoi = gpd.clip(gdf, aoi_file)

        gdf_aoi.to_file(f"{local_output_dir}/{city_name_l}_rwi.gpkg", driver = 'GPKG', layer = 'rwi')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_rwi.gpkg", f"{output_dir}/{city_name_l}_rwi.gpkg")

        # delete data file
        os.remove(f'{local_data_dir}/{rwi_data}')
    else:
        print(f'No RWI data for {country_iso3}')
