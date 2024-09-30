def accessibility(aoi_file, city_inputs, local_output_dir, city_name_l, cloud_bucket, output_dir):    
    print('run accessibility')
    
    import os
    import geopandas as gpd
    import osmnx as ox
    import pickle
    import pandas as pd
    import GOSTnets as gn
    import utils
    from GOSTnets.fetch_pois import OsmObject

    # Read AOI shapefile --------
    # buffer AOI by 5% of its width to capture roads immedately outside of city boundaries
    buff_dist = (aoi_file.total_bounds[2] - aoi_file.total_bounds[0]) * city_inputs['accessibility_buffer'] / 100
    aoi_file = aoi_file.buffer(buff_dist)
    features = aoi_file.geometry

    # COMPILE ISOCHRONE DICTIONARY #################
    isochrones = None
    if ('isochrone' in city_inputs) and bool(city_inputs['isochrone']):
        isochrones = city_inputs['isochrone']

    # PROCESS BY POLYGON ###############################
    for fi in range(len(features)):
        try:
            # EXTRACT OSM POI ##############################
            queries = {}
            if ('osm_query' in city_inputs) and bool(city_inputs['osm_query']):
                for tags in city_inputs['osm_query'].items():
                    # create the OsmObject
                    queries[tags[0]] = OsmObject(f'{tags[0]}', features[fi], tags[1])
            
            for query in queries.items():
                try:
                    result = query[1].GenerateOSMPOIs()
                
                    # if query is not empty
                    if result.empty == False:
                        # try:
                        query[1].RemoveDupes(0.0005)
                        
                        if 'name' in query[1].df.columns:
                            query_results = query[1].df[['amenity','geometry','name']]
                        else:
                            query_results = query[1].df[['amenity','geometry']]

                        # convert to GeoDataFrame
                        query_results_gpd = gpd.GeoDataFrame(query_results, crs = "epsg:4326", geometry = 'geometry')
                        query_results_gpd.to_file(f'{local_output_dir}/{city_name_l}_osm_{query[0]}_{fi}.gpkg', driver='GPKG', layer=f'{query[0]}_{fi}')
                except Exception:
                    pass
            
            
            # PROCESS ROADS ##############################
            road_graph = f"{local_output_dir}/{city_name_l}_osm_roads_{fi}.pickle"

            # extent = box(*features[i].total_bounds)
            G = ox.graph_from_polygon(features[fi], network_type = 'drive_service', retain_all = True, truncate_by_edge = True)   # available network_type {"all", "all_public", "bike", "drive", "drive_service", "walk"}
            # This is how time is calculated from the OSMNX length attribute
            G = gn.convert_network_to_time(G, 'length')  # default walk_speed = 4.5 (km/h)

            with open(road_graph, 'wb') as f:
                pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

            roads = gn.edge_gdf_from_graph(G)

            def replace_hwy(x):
                if isinstance(x, list):
                    x = x[0]
                return x

            roads['highway'] = roads.apply(lambda x: replace_hwy(x['highway']), axis = 1)

            roads = roads[['length','time','mode','geometry']]
            roads.to_file(f'{local_output_dir}/{city_name_l}_osm_roads_{fi}.gpkg', driver='GPKG', layer=f'roads_{fi}')


            # SNAP POI TO ROADS ############################
            snapped_destinations_dict = {}
            for results_gpd in isochrones:
                results_gpd_gpkg = f'{local_output_dir}/{city_name_l}_osm_{results_gpd}_{fi}.gpkg'
                if os.path.exists(results_gpd_gpkg):
                    snapped_destinations = gn.pandana_snap(G, gpd.read_file(results_gpd_gpkg, layer = f'{results_gpd}_{fi}'))
                    snapped_destinations_dict[results_gpd] = list(snapped_destinations['NN'].unique())
            

            # PROCESS ISOCHRONES ###########################
            # find graph utm zone
            G_utm = gn.utm_of_graph(G)

            def isochrone_processing(amenity_type):
                amenity_threshold_list = isochrones.get(amenity_type)
                if amenity_threshold_list == None:
                    print(f"Amenity type {amenity_type} not found")
                    return
                # if no destinations for amenity type exist
                if snapped_destinations_dict.get(amenity_type) == None:
                    print(f"no destinations for {amenity_type} exist")
                else:
                    for threshold in amenity_threshold_list:
                        print(f'process isochrone for {amenity_type}')
                        iso_gdf = gn.make_iso_polys(G, snapped_destinations_dict[amenity_type], [threshold], edge_buff = 300, node_buff = 300, weight = 'length', measure_crs = G_utm)
                        dissolved = iso_gdf.dissolve(by = "thresh")
                        gdf_out = dissolved.explode(index_parts = True)
                        gdf_out2 = gdf_out.reset_index()
                        # save file
                        gdf_out2.to_file(f'{local_output_dir}/{city_name_l}_accessibility_{amenity_type}_{threshold}m_{fi}.gpkg', driver='GPKG', layer=f'{amenity_type}_iso')
                    
            for key in snapped_destinations_dict:
                isochrone_processing(key)
        except Exception as e:
            print(f'error encountered in feature {fi}: {e}')


    # COMBINE FILES ACROSS POLYGONS ##########################
    tag_list = ['roads']
    if ('osm_query' in city_inputs) and bool(city_inputs['osm_query']):
        for tag in city_inputs['osm_query']:
            tag_list.append(tag)
    
    for tag in tag_list:
        gdf_concat = [
            gpd.read_file(f'{local_output_dir}/{city_name_l}_osm_{tag}_{fi}.gpkg', layer=f'{tag}_{fi}')
            for fi in range(len(features))
            if os.path.exists(f'{local_output_dir}/{city_name_l}_osm_{tag}_{fi}.gpkg')
        ]
        
        if gdf_concat:
            gpd.GeoDataFrame(pd.concat(gdf_concat)).to_file(f'{local_output_dir}/{city_name_l}_osm_{tag}.gpkg', driver='GPKG', layer = tag)
            utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_osm_{tag}.gpkg', f'{output_dir}/{city_name_l}_osm_{tag}.gpkg')

    if isochrones:
        for iso in isochrones:
            if isochrones[iso]:
                for dist in isochrones[iso]:
                    gdf_concat = [
                        gpd.read_file(f'{local_output_dir}/{city_name_l}_accessibility_{iso}_{dist}m_{fi}.gpkg', layer=f'{iso}_iso')
                        for fi in range(len(features))
                        if os.path.exists(f'{local_output_dir}/{city_name_l}_accessibility_{iso}_{dist}m_{fi}.gpkg')
                    ]

                    if gdf_concat:
                        gpd.GeoDataFrame(pd.concat(gdf_concat)).dissolve().to_file(f'{local_output_dir}/{city_name_l}_accessibility_{iso}_{dist}m.gpkg', driver = 'GPKG', layer = f'{iso}_iso')
                        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_accessibility_{iso}_{dist}m.gpkg', f'{output_dir}/{city_name_l}_accessibility_{iso}_{dist}m.gpkg')
