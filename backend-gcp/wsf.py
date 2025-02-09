def wsf(aoi_file, local_data_dir, data_bucket, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict):
    import raster_pro
    import math
    import csv
    import utils
    import os
    import rasterio

    local_wsf_folder = f'{local_data_dir}/wsf'
    os.makedirs(local_wsf_folder, exist_ok=True)
    aoi_bounds = aoi_file.bounds

    wsf_file_list = []
    for i in range(len(aoi_bounds)):
        for x in range(math.floor(aoi_bounds.minx[i] - aoi_bounds.minx[i] % 2), math.ceil(aoi_bounds.maxx[i]), 2):
            for y in range(math.floor(aoi_bounds.miny[i] - aoi_bounds.miny[i] % 2), math.ceil(aoi_bounds.maxy[i]), 2):
                wsf_file_list.append(f'WSFevolution_v1_{x}_{y}')

    wsf_download_list = [f'https://download.geoservice.dlr.de/WSF_EVO/files/{f}/{f}.tif' for f in wsf_file_list]

    downloaded_list = raster_pro.download_raster(wsf_download_list, local_wsf_folder, data_bucket, data_bucket_dir='WSFevolution')
    raster_pro.mosaic_raster(downloaded_list, local_wsf_folder, f'{city_name_l}_wsf_evolution.tif')
    out_image, out_meta = raster_pro.raster_mask_file(f'{local_wsf_folder}/{city_name_l}_wsf_evolution.tif', aoi_file.geometry)
    out_meta.update({"nodata": 0})
    with rasterio.open(f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', "w", **out_meta) as dest:
        dest.write(out_image)

    raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', dst_crs=utils.find_utm(aoi_file))
    area_dict = raster_pro.calculate_raster_area(f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', range(1985, 2016))
    # Calculate the cumulative built-up area
    cumulative_area = 0
    cumulative_dict = {}
    for year, area in sorted(area_dict.items()):
        area = area/1e6
        cumulative_area += area
        cumulative_dict[year] = cumulative_area

    # Write the cumulative data to a CSV file
    with open(f'{local_output_dir}/{city_name_l}_wsf_stats.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["year", "cumulative sq km"])
        for year, cumulative_area in cumulative_dict.items():
            writer.writerow([year, cumulative_area])

    raster_pro.reproject_raster(f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', f'{local_output_dir}/{city_name_l}_wsf_evolution_3857.tif', dst_crs='epsg:3857')

    plot_wsf_stats(cloud_bucket, local_output_dir, output_dir, city_name_l, render_dir, font_dict)

    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_evolution.tif', f'{output_dir}/{city_name_l}_wsf_evolution.tif')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_evolution_utm.tif', f'{output_dir}/{city_name_l}_wsf_evolution_utm.tif')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_stats.csv', f'{output_dir}/{city_name_l}_wsf_stats.csv')
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_evolution_3857.tif', f'{output_dir}/{city_name_l}_wsf_evolution_3857.tif')

def plot_wsf_stats(cloud_bucket, local_output_dir, output_dir, city_name_l, render_dir, font_dict):
    from os.path import exists

    wsf_stats_file = f"{local_output_dir}/{city_name_l}_wsf_stats.csv"
    if exists(wsf_stats_file):
        import pandas as pd
        import matplotlib.pyplot as plt
        import plotly.graph_objects as go
        import utils
        import yaml

        wsf = pd.read_csv(wsf_stats_file)
        
        wsf = wsf.rename(columns={'year': 'Year'}).\
        loc[:, ['Year', 'cumulative sq km']].\
        rename(columns={'cumulative sq km': 'uba_km2'})

        wsf['growth_pct'] = (wsf['uba_km2'] / wsf['uba_km2'].shift(1) - 1)
        wsf['growth_km2'] = wsf['uba_km2'] - wsf['uba_km2'].shift(1)

        plt.figure(figsize=(4, 4))
        plt.plot(wsf['Year'], wsf['uba_km2'], marker='o', linestyle='-')
        plt.title("Urban Built-up Area, 1985-2015")
        plt.xlabel("Year")
        plt.ylabel("Urban built-up area (sq. km)")
        plt.grid(True)
        render_path = f"{local_output_dir}/{city_name_l}_urban_built_up_area.png"
        plt.savefig(render_path,bbox_inches='tight')
        plt.close()
        utils.upload_blob(cloud_bucket, render_path, f'{render_dir}/{city_name_l}_urban_built_up_area.png', type='render')

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=wsf['Year'],
            y=wsf['uba_km2'],
            mode='lines+markers',
            name='Urban built-up area (sq. km)',
            line=dict(color='black')
        ))

        fig.update_layout(
            xaxis_title="",
            yaxis_title="Urban built-up area in sq. km",
            template='plotly_white',
            showlegend=False,
            autosize=True,
            hovermode='x',
            yaxis=dict(
            range=[0, None],
            linecolor='black'  # Ensures that the Y-axis starts at 0 )
        ),
        xaxis=dict(
                linecolor='black'  
            ),
        font=font_dict,
        plot_bgcolor='white'  
        )
        fig.show()
        fig.write_html(render_path.replace('.png', '.html'),full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, render_path.replace('.png', '.html'), f'{render_dir}/{city_name_l}_urban_built_up_area.html', type='render')
        first_area = wsf['uba_km2'].iloc[0]
        latest_area = wsf['uba_km2'].iloc[-1]
        first_year = wsf['Year'].iloc[0]
        latest_year = wsf['Year'].iloc[-1]
        pct_growth = 100 * (latest_area - first_area) / first_area
        wsf_stats = {'wsf_stats': f"The city's built-up area grew from {round(first_area, 2)} sq. km in {first_year} to {round(latest_area, 2)} in {latest_year} for {round(pct_growth, 2)}% growth"}
        with open(f'{local_output_dir}/{city_name_l}_wsf_stats.yml', 'w') as f:
            yaml.dump(wsf_stats, f)
        utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_wsf_stats.yml', f'{output_dir}/{city_name_l}_wsf_stats.yml')