def elevation(aoi_file, local_data_dir, data_bucket, city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict):
    import raster_pro
    import zipfile
    import os
    import rasterio
    import utils

    # download
    local_elev_folder = f'{local_data_dir}/elev'
    os.makedirs(local_elev_folder, exist_ok=True)

    aoi_file_buf = aoi_file.buffer(0.001)
    lat_tiles_small = raster_pro.tile_finder(aoi_file_buf, 'lat', 1)
    lon_tiles_small = raster_pro.tile_finder(aoi_file_buf, 'lon', 1)

    elev_download_dict = {}
    for lat1 in lat_tiles_small:
        for lon1 in lon_tiles_small:
            file_name1 = f'{lat1}{lon1}_FABDEM_V1-2.tif'
            lat, lon = raster_pro.fabdem_big_tile_matcher(lat1, lon1)
            elev_download_dict[file_name1] = f'{lat}{lon}-{raster_pro.fabdem_tile_end_matcher(lat)}{raster_pro.fabdem_tile_end_matcher(lon)}_FABDEM_V1-2.zip'

    elev_download_list = [f'https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/{fn}' for fn in list(elev_download_dict.values())]
    downloaded_list = raster_pro.download_raster(list(set(elev_download_list)), local_elev_folder, data_bucket, data_bucket_dir='FABDEM')
    mosaic_list = []

    # unzip and mosaic as needed
    for fn in elev_download_dict:
        if f'{local_elev_folder}/{elev_download_dict[fn]}' in downloaded_list:
            try:
                with zipfile.ZipFile(f'{local_elev_folder}/{elev_download_dict[fn]}', 'r') as z:
                    z.extract(fn, local_elev_folder)
                    mosaic_list.append(f'{local_elev_folder}/{fn}')
            except Exception:
                pass
    
    if mosaic_list:
        raster_pro.mosaic_raster(mosaic_list, local_elev_folder, f'{city_name_l}_elevation.tif')
        out_image, out_meta = raster_pro.raster_mask_file(f'{local_elev_folder}/{city_name_l}_elevation.tif', aoi_file.geometry)
        with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation.tif', "w", **out_meta) as dest:
            dest.write(out_image)
        out_image, out_meta = raster_pro.raster_mask_file(f'{local_elev_folder}/{city_name_l}_elevation.tif', aoi_file_buf.geometry)
        with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation_buf.tif', "w", **out_meta) as dest:
            dest.write(out_image)
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.tif', f'{output_dir}/{city_name_l}_elevation.tif')
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation_buf.tif', f'{output_dir}/{city_name_l}_elevation_buf.tif')
        with open(f"{local_output_dir}/{city_name_l}_elevation_source.txt", 'w') as f:
            f.write('FABDEM')
    else:
        import gee_fun

        gee_fun.gee_elevation(city_name_l, aoi_file, cloud_bucket, output_dir)
        utils.download_blob_timed(cloud_bucket, f"{output_dir}/spatial/{city_name_l}_elevation.tif", f'{local_output_dir}/{city_name_l}_elevation.tif', 60*60, 30)
        with open(f"{local_output_dir}/{city_name_l}_elevation_source.txt", 'w') as f:
            f.write('SRTM')

    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_elevation_source.txt", f"{output_dir}/{city_name_l}_elevation_source.txt")

    contour_levels = contour(city_name_l, local_output_dir, cloud_bucket, output_dir)
    elevation_stats(city_name_l, local_output_dir, cloud_bucket, output_dir, contour_levels)
    plot_elevation_stats(city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict)

