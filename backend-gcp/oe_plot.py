def check_city_in_oxford(data_bucket, oe_dir, oe_locations_blob, local_data_dir, country, city_name):
    import pandas as pd
    import utils

    utils.download_blob(data_bucket, f'{oe_dir}/{oe_locations_blob}', f'{local_data_dir}/oe_locations.csv', check_exists=True)
    oe_locations = pd.read_csv(f'{local_data_dir}/oe_locations.csv')
    oe_locations_in_country = oe_locations[oe_locations['Country'] == country]
    in_oxford = city_name in oe_locations_in_country['Location'].values

    return in_oxford
    
def find_nearby_countries(local_data_dir, countries_shp_blob, country_name, max_nearby_countries=None):
    import geopandas as gpd
    import pandas as pd

    # Load the world shapefile
    world = gpd.read_file(f"{local_data_dir}/{countries_shp_blob}.shp").to_crs(epsg=4326)

    # Find the country specified by country_name
    target_country = world[world['NAME_EN'] == country_name]

    if target_country.empty:
        raise ValueError(f"Country '{country_name}' not found in the shapefile.")

    # Get the region of the target country
    region = target_country.iloc[0]['WB_REGION']

    # Find nearby countries in the same region that intersect with the target country
    intersecting_countries = world[(world.intersects(target_country)) & (world['WB_REGION'] == region) & (world['NAME_EN'] != country_name)]

    if max_nearby_countries is None:
        # Return all intersecting countries in the same region
        nearby_countries_list = intersecting_countries['NAME_EN'].unique().tolist()
    else:
        # Calculate the centroid of the target country
        target_centroid = target_country.geometry.centroid.iloc[0]

        # Find all countries in the same region, excluding the target country
        all_nearby_countries = world[(world['WB_REGION'] == region) & (world['NAME_EN'] != country_name)]

        # Calculate the distance of each country to the target country
        all_nearby_countries['distance'] = all_nearby_countries.geometry.centroid.distance(target_centroid)

        # Sort all nearby countries by distance
        all_nearby_countries = all_nearby_countries.sort_values(by='distance')

        # Select the top max_nearby_countries, including both intersecting and additional nearby countries
        nearby_countries = pd.concat([intersecting_countries, all_nearby_countries]).drop_duplicates().head(max_nearby_countries)

        # Get the names of the nearby countries
        nearby_countries_list = nearby_countries['NAME_EN'].unique().tolist()

    return nearby_countries_list

def find_benchmark_cities(data_bucket, oe_dir, oe_locations_blob, oegc_blob, countries_shp_blob, local_data_dir, country_name, city_name):
    import pandas as pd
    import utils
    
    utils.download_blob(data_bucket, f'{oe_dir}/{oe_locations_blob}', f'{local_data_dir}/oe_locations.csv', check_exists=True)
    utils.download_blob(data_bucket, f'{oe_dir}/{oegc_blob}', f'{local_data_dir}/oegc.csv', check_exists=True)
    oe_locations = pd.read_csv(f'{local_data_dir}/oe_locations.csv')
    oegc = pd.read_csv(f'{local_data_dir}/oegc.csv')

    def find_nearby_cities(max_nearby_countries):
        nearby_countries = find_nearby_countries(local_data_dir, countries_shp_blob, country_name, max_nearby_countries=max_nearby_countries)
        nearby_cities = oe_locations[
            oe_locations['Country'].str.lower().isin(nearby_countries) &
            (oe_locations['Location'] != city_name) &
            (~oe_locations['Location'].str.contains("Total"))
        ]['Location'].tolist()

        city_pop = get_oe_population(data_bucket, oe_dir, oegc_blob, local_data_dir, city_name)
        bm_cities_df = oegc[
            (oegc['Location'].isin(nearby_cities)) &
            (oegc['Indicator'] == "Total population") &
            (
                (oegc['2021'].between(city_pop * 0.5 / 1000, city_pop * 1.5 / 1000)) |
                (oegc['Country'] == country_name)
            ) &
            (oegc['Location'] != city_name)
        ]

        bm_cities = bm_cities_df['Location'].tolist()

        return bm_cities, len(nearby_countries)
    
    bm_cities, num_nearby_countries = find_nearby_cities(max_nearby_countries=None)
    while len(bm_cities) < 4:
        bm_cities = find_nearby_cities(max_nearby_countries=len(num_nearby_countries) + 1)
    while len(bm_cities) > 12:
        bm_cities = find_nearby_cities(max_nearby_countries=len(num_nearby_countries) - 1)

    return bm_cities

def get_oe_population(data_bucket, oe_dir, oegc_blob, local_data_dir, city_name):
    import pandas as pd
    import utils
    
    utils.download_blob(data_bucket, f'{oe_dir}/{oegc_blob}', f'{local_data_dir}/oegc.csv', check_exists=True)
    oegc = pd.read_csv(f'{local_data_dir}/oegc.csv')

    city_pop = (oegc[(oegc['Location'] == city_name) & 
                            (oegc['Indicator'] == 'Total population')]['2021'] * 1000).values[0]
    
    return city_pop

