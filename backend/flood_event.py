def plot_flood_event(data_bucket, cloud_bucket, flood_archive_dir, flood_archive_blob, features, local_data_dir, local_output_dir, city_name_l, output_dir, render_dir, font_dict):
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pandas as pd
    import plotly.express as px
    import yaml
    import utils
    
    for f in [f'{flood_archive_blob}.{suf}' for suf in ['dbf', 'prj', 'shp', 'shx']]:
        utils.download_blob(data_bucket, f'{flood_archive_dir}/{f}', f'{local_data_dir}/{f}')
    flood_archive = gpd.read_file(f'{local_data_dir}/{flood_archive_blob}.shp')
    flood_archive = flood_archive[flood_archive.is_valid]
    aoi = features.to_crs(flood_archive.crs)
    flood_archive = flood_archive[flood_archive.intersects(aoi.unary_union)]

    floods = flood_archive[['BEGAN', 'ENDED', 'DEAD', 'DISPLACED', 'MAINCAUSE', 'SEVERITY']]

    flood_event_stats = floods.agg({'DEAD': 'sum', 'DISPLACED': 'sum', 'BEGAN': 'count'})

    with open(f'{local_output_dir}/{city_name_l}_flood_events.yml', 'w') as f:
        yaml.dump({'flood_text': f"The {flood_event_stats['BEGAN']} flood event{'s' if flood_event_stats['BEGAN'] > 1 else ''} displaced {flood_event_stats['DISPLACED']} and killed {flood_event_stats['DEAD']}."}, f)
    utils.upload_blob(cloud_bucket, f'{local_output_dir}/{city_name_l}_flood_events.yml', f'{output_dir}/{city_name_l}_flood_events.yml')

    floods['BEGAN'] = pd.to_datetime(floods['BEGAN'])
    floods['Year'] = floods['BEGAN'].dt.year
    floods['Month'] = floods['BEGAN'].dt.month_name()

    severity_mapping = {
        1: 'Large event',
        1.5: 'Very large event',
        2: 'Extreme event'
    }
    floods['Severity'] = floods['SEVERITY'].map(severity_mapping)
    floods['text'] = floods.apply(
        lambda row: f"{row['BEGAN'].strftime('%Y-%m-%d')}, {row['Severity'].lower()} {row['MAINCAUSE']}, "
                    f"{row['DEAD']:,} fatalities, {row['DISPLACED']:,} displaced",
        axis=1
    )

    floods['Month'] = pd.Categorical(floods['Month'], 
                                    categories=['January', 'February', 'March', 'April', 'May', 'June', 
                                                'July', 'August', 'September', 'October', 'November', 'December'], 
                                    ordered=True)

    fig = px.scatter(
        floods,
        x='Year',
        y='Month',
        size='DISPLACED',
        color='Severity',
        size_max=60,
        category_orders={'Month': ['January', 'February', 'March', 'April', 'May', 'June', 
                                   'July', 'August', 'September', 'October', 'November', 'December']},
        color_discrete_map={
            'Large event': 'lightblue',
            'Very large event': 'blue',
            'Extreme event': 'darkblue'
        },
        labels={'DEAD': 'Fatalities', 'Year': 'Year', 'DISPLACED': 'Displaced', 'Month': 'Month'}
    )

    fig.update_layout(
        template='plotly_white',
        autosize=True,
        xaxis_title='',
        yaxis_title='',
        xaxis=dict(
            linecolor='black'  
        ),       
        yaxis=dict(
            type='category', 
            categoryorder='array', 
            categoryarray=['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December'],
            tickvals=['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December'],
            linecolor='black'
        ),
        coloraxis_colorbar=dict(title='Severity'),
        font=font_dict,
        showlegend=False,
        plot_bgcolor='white'  
    )

    render_path_html = f"{local_output_dir}/{city_name_l}_flood_timeline.html"
    fig.write_html(render_path_html, full_html=False, include_plotlyjs='cdn')
    utils.upload_blob(cloud_bucket, render_path_html, f'{render_dir}/{city_name_l}_flood_timeline.html', type='render')

    plt.figure(figsize=(12.5, 6))
    colors = {
        'Large event': 'lightblue',
        'Very large event': 'blue',
        'Extreme event': 'darkblue'
    }
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    for severity, color in colors.items():
        subset = floods[floods['Severity'] == severity]
        plt.scatter(subset['Year'], subset['Month'].map(lambda x: month_order.index(x) + 1), 
                    s=subset['DISPLACED']/10000, c=color, label=severity, alpha=0.6, edgecolors='w', linewidth=0.5)
    
    plt.yticks(ticks=range(1, 13), labels=month_order)
    plt.title('Flood Events Timeline')
    plt.xlabel('Year')
    plt.ylabel('Month')
    plt.legend(title='Severity')
    plt.grid(True)
    render_path_matplotlib = f"{local_output_dir}/{city_name_l}_flood_timeline.png"
    plt.savefig(render_path_matplotlib)
    plt.close()
    utils.upload_blob(cloud_bucket, render_path_matplotlib, f'{render_dir}/{city_name_l}_flood_timeline.png', type='render')
