def get_earthquake_data():
    import requests
    from datetime import datetime
    import pandas as pd

    url = "http://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"
    response = requests.get(url, params={"minYear": 1900, "maxYear": datetime.now().year})
    response.raise_for_status()  # Check if the request was successful
    eq_json = response.json()
    eq = pd.json_normalize(eq_json, record_path=['items'])
    return eq

def plot_earthquake_event(features, city_name_l, local_output_dir, cloud_bucket, output_dir, render_dir, font_dict):
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import numpy as np
    import plotly.graph_objects as go
    from shapely.geometry import Point
    import pandas as pd
    import utils
    
    damages = {
        "0": "None",
        "1": "Limited",
        "2": "Moderate",
        "3": "Severe",
        "4": "Extreme"
    }

    severity_colors = {
        "Low": "#ff9999",
        "Moderate": "#ff4d4d",
        "High": "#cc0000"
    }

    eq = get_earthquake_data()

    city_point = features.unary_union.centroid

    eq_near = eq.dropna(subset=['latitude', 'longitude'])
    eq_near['geometry'] = eq_near.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
    eq_near = gpd.GeoDataFrame(eq_near, geometry='geometry', crs='EPSG:4326')

    eq_near = eq_near.to_crs("EPSG:3857")
    city_point = gpd.GeoSeries([city_point], crs="EPSG:4326").to_crs("EPSG:3857").iloc[0]

    eq_near['distance'] = eq_near.geometry.distance(city_point) / 1000  
    eq_near['magXdist'] = eq_near['eqMagnitude'] * (2000 - eq_near['distance'])

    eq_near['damageAmountOrder'] = eq_near['damageAmountOrder'].fillna(0).astype(int)
    eq_near['damageMillionsDollars'] = eq_near['damageMillionsDollars'].fillna(0).astype(float)
    eq_near['deaths'] = eq_near['deaths'].fillna(0).astype(int)
    eq_near['deathsAmountOrder'] = eq_near['deathsAmountOrder'].fillna(0).astype(int)
    eq_near['eqMagnitude'] = eq_near['eqMagnitude'].fillna(0).astype(float)
    eq_near['intensity'] = eq_near['intensity'].fillna(0).astype(int)

    conditions = (
        (eq_near['damageAmountOrder'] >= 2) |
        (eq_near['damageMillionsDollars'] >= 1) |
        (eq_near['deaths'] >= 10) |
        (eq_near['deathsAmountOrder'] >= 2) |
        (eq_near['eqMagnitude'] >= 7.5) |
        (eq_near['intensity'] >= 10) |
        (~eq_near['tsunamiEventId'].isna())
    )

    eq_near = eq_near[conditions & (eq_near['distance'] < 500)]

    eq_text = eq_near.copy()
    if 'locationName' in eq_text.columns:
        eq_text['locationName'] = eq_text['locationName'].astype(str)
        eq_text['location'] = eq_text['locationName'].str.extract(r"([^:][\s]+.*)", expand=False).str.strip()
    else:
        eq_text['location'] = ""

    eq_text['fatalities'] = eq_text['deaths'].apply(lambda x: f"{int(x):,} fatalities" if pd.notna(x) else "")
    eq_text['fatalities'] = eq_text['fatalities'].str.replace("1 fatalities", "1 fatality")
    eq_text['fatalities'] = eq_text['fatalities'].str.replace("NA fatalities", "")
    eq_text['damage'] = eq_text['damageAmountOrder'].apply(lambda x: damages.get(str(int(x)), "Unknown") + " damage")
    eq_text['day'] = eq_text['day'].fillna(1).astype(int)
    eq_text['BEGAN'] = pd.to_datetime(eq_text[['year', 'month', 'day']])

    eq_text = eq_text.sort_values(by='BEGAN')
    eq_text['line1'] = eq_text['BEGAN'].dt.strftime('%B %Y').str.upper()
    eq_text['line2'] = eq_text.apply(lambda row: f"{row['eqMagnitude']}-magnitude; {int(row['distance']):,} km away", axis=1)
    eq_text['line3'] = eq_text['damage']
    eq_text['line4'] = eq_text['fatalities']
    eq_text['text'] = eq_text.apply(lambda row: f"{row['line1']}\n{row['line2']}\n{row['line3']}\n{row['line4']}", axis=1)
    eq_text['above_line'] = (2 * (np.arange(len(eq_text)) % 2) - 1) * -1

    eq_text_select = eq_text.nlargest(10, 'magXdist').sort_values(by='BEGAN')

    eq_text_select['severity_color'] = eq_text_select['damageAmountOrder'].apply(lambda x: severity_colors.get(str(int(x)), 'black'))

    plt.figure(figsize=(12.5, 6))
    scatter = plt.scatter(eq_text_select['distance'], eq_text_select['BEGAN'].dt.year, s=eq_text_select['eqMagnitude'] * 100, alpha=0.6, c=eq_text_select['severity_color'], edgecolors="w", linewidth=0.5)
    for _, row in eq_text_select.iterrows():
        plt.text(row['distance'] + 0.1, row['BEGAN'].year + 0.1, row['text'], fontsize=8, ha='left')
    plt.xlabel('Distance from the City (km)')
    plt.ylabel('Year')
    plt.title('Significant Earthquakes within 500 km of the city since 1900')
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.tight_layout()
    render_path = f"{local_output_dir}/{city_name_l}_earthquake_timeline.png"
    plt.savefig(render_path, bbox_inches='tight')
    utils.upload_blob(cloud_bucket, render_path, f'{render_dir}/{city_name_l}_earthquake_timeline.png', type='render')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
    x=eq_text_select['distance'],
    y=eq_text_select['BEGAN'].dt.year,
    marker=dict(
        size=eq_text_select['eqMagnitude'] * 10,
        color=eq_text_select['damageAmountOrder'],
        colorscale=['#ff9999', '#ff4d4d', '#cc0000'],
        showscale=True
    ),
    text=eq_text_select['text'],  
    hoverinfo='text', 
    textposition='top center'
    ))

    fig.update_layout(
        template='plotly_white',
        xaxis=dict(
            title='Distance from the City (km)',
            linecolor='black', 
            titlefont=font_dict
        ),
        autosize=True,
        yaxis=dict(
            title='',
            tickmode='linear',  
            dtick=1,
            linecolor='black',
            titlefont=font_dict
        ),
        font=font_dict,
        showlegend=False,
        plot_bgcolor='white'  
    )
    fig.write_html(render_path.replace('.png', '.html'), full_html=False, include_plotlyjs='cdn')
    utils.upload_blob(cloud_bucket, render_path.replace('.png', '.html'), f'{render_dir}/{city_name_l}_earthquake_timeline.html', type='render')