def contour(city_name_l, local_output_dir, cloud_bucket, output_dir):
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon
    import fiona
    import math
    import rasterio
    import utils

    with rasterio.open(f'{local_output_dir}/{city_name_l}_elevation.tif') as src:
        elevation_data = src.read(1)
        transform = src.transform
        demNan = src.nodata if src.nodata else -9999
    
    # Get min and max elevation values
    demMax = elevation_data.max()
    demMin = elevation_data[elevation_data != demNan].min()
    demDiff = demMax - demMin

    # Generate contour lines
    # Determine contour intervals
    contourInt = 1
    if demDiff > 250:
        contourInt = math.ceil(demDiff / 500) * 10
    elif demDiff > 100:
        contourInt = 5
    elif demDiff > 50:
        contourInt = 2
    
    contourMin = math.floor(demMin / contourInt) * contourInt
    contourMax = math.ceil(demMax / contourInt) * contourInt
    if contourMin < demMin:
        contour_levels = range(contourMin + contourInt, contourMax + contourInt, contourInt)
    else:
        contour_levels = range(contourMin, contourMax + contourInt, contourInt)

    contours = plt.contourf(elevation_data, levels=contour_levels)

    # Convert contours to Shapely geometries
    contour_polygons = []
    # Iterate over all contour levels and their corresponding segments
    for level, segments in zip(contours.levels, contours.allsegs):
        if len(segments) == 0:  # Skip levels with no segments
            continue
        
        for segment in segments:  # Iterate over paths (segments) at this level
            if len(segment) > 2:  # Ensure valid polygons with enough points
                # Convert segment coordinates from pixel space to geographic coordinates
                geographic_polygon = [
                    (transform * (x, y)) for x, y in segment
                ]
                poly = Polygon(geographic_polygon)
                if poly.is_valid:  # Ensure valid geometry before appending
                    contour_polygons.append((poly, float(level)))

    # Optionally save to a shapefile using Fiona
    schema = {
        'geometry': 'Polygon',
        'properties': {'elevation': 'float'},
    }

    with fiona.open(f'{local_output_dir}/{city_name_l}_contours.gpkg', 'w', driver='GPKG', schema=schema, crs='EPSG:4326', layer='contours') as shpfile:
        for poly, elevation in contour_polygons:
            shpfile.write({
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [list(poly.exterior.coords)],
                },
                'properties': {'elevation': elevation},
            })

    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_contours.gpkg', f"{output_dir}/{city_name_l}_contours.gpkg")
    return range(contourMin, contourMax + contourInt, contourInt)

def elevation_stats(city_name_l, local_output_dir, cloud_bucket, output_dir, contour_levels):
    import raster_pro
    import utils

    contour_levels = list(contour_levels)
    contour_bins = [contour_levels[int(((len(contour_levels) - 6) / 5 + 1) * i)] for i in range(6)]
    raster_pro.get_raster_histogram(f'{local_output_dir}/{city_name_l}_elevation.tif', contour_bins, f'{local_output_dir}/{city_name_l}_elevation.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_elevation.csv', f'{output_dir}/{city_name_l}_elevation.csv')