def plot_oxford_pop_growth(data_bucket, cloud_bucket, oe_dir, oegc_blob, local_data_dir, local_output_dir, city_name, city_name_l, bm_cities, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.express as px
    from adjustText import adjust_text
    import utils

    utils.download_blob(data_bucket, f'{oe_dir}/{oegc_blob}', f'{local_data_dir}/oegc.csv', check_exists=True)
    oxford = pd.read_csv(f'{local_data_dir}/oegc.csv')
    filtered_oxford = oxford[oxford['Location'].isin([city_name] + bm_cities)]

    if len(filtered_oxford) > 0:
        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)

        pop_longitude = filtered_oxford[filtered_oxford['Indicator'] == "Total population"]
        pop_longitude = pop_longitude.melt(id_vars=['Group', 'Location'], value_vars=[col for col in pop_longitude.columns if '20' in col], var_name='Year', value_name='Population')
        pop_longitude['Year'] = pop_longitude['Year'].astype(int)

        pop_longitude['Population'] = pop_longitude['Population'] * 6

        plt.figure(figsize=(8.5, 6))
        
        for location in bm_cities:
            city_data = pop_longitude[pop_longitude['Location'] == location]
            if not city_data.empty:
                plt.plot(city_data['Year'], city_data['Population'], color='grey', linestyle='-', linewidth=1)
        
        city_data = pop_longitude[pop_longitude['Location'] == city_name]
        if not city_data.empty:
            plt.plot(city_data['Year'], city_data['Population'], color='black', linestyle='-', linewidth=2, marker='o')

        plt.title(f"Population of {city_name} and benchmark cities")
        plt.xlabel('Year')
        plt.ylabel('Population')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        texts = []
        for location in [city_name] + bm_cities:
            city_data = pop_longitude[pop_longitude['Location'] == location]
            if not city_data.empty:
                last_point = city_data.iloc[-1]
                texts.append(plt.text(last_point['Year'], last_point['Population'], location,
                                      horizontalalignment='left', bbox=dict(facecolor='white', edgecolor='none', pad=1.0)))
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'))

        plt.tight_layout()
        plt.savefig(f"{render_dir}/{city_name_l}-oxford-pop-plot.png", format='png', dpi=300)
        plt.show()
        
        fig = px.line(pop_longitude, x='Year', y='Population', color='Location')
        for location in bm_cities:
            fig.update_traces(selector=dict(name=location), line=dict(dash='dash'), mode='lines')
        fig.update_traces(selector=dict(name=city_name), line=dict(dash='solid',color='black'), mode='lines')
        fig.update_layout(
            template='plotly_white',
            autosize=True,
            showlegend=False,  
            legend=dict(
                orientation="h", 
                yanchor="bottom",
                y=-0.3, 
                xanchor="center",
                x=0.5,
                title_text='',  
            ),
            xaxis=dict(
                title_text='',
                linecolor='black'  
            ),
            yaxis=dict(
                title_text='',
                range=[0, None],
                linecolor='black'  
            ),
            margin=dict(l=40, r=40, t=80, b=40),
            title=dict(font=dict(size=20, color='black', family="Arial")),
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.write_html(f"{local_output_dir}/{city_name_l}-oxford-pop-plot.html", full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-pop-plot.html", f"{render_dir}/{city_name_l}-oxford-pop-plot.html", type='render')

def get_de_pop_growth(city_name, country_name_l, alternate_city_name):
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup
    import lxml

    url = f'https://www.citypopulation.de/en/{country_name_l}/cities/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    def get_pop(city_name, soup, table_id):
        html_table = soup.find('section', id=table_id).find('table')
        if html_table:
            cities_df = pd.read_html(str(html_table))[0]
            city_pop = cities_df[cities_df['Name'].str.contains(city_name, case=False, na=False)]
            return city_pop
        return pd.DataFrame()

    table_ids = ['citysection', 'largecities', 'adminareas']
    city_pop = pd.DataFrame()

    for table_id in table_ids:
        city_pop = get_pop(city_name, soup, table_id)
        if not city_pop.empty:
            break
    
    if city_pop.empty:
        if alternate_city_name:
            for table_id in table_ids:
                city_pop = get_pop(alternate_city_name, soup, table_id)
                if not city_pop.empty:
                    city_name = alternate_city_name
                    break
    
    if city_pop.empty:
        raise ValueError(f"{city_name} (and alternate name if provided) cannot be found in citypopulation.de. Try manual entry instead.")
    
    cols = city_pop.columns
    pop_cols = cols[cols.str.contains('Population')]
    pop_df = pd.melt(city_pop, id_vars=['Name', 'Area'], value_vars=pop_cols, var_name='Year', value_name='Population')

    pop_df['Year'] = pop_df['Year'].str.extract(r'(\d{4})').astype(int)
    pop_df['Population'] = pop_df['Population'].astype(int)
    pop_df['Source'] = 'citypopulation.de'
    pop_df['Area_km'] = pop_df['Area'].astype(int) / 100
    pop_df = pop_df.rename(columns={'Name': 'Location'})
    pop_df = pop_df[['Location', 'Year', 'Population', 'Area_km', 'Source']]

    pop_df = pop_df.sort_values(by='Year')
    return pop_df

# Population plot CityPopulation.de
def plot_de_population_growth(pop_growth, city_name, city_name_l, cloud_bucket, local_output_dir, render_dir, font_dict):
    import matplotlib.pyplot as plt
    import seaborn as sns
    import plotly.express as px
    from matplotlib.ticker import FuncFormatter
    import utils

    if pop_growth is None or pop_growth.empty:
        raise ValueError("Population growth data is empty or None.")
    
    pop_growth['Year'] = pop_growth['Year'].astype(int)
    pop_min_year = pop_growth['Year'].min()
    pop_max_year = pop_growth['Year'].max()

    breaks = range(pop_min_year, pop_max_year + 1, 5 if pop_max_year - pop_min_year > 15 else 2)

    plt.figure(figsize=(8.5, 6), dpi=300)
    sns.lineplot(data=pop_growth, x='Year', y='Population', marker='o', hue='Location')

    plt.xticks(breaks)
    plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(1))
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x):,}'))
    plt.ylim(0, pop_growth['Population'].max() * 1.1)

    plt.title(f"{city_name} Population Growth, {pop_min_year}-{pop_max_year}")
    plt.xlabel('Year')
    plt.ylabel('Population')
    plt.legend(title='Location')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    legend = plt.gca().get_legend()
    if legend:
        legend.remove()

    plt.savefig(f"{local_output_dir}/{city_name_l}-pop-growth.png", dpi=300, bbox_inches='tight')
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-pop-growth.png", f"{render_dir}/{city_name_l}-pop-growth.png", type='render')

    fig = px.line(
        pop_growth, 
        x='Year', 
        y='Population', 
        color='Location', 
        markers=True, 
        labels={'Year': 'Year', 'Population': 'Population'}
    )
    fig.update_traces(line=dict(color='black'))

    pop_min_year = pop_growth['Year'].min()
    pop_max_year = pop_growth['Year'].max()
    breaks = list(range(pop_min_year, pop_max_year + 1, 5 if pop_max_year - pop_min_year > 15 else 2))

    fig.update_xaxes(
        tickmode='array',
        tickvals=breaks,
        ticktext=[str(year) for year in breaks]
    )
    fig.update_yaxes(
        tickformat=',',
        range=[0, pop_growth['Population'].max()]
    )

    fig.update_layout(
        template='plotly_white',
        autosize=True,
        xaxis_title='',
        yaxis_title='',
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        xaxis=dict(
            linecolor='black'
        ),
        yaxis=dict(
            linecolor='black'
        ),
        showlegend=False,
        font=font_dict,
        plot_bgcolor='white'
    )
    
    fig.write_html(f"{local_output_dir}/{city_name_l}_pop_growth.html",full_html=False, include_plotlyjs='cdn')
    utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_pop_growth.html", f"{render_dir}/{city_name_l}_pop_growth.html", type='render')

