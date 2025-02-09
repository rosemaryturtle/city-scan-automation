def plot_solar(cloud_bucket, local_data_dir, data_bucket, solar_graph_blob, features, city_name_l, local_output_dir, output_dir, render_dir, font_dict):
    import utils
    import rasterio
    from rasterio.mask import mask
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import plotly.express as px
    import yaml
    
    utils.download_blob(data_bucket, solar_graph_blob, f'{local_data_dir}/solar.tif')
    
    monthly_pv = {}

    # Loop through each band in the GeoTIFF
    with rasterio.open(f'{local_data_dir}/solar.tif') as src:
        for band_index in range(1, src.count + 1):  # Bands are 1-indexed in rasterio
            # Mask the raster with the polygon(s)
            masked, _ = mask(src, features, crop=True, all_touched=True, indexes=band_index)
            
            # Flatten the masked array and remove nodata values (masked values)
            masked_data = masked[0]  # Extract the first (and only) layer from masking
            valid_data = masked_data[~np.isnan(masked_data)]  # Remove NaN values
            
            # Calculate the max value for this band
            if valid_data.size > 0:  # Ensure there are valid data points
                max_value = valid_data.max()
            else:
                max_value = None  # No valid data within the polygon
            
            # Store in dictionary with band index as key
            monthly_pv[band_index] = max_value

    # Convert dictionary to DataFrame
    monthly_pv_df = pd.DataFrame(list(monthly_pv.items()), columns=['month', 'max'])
    monthly_pv_df.sort_values(by='month', inplace=True)
    
    highest_value = monthly_pv_df['max'].max()
    lowest_value = monthly_pv_df['max'].min()

    ratio = highest_value / lowest_value

    # Check if the ratio is greater than 2.5
    if ratio > 2.5:
        solar_text = "Seasonality is high, making solar energy available throughout the year"
    else:
        solar_text = "Seasonality is low to moderate, making solar energy available in only some of the months"
    
    with open(f'{local_output_dir}/{city_name_l}_solar.yml', 'w') as f:
        yaml.dump({'soalr_text': solar_text}, f)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_solar.yml', f'{output_dir}/{city_name_l}_solar.yml')

    plt.figure(figsize=(8, 8))
    plt.plot(monthly_pv_df['month'], monthly_pv_df['max'], marker='o', linestyle='-')

    plt.axhline(y=3.5, linestyle='--', color='black')
    plt.text(1, 3.52, 'Favorable Conditions', color='darkgrey', verticalalignment='bottom', horizontalalignment='left')

    plt.axhline(y=4.5, linestyle='--', color='black')
    plt.text(1, 4.52, 'Excellent Conditions', color='darkgrey', verticalalignment='bottom', horizontalalignment='left')

    plt.xlabel('Month')
    plt.ylabel('Daily PV energy yield (kWh/kWp)')
    plt.title('Seasonal availability of solar energy')
    plt.xticks(np.arange(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    plt.grid(True)
    plt.tight_layout()

    render_path = f"{local_output_dir}/{city_name_l}_PV_graph.png"
    plt.savefig(render_path, bbox_inches='tight')
    plt.close()
    utils.upload_blob(cloud_bucket, render_path, f'{render_dir}/{city_name_l}_PV_graph.png', type='render')

    fig = px.line(monthly_pv_df, x='month', y='max', markers=True)
    fig.add_annotation(x=6.5,y=4.6, text='Excellent Conditions', showarrow=False, font=dict(color='darkgrey'),xanchor='center', xref='x')
    fig.add_annotation(x=6.5,y=3.6, text='Favorable Conditions', showarrow=False, font=dict(color='darkgrey'),xanchor='center', xref='x')
    fig.update_xaxes(title='', tickvals=list(range(1, 13)), ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    fig.update_yaxes(title='Daily PV energy yield (kWh/kWp)', range=[0, None])
    fig.add_shape(type="line", x0=1, y0=3.5, x1=12, y1=3.5, line=dict(color="black", width=1, dash='dash'))
    fig.add_shape(type="line", x0=1, y0=4.5, x1=12, y1=4.5, line=dict(color="black", width=1, dash='dash'))
    fig.update_traces(line=dict(color='black'))
    fig.update_layout(xaxis=dict(showgrid=True, zeroline=False,linecolor='black'),yaxis=dict(linecolor='black'),template='plotly_white',autosize=True,font=font_dict,plot_bgcolor='white')
    fig.write_html(render_path.replace('.png', '.html'),full_html=False, include_plotlyjs='cdn')
    utils.upload_blob(cloud_bucket, render_path.replace('.png', '.html'), f'{render_dir}/{city_name_l}_PV_graph.html', type='render')