def plot_elevation_stats(city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict):
    from os.path import exists
    
    elev_stats_file = f"{local_output_dir}/{city_name_l}_elevation.csv"
    if exists(elev_stats_file):
        import pandas as pd
        import matplotlib.pyplot as plt
        import squarify
        import plotly.express as px
        import utils
        import yaml
        
        elev = pd.read_csv(elev_stats_file)
        
        # Check for necessary columns
        if 'Bin' not in elev.columns or 'Count' not in elev.columns:
            print("Missing required columns in elevation stats.")
            return
        
        elev['Bin'] = elev['Bin'].astype(str).str.strip()
        elev = elev[elev['Count'] > 0]
        
        total_count = elev['Count'].sum()
        if total_count == 0:
            print("Total count is zero, cannot calculate percentages.")
            return

        elev['percent'] = elev['Count'] / total_count * 100

        # Define elevation colors as shades of pink/magenta
        elevation_colors = [
            "#f5c4c0",  # Light Pink
            "#f19bb4",  # Medium Pink
            "#ec5fa1",  # Darker Pink
            "#c20b8a",  # Magenta
            "#762175"   # Dark Magenta
        ]

        # Convert 'Bin' to a categorical type
        elev['Bin'] = pd.Categorical(elev['Bin'], categories=elev['Bin'].unique(), ordered=True)

        # Static treemap using squarify
        plt.figure(figsize=(12, 8))
        squarify.plot(
            sizes=elev['percent'], 
            label=elev['Bin'], 
            color=elevation_colors, 
            alpha=0.8, 
            pad=True
        )
        plt.title(f"Elevation Distribution in {city_name}")
        plt.axis('off')
        plt.tight_layout()

        render_path_png = f"{local_output_dir}/{city_name_l}_elevation_treemap.png"
        plt.savefig(render_path_png, bbox_inches='tight')
        plt.close()
        utils.upload_blob(cloud_bucket, render_path_png, f"{render_dir}/{city_name_l}_elevation_treemap.png", type='render')

        # Interactive treemap using Plotly
        try:
            fig = px.treemap(
                elev, 
                path=['Bin'],  
                values='percent', 
                color='Bin',
                color_discrete_sequence=elevation_colors,  # Use the defined color sequence
                labels={'percent': 'Percentage', 'Elevation': 'Elevation Range'}
            )

            fig.update_layout(
                showlegend=False,
                margin=dict(t=50, l=25, r=25, b=25),
                font=font_dict  # Ensure font_dict is defined
            )
            fig.show()
            fig.write_html(render_path_png.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')
            utils.upload_blob(cloud_bucket, render_path_png.replace('.png', '.html'), f"{render_dir}/{city_name_l}_elevation_treemap.html", type='render')
        except ValueError as e:
            print(f"Error while creating treemap: {e}")
            return

        # Finding the highest percentage
        max_percent_index = elev['percent'].idxmax()
        highest_percent_row = elev.loc[max_percent_index]
        elev_stats = {'elev_stats': f"The most common elevation range in the city is {highest_percent_row['Bin']} meters, with a {highest_percent_row['percent']:.2f}% frequency."}
        with open(f"{local_output_dir}/{city_name_l}_elev_stats.yml", 'w') as f:
            yaml.dump(elev_stats, f)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_elev_stats.yml", f"{output_dir}/{city_name_l}_elevation_stats.yml")

def plot_slope_stats(city_name, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict):
    from os.path import exists
    
    slope_stats_file = f"{local_output_dir}/{city_name_l}_slope.csv"
    if exists(slope_stats_file):
        import pandas as pd
        import matplotlib.pyplot as plt
        import squarify
        import plotly.express as px
        import utils
        import yaml

        slope = pd.read_csv(slope_stats_file)
        slope = slope[slope['Count'] > 0].copy()
        total_count = slope['Count'].sum()

        slope['percent'] = slope['Count'] / total_count * 100

        slope['percent'] = pd.to_numeric(slope['percent'], errors='coerce')

        slope['Percent'] = (slope['percent'] / 100).apply(lambda x: f"{x:.0%}")
        slope['Slope'] = slope['Bin'].str.extract(r"(\d+)").astype(float)
        slope['Bin'] = pd.Categorical(slope['Bin'], categories=slope['Bin'].unique())

        slope['UpperRange'] = slope['Bin'].str.extract(r"-(\d+)$").astype(float)
        max_upper_range = slope['UpperRange'].max()

        slope_colors = {
            "0-2": "#ffffd4",
            "2-5": "#fed98e",
            "5-10": "#fe9929",
            "10-20": "#d95f0e",
            f"20-{int(max_upper_range)}": "#993404"
        }

        plt.figure(figsize=(12, 8))
        squarify.plot(sizes=slope['percent'], label=slope['Bin'], 
                      color=[slope_colors.get(bin_label, "#999999") for bin_label in slope['Bin']], 
                      alpha=0.8, pad=True)
        plt.title(f"Slope Distribution in {city_name}")
        plt.axis('off')
        plt.tight_layout()

        render_path_png = f"{local_output_dir}/{city_name_l}_slope_treemap.png"
        plt.savefig(render_path_png, bbox_inches='tight')
        plt.close()
        utils.upload_blob(cloud_bucket, render_path_png, f"{render_dir}/{city_name_l}_slope_treemap.png", type='render')

        fig = px.treemap(
            slope, 
            path=['Bin'],  
            values='percent', 
            color='Bin',
            color_discrete_map=slope_colors, 
            labels={'percent': 'Percentage', 'Slope': 'Slope Range'}
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(t=50, l=25, r=25, b=25),
            font=font_dict
        )
        fig.write_html(render_path_png.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, render_path_png.replace('.png', '.html'), f"{render_dir}/{city_name_l}_slope_treemap.html", type='render')

        max_percent_index = slope['percent'].idxmax()
        highest_percent_row = slope.loc[max_percent_index]
        slope_stats = {'slope_stats': f"The most common slope range in the city is {highest_percent_row['Bin']} degrees, with a {highest_percent_row['percent']:.2f}% frequency."}
        with open(f"{local_output_dir}/{city_name_l}_slope_stats.yml", 'w') as f:
            yaml.dump(slope_stats, f)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_slope_stats.yml", f"{output_dir}/{city_name_l}_slope_stats.yml")