def plot_pop_growth(data_bucket, cloud_bucket, oe_dir, oe_locations_blob, oegc_blob, countries_shp_blob, local_data_dir, country_name, country_name_l, city_name, city_name_l, alternate_city_name, local_output_dir, output_dir, render_dir, font_dict):
    import utils

    if check_city_in_oxford(data_bucket, oe_dir, oe_locations_blob, local_data_dir, country_name, city_name):
        bm_cities = find_benchmark_cities(data_bucket, oe_dir, oe_locations_blob, oegc_blob, countries_shp_blob, local_data_dir, country_name, city_name)
        plot_oxford_pop_growth(data_bucket, cloud_bucket, oe_dir, oegc_blob, local_data_dir, local_output_dir, city_name, city_name_l, bm_cities, render_dir, font_dict)
    else:
        pop_growth = get_de_pop_growth(city_name, country_name_l, alternate_city_name)
    
        if pop_growth is not None and not pop_growth.empty:
            pop_growth.to_csv(f"{local_output_dir}/{city_name_l}_pop_growth.csv", index=False)
            utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}_pop_growth.csv", f"{output_dir}/{city_name_l}_pop_growth.csv")
            pop_growth_message = pop_growth[pop_growth['Location'].str.contains(city_name, case=False, na=False)].sort_values(by='Year')
            
            if pop_growth_message.empty:
                print(f"No population growth data found for {city_name} after filtering.")
            else:
                plot_de_population_growth(pop_growth, city_name, city_name_l, cloud_bucket, local_output_dir, render_dir, font_dict)
        else:
            print(f"{city_name} population data could not be retrieved from CityPopulation.de. Try manual entry instead")
