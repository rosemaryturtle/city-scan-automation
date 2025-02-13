def check_city_in_oxford(oe_locations, country, city_name):
    oe_locations_in_country = oe_locations[oe_locations['Country'] == country]
    in_oxford = city_name in oe_locations_in_country['Location'].values

    return in_oxford
    
def find_nearby_countries(local_data_dir, countries_shp_blob, country_name, max_nearby_countries=3):
    import geopandas as gpd
    # import pandas as pd

    # Load the world shapefile
    world = gpd.read_file(f"{local_data_dir}/{countries_shp_blob}.shp").to_crs(epsg=3857)

    # Find the country specified by country_name
    target_country = world[world['NAME_EN'] == country_name]

    if target_country.empty:
        raise ValueError(f"Country '{country_name}' not found in the shapefile.")

    # Get the region of the target country
    region = target_country.iloc[0]['WB_REGION']

    # Get how many countries are in the same region
    num_regional_countries = len(world[world['WB_REGION'] == region])

    # Find nearby countries in the same region that intersect with the target country
    # intersecting_countries = world[(world.intersects(target_country)) & (world['WB_REGION'] == region) & (world['NAME_EN'] != country_name)]

    # if max_nearby_countries is None:
    #     # Return all intersecting countries in the same region
    #     nearby_countries_list = intersecting_countries['NAME_EN'].unique().tolist()
    # else:
    # Calculate the centroid of the target country
    target_centroid = target_country.geometry.centroid.iloc[0]

    # Find all countries in the same region, excluding the target country
    all_nearby_countries = world[(world['WB_REGION'] == region) & (world['NAME_EN'] != country_name)].copy()

    # Calculate the distance of each country to the target country
    all_nearby_countries['distance'] = all_nearby_countries.geometry.centroid.distance(target_centroid)

    # Sort all nearby countries by distance
    all_nearby_countries = all_nearby_countries.sort_values(by='distance').drop_duplicates().head(max_nearby_countries)

    # Get the names of the nearby countries
    nearby_countries_list = all_nearby_countries['NAME_EN'].unique().tolist()

    return nearby_countries_list, num_regional_countries

def find_benchmark_cities(oe_locations, oegc, countries_shp_blob, local_data_dir, country_name, city_name):
    def find_nearby_cities(max_nearby_countries, pop_threshold):
        nearby_countries, num_regional_countries = find_nearby_countries(local_data_dir, countries_shp_blob, country_name, max_nearby_countries=max_nearby_countries)
        nearby_cities = oe_locations[
            oe_locations['Country'].isin(nearby_countries + [country_name]) &
            (oe_locations['Location'] != city_name) &
            (~oe_locations['Location'].str.contains("Total"))
        ]['Location'].tolist()

        city_pop = get_oe_population(oegc, city_name)
        bm_cities_df = oegc[
            (oegc['Location'].isin(nearby_cities)) &
            (oegc['Indicator'] == "Total population") &
            (
                (oegc['2021'].between(city_pop * (1-pop_threshold) / 1000, city_pop * (1+pop_threshold) / 1000)) |
                (oegc['Country'] == country_name)
            ) &
            (oegc['Location'] != city_name)
        ]

        bm_cities = bm_cities_df['Location'].tolist()
        bm_cities_countries = bm_cities_df['Country'].tolist()

        return bm_cities, bm_cities_countries, len(nearby_countries), num_regional_countries
    
    pop_threshold = 0.5
    bm_cities, bm_cities_countries, num_nearby_countries, num_regional_countries = find_nearby_cities(max_nearby_countries=None, pop_threshold=pop_threshold)
    while (len(bm_cities) < 4) & (num_nearby_countries < num_regional_countries-1):
        print('Not enough benchmark cities found. Increasing the number of nearby countries.')
        bm_cities, bm_cities_countries, num_nearby_countries, num_regional_countries = find_nearby_cities(max_nearby_countries=num_nearby_countries + 1, pop_threshold=pop_threshold)
        print(bm_cities, bm_cities_countries, num_nearby_countries, num_regional_countries)
    if len(bm_cities) > 12:
        print('Too many benchmark cities found. Narrowing population range.')
        pop_threshold -= 0.1
        bm_cities, bm_cities_countries, num_nearby_countries, num_regional_countries = find_nearby_cities(max_nearby_countries=None, pop_threshold=pop_threshold)

    return bm_cities, bm_cities_countries

def get_oe_population(oegc, city_name):
    city_pop = (oegc[(oegc['Location'] == city_name) & 
                            (oegc['Indicator'] == 'Total population')]['2021'] * 1000).values[0]
    
    return city_pop

def plot_oegc_pop_growth(cloud_bucket, oegc, local_output_dir, city_name, city_name_l, bm_cities, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.express as px
    from adjustText import adjust_text
    import utils

    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]

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
        plt.savefig(f"{local_output_dir}/{city_name_l}-oxford-pop-plot.png", format='png', dpi=300)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-pop-plot.png", f"{render_dir}/{city_name_l}-oxford-pop-plot.png", type='render')
        
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

def plot_national_shares(cloud_bucket, oegc, city_name, city_name_l, bm_cities, bm_cities_countries, local_output_dir, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import plotly.express as px
    import matplotlib.pyplot as plt
    import seaborn as sns
    import utils

    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]
    bm_cities_countries_total = [country + ' - Total' for country in bm_cities_countries]
    oxford_countries = oegc[(oegc['Country'].isin(bm_cities_countries)) & (oegc['Location'].isin(bm_cities_countries + bm_cities_countries_total))]

    if len(filtered_oxford) > 0:
        extra_inds = ["Total population", "Employment - Total", "GDP, real, US$ - Total"]

        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)

        oxford_filtered = filtered_oxford[filtered_oxford['Indicator'].isin(extra_inds)].drop_duplicates(subset=['Group', 'Location', 'Country', 'Indicator'])
        oxford_countries_filtered = oxford_countries[oxford_countries['Indicator'].isin(extra_inds)].drop_duplicates(subset=['Country', 'Indicator'])

        oxford_wide = oxford_filtered.pivot(index=['Group', 'Location', 'Country'], columns='Indicator', values='2021').reset_index()
        oxford_countries_wide = oxford_countries_filtered.pivot(index='Country', columns='Indicator', values='2021').reset_index()
        national_shares = pd.merge(oxford_wide, oxford_countries_wide, on='Country', suffixes=('', '_national'))
        print(national_shares)
        national_shares['Population Share'] = national_shares['Total population'] / national_shares['Total population_national']
        national_shares['GDP Share'] = national_shares['GDP, real, US$ - Total'] / national_shares['GDP, real, US$ - Total_national']
        national_shares['Employment Share'] = national_shares['Employment - Total'] / national_shares['Employment - Total_national']
        national_shares = national_shares[['Group', 'Location', 'Population Share', 'GDP Share', 'Employment Share']]
        national_shares = national_shares.sort_values(by=['Group', 'Population Share'], ascending=[False, False])
        national_shares['Location'] = pd.Categorical(national_shares['Location'], categories=national_shares['Location'].unique(), ordered=True)

        national_shares_long = national_shares.melt(id_vars=['Group', 'Location'], 
                                                    value_vars=['Population Share', 'GDP Share', 'Employment Share'], 
                                                    var_name='Indicator', value_name='Percentage')
        national_shares_long['Indicator'] = pd.Categorical(national_shares_long['Indicator'], 
                                                            categories=['GDP Share', 'Employment Share', 'Population Share'], 
                                                            ordered=True)
        fig = px.bar(national_shares_long, x='Percentage', y='Location', color='Indicator', barmode='group',
                     labels={'Percentage': 'Percentage', 'Location': 'City'})

        fig.update_layout(
            xaxis=dict(
                tickformat='.0%',
                dtick=0.05,
                range=[0, round(national_shares[['Population Share', 'GDP Share', 'Employment Share']].max().max(), 1)],
                title_text='',
                tickfont=dict(size=12, color='black', family="Arial"),
                linecolor='black'
            ),
            yaxis=dict(
                title_text='',
                linecolor='black'
            ),
            template='plotly_white',
            showlegend=False,
            margin=dict(l=40, r=40, t=80, b=40),
            title=dict(font=dict(size=20, color='black', family="Arial")),
            autosize=True,
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.update_yaxes(categoryorder='total ascending')
        file_path_html = f"{local_output_dir}/{city_name_l}-national-shares.html"
        fig.write_html(file_path_html,full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, file_path_html, f"{render_dir}/{city_name_l}-national-shares.html", type='render')

        plt.figure(figsize=(8.5, 6))
        sns.barplot(data=national_shares_long, x='Percentage', y='Location', hue='Indicator', dodge=True)
        plt.title("Cities' shares of national population, employment & GDP")
        plt.xlabel('Percentage')
        plt.ylabel('City')
        plt.legend(title='', loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3)
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        file_path_png = f"{local_output_dir}/{city_name_l}-national-shares.png"
        plt.savefig(file_path_png, format='png', dpi=300)
        utils.upload_blob(cloud_bucket, file_path_png, f"{render_dir}/{city_name_l}-national-shares.png", type='render')

def plot_emp_growth(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.express as px
    from adjustText import adjust_text
    import utils

    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]

    if len(filtered_oxford) > 0:
        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)
        emp_longitude = filtered_oxford[filtered_oxford['Indicator'].isin(["Employment - Total"])]
        emp_longitude = emp_longitude.melt(id_vars=['Group', 'Location', 'Country', 'Indicator'], value_vars=[col for col in emp_longitude.columns if col.isdigit()], var_name='Year', value_name='Value')
        emp_longitude = emp_longitude.pivot_table(values='Value', index=['Group', 'Location', 'Country', 'Year'], columns='Indicator').reset_index()
        emp_longitude['Year'] = emp_longitude['Year'].astype(int)
        emp_longitude['Total employed'] = emp_longitude['Employment - Total'] * 1000
        emp_longitude = emp_longitude[emp_longitude['Year'] <= 2021].dropna(subset=['Total employed'])
        plt.figure(figsize=(8.5, 6))
        for location in bm_cities:
            city_data = emp_longitude[emp_longitude['Location'] == location]
            if not city_data.empty:
                plt.plot(city_data['Year'], city_data['Total employed'], color='grey', linestyle='-', linewidth=1)
        
        city_data = emp_longitude[emp_longitude['Location'] == city_name]
        if not city_data.empty:
            plt.plot(city_data['Year'], city_data['Total employed'], color='black', linestyle='-', linewidth=2, marker='o')

        plt.title(f"Employment of {city_name} and benchmark cities")
        plt.xlabel('Year')
        plt.ylabel('Total employed')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)

        texts = []
        for location in [city_name] + bm_cities:
            city_data = emp_longitude[emp_longitude['Location'] == location]
            if not city_data.empty:
                last_point = city_data.iloc[-1]
                texts.append(plt.text(last_point['Year'], last_point['Total employed'], location,
                                      horizontalalignment='left', bbox=dict(facecolor='white', edgecolor='none', pad=1.0)))

        adjust_text(texts, arrowprops=dict(arrowstyle='-', color='red'))
        plt.tight_layout()
        plt.savefig(f"{local_output_dir}/{city_name_l}-oxford-emp-plot.png", format='png', dpi=300)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-emp-plot.png", f"{render_dir}/{city_name_l}-oxford-emp-plot.png", type='render')

        fig = px.line(emp_longitude, x='Year', y='Total employed', color='Location')

        for location in bm_cities:
            fig.update_traces(selector=dict(name=location), line=dict(dash='dash', width=1), mode='lines')
        fig.update_traces(selector=dict(name=city_name), line=dict(dash='solid', color='black', width=2), mode='lines')
        fig.update_layout(
            template='plotly_white',
            autosize=True,
            showlegend=False,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                title_text='',
                linecolor='black'  
            ),
            yaxis=dict(
                title_text='',
                linecolor='black'  
            ),
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.write_html(f"{local_output_dir}/{city_name_l}-oxford-emp-plot.html", full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-emp-plot.html", f"{render_dir}/{city_name_l}-oxford-emp-plot.html", type='render')

def plot_gdp_growth(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from adjustText import adjust_text
    import plotly.express as px
    import utils

    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]

    if len(filtered_oxford) > 0:
        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)

        gdp_longitude = filtered_oxford[filtered_oxford['Indicator'] == "GDP, real, US$ - Total"]

        value_vars = [col for col in gdp_longitude.columns if col.isdigit()]
        if not value_vars:
            raise ValueError("No valid year columns found for melting.")
        
        gdp_longitude = gdp_longitude.melt(id_vars=['Group', 'Location', 'Country', 'Indicator'], 
                                           value_vars=value_vars, 
                                           var_name='Year', value_name='Value')
        

        gdp_longitude = gdp_longitude.pivot_table(values='Value', index=['Group', 'Location', 'Country', 'Year'], 
                                                  columns='Indicator').reset_index()
        gdp_longitude['Year'] = gdp_longitude['Year'].astype(int)
        gdp_longitude['GDP'] = gdp_longitude['GDP, real, US$ - Total'] * 1e6
        gdp_longitude = gdp_longitude[gdp_longitude['Year'] <= 2021].dropna(subset=['GDP'])

        plt.figure(figsize=(8.5, 6))

        for location in bm_cities:
            city_data = gdp_longitude[gdp_longitude['Location'] == location]
            if not city_data.empty:
                plt.plot(city_data['Year'], city_data['GDP'], color='grey', linestyle='-', linewidth=1)

        city_data = gdp_longitude[gdp_longitude['Location'] == city_name]
        if not city_data.empty:
            plt.plot(city_data['Year'], city_data['GDP'], color='black', linestyle='-', linewidth=2, marker='o')

        plt.title(f"GDP of {city_name} and benchmark cities")
        plt.xlabel('Year')
        plt.ylabel('GDP')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)

        texts = []
        for location in [city_name] + bm_cities:
            city_data = gdp_longitude[gdp_longitude['Location'] == location]
            if not city_data.empty:
                last_point = city_data.iloc[-1]
                texts.append(plt.text(last_point['Year'], last_point['GDP'], location,
                                      horizontalalignment='left', bbox=dict(facecolor='white', edgecolor='none', pad=1.0)))

        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'))

        plt.tight_layout()
        plt.savefig(f"{local_output_dir}/{city_name_l}-oxford-gdp-plot.png", format='png', dpi=300)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-gdp-plot.png", f"{render_dir}/{city_name_l}-oxford-gdp-plot.png", type='render')

        fig = px.line(gdp_longitude, x='Year', y='GDP', color='Location')

        for location in bm_cities:
            fig.update_traces(selector=dict(name=location), line=dict(dash='dash', width=1), mode='lines')
        fig.update_traces(selector=dict(name=city_name), line=dict(dash='solid', color='black', width=2), mode='lines')

        fig.update_layout(
            template='plotly_white',
            autosize=True,
            showlegend=False,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            xaxis=dict(
                title_text='',
                linecolor='black'  
            ),
            yaxis=dict(
                title_text='',
                linecolor='black'  
            ),
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.write_html(f"{local_output_dir}/{city_name_l}-oxford-gdp-plot.html", full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-gdp-plot.html", f"{render_dir}/{city_name_l}-oxford-gdp-plot.html", type='render')

def plot_emp_gva_shares(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.express as px
    import plotly.graph_objects as go
    import utils
    
    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]
    indicators = oegc[['Indicator']].drop_duplicates()
    emp_inds = indicators['Indicator'][indicators['Indicator'].str.contains("Employment")].tolist()
    gva_inds = indicators['Indicator'][indicators['Indicator'].str.lower().str.contains("gross value added, real, us")].tolist()

    if len(filtered_oxford) > 0:
        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)
        emp_shares = filtered_oxford[filtered_oxford['Indicator'].isin(emp_inds) & (filtered_oxford['Indicator'] != "Employment - Total")]
        emp_shares = emp_shares[['Group', 'Location', 'Indicator', '2021']].rename(columns={'2021': 'Value'})
        emp_shares['Indicator'] = emp_shares['Indicator'].str.replace("Employment - ", "").str.replace("Transport, storage, information & communication services", "Transport & ICT")
        emp_shares['Share'] = emp_shares.groupby(['Location', 'Group'])['Value'].transform(lambda x: x / x.sum())

        emp_shares2 = emp_shares.groupby(['Group', 'Indicator']).agg({'Share': 'median'}).reset_index().sort_values(by=['Group', 'Share'], ascending=[False, False])
        
        sector_order = emp_shares2[emp_shares2['Group'] == city_name]['Indicator'].unique()
        sector_order = list(sector_order[sector_order != "Other"]) + ["Other"]
        
        emp_shares['Indicator'] = pd.Categorical(emp_shares['Indicator'], categories=sector_order, ordered=True)
        emp_shares = emp_shares.sort_values(by='Indicator')
        
        emp_shares2['Indicator'] = pd.Categorical(emp_shares2['Indicator'], categories=sector_order, ordered=True)
        emp_shares2 = emp_shares2.sort_values(by='Indicator')
        emp_shares2['Share'] = np.where((emp_shares2['Indicator'] == "Other") & (emp_shares2['Group'] == "Benchmark"), emp_shares2['Share'] * 2 / 6, emp_shares2['Share'])

        gva_shares = filtered_oxford[filtered_oxford['Indicator'].isin(gva_inds) & ~filtered_oxford['Indicator'].str.contains("Total")]
        gva_shares = gva_shares[['Group', 'Location', 'Indicator', '2021']].rename(columns={'2021': 'Value'})
        gva_shares['Indicator'] = gva_shares['Indicator'].str.replace("Gross value added, real, US$ -", "").str.replace("Transport, storage, information & communication services", "Transport & ICT")
        gva_shares['Indicator'] = gva_shares['Indicator'].str.replace(".*- ", "").str.replace("Transport, storage, information & communication services", "Transport & ICT")
        gva_shares['Share'] = gva_shares.groupby(['Location', 'Group'])['Value'].transform(lambda x: x / x.sum())
        gva_shares['Indicator'] = pd.Categorical(gva_shares['Indicator'], categories=sector_order, ordered=True)

        ylims_shares = (0, np.ceil(max(emp_shares['Share'].max(), gva_shares['Share'].max()) * 10) / 10)
        plt.figure(figsize=(12.5, 6))
        for group in emp_shares2['Group'].unique():
            data = emp_shares2[emp_shares2['Group'] == group]
            plt.bar(data['Indicator'], data['Share'], label=group, alpha=0.7)

        for location in emp_shares[emp_shares['Location'] != city_name]['Location'].unique():
            location_data = emp_shares[emp_shares['Location'] == location]
            plt.plot(location_data['Indicator'], location_data['Share'], 'o', color='darkgrey')

        plt.title(f"Share of employment by sector in {city_name} and median benchmark city")
        plt.xlabel("Sector")
        plt.ylabel("Share")
        plt.ylim(ylims_shares)
        plt.xticks(rotation=30, ha='right')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(loc='best')
        plt.tight_layout()
        plt.savefig(f"{local_output_dir}/{city_name_l}-oxford-employment-sectors.png", format='png', dpi=300)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-employment-sectors.png", f"{render_dir}/{city_name_l}-oxford-employment-sectors.png", type='render')

        fig = px.bar(emp_shares2, y='Indicator', x='Share', color='Group', barmode='group',color_discrete_map={city_name: 'red', 'Benchmark': 'blue'})

        for location in emp_shares[emp_shares['Location'] != city_name]['Location'].unique():
            location_data = emp_shares[emp_shares['Location'] == location]
            fig.add_trace(go.Scatter(y=location_data['Indicator'], x=location_data['Share'], mode='markers', marker=dict(color='darkgrey'), name=location, showlegend=False))

        fig.update_layout(
            template='plotly_white',
            autosize=True,
            showlegend=True,  
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.5,
                xanchor="center",
                x=0.5,
                title_text=None
            ),
            yaxis=dict(
                tickangle=0,  
                title_text=None,
                linecolor='black'  
            ),
            xaxis=dict(
                tickformat=".1%",
                range=ylims_shares,
                title_text=None,
                linecolor='black'  
            ),
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.write_html(f"{local_output_dir}/{city_name_l}-oxford-employment-sectors.html", full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-employment-sectors.html", f"{render_dir}/{city_name_l}-oxford-employment-sectors.html", type='render')

def plot_gva_inequality(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import plotly.express as px
    import plotly.graph_objects as go
    import utils

    filtered_oxford = oegc[oegc['Location'].isin([city_name] + bm_cities)]
    indicators = oegc[['Indicator']].drop_duplicates()
    gva_inds = indicators['Indicator'][indicators['Indicator'].str.lower().str.contains("gross value added, real, us")].tolist()

    if len(filtered_oxford) > 0:
        filtered_oxford['Group'] = np.where(filtered_oxford['Location'] == city_name, city_name, 'Benchmark')
        filtered_oxford['Group'] = pd.Categorical(filtered_oxford['Group'], categories=[city_name, 'Benchmark'], ordered=True)
        gva_shares = filtered_oxford[filtered_oxford['Indicator'].isin(gva_inds) & ~filtered_oxford['Indicator'].str.contains("Total")]
        gva_shares = gva_shares[['Group', 'Location', 'Indicator', '2021']].rename(columns={'2021': 'Value'})
        gva_shares['Indicator'] = gva_shares['Indicator'].str.replace("Gross value added, real, US$ -", "").str.replace("Transport, storage, information & communication services", "Transport & ICT")
        gva_shares['Share'] = gva_shares.groupby(['Location', 'Group'])['Value'].transform(lambda x: x / x.sum())
        gva_shares['Indicator'] = pd.Categorical(gva_shares['Indicator'], categories=gva_shares['Indicator'].unique(), ordered=True)

        gva_shares2 = gva_shares.groupby(['Group', 'Indicator']).agg({'Share': 'median'}).reset_index().sort_values(by=['Group', 'Indicator'])
        
        ylims_shares = (0, np.ceil(gva_shares['Share'].max() * 10) / 10)

        plt.figure(figsize=(12.5, 6))
        for group in gva_shares2['Group'].unique():
            data = gva_shares2[gva_shares2['Group'] == group]
            plt.bar(data['Indicator'], data['Share'], label=group, alpha=0.7)

        for location in gva_shares[gva_shares['Location'] != city_name]['Location'].unique():
            location_data = gva_shares[gva_shares['Location'] == location]
            plt.plot(location_data['Indicator'], location_data['Share'], 'o', color='darkgrey')

        plt.title(f"Share of GVA by sector in {city_name} and median benchmark city")
        plt.xlabel("Sector")
        plt.ylabel("Share")
        plt.ylim(ylims_shares)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(loc='best')
        plt.tight_layout()
        plt.savefig(f"{local_output_dir}/{city_name_l}-oxford-gva-sectors.png", format='png', dpi=300)
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-gva-sectors.png", f"{render_dir}/{city_name_l}-oxford-gva-sectors.png", type='render')

        fig = px.bar(gva_shares2, y='Indicator', x='Share', color='Group', barmode='group',color_discrete_map={city_name: 'red', 'Benchmark': 'blue'})

        for location in gva_shares[gva_shares['Location'] != city_name]['Location'].unique():
            location_data = gva_shares[gva_shares['Location'] == location]
            fig.add_trace(go.Scatter(y=location_data['Indicator'], x=location_data['Share'], mode='markers', marker=dict(color='darkgrey'), name=location, showlegend=False))  # Swap x and y

        fig.update_layout(
            template='plotly_white',
            autosize=True,
            showlegend=True,  
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.5,
                xanchor="center",
                x=0.5,
                title_text=None
            ),
            yaxis=dict(  
                tickangle=0,
                title_text=None,
                linecolor='black'
            ),
            xaxis=dict(  
                tickformat=".1%",
                range=ylims_shares,
                title_text=None,
                linecolor='black'
            ),
            font=font_dict,
            plot_bgcolor='white'
        )

        fig.write_html(f"{local_output_dir}/{city_name_l}-oxford-gva-sectors.html", full_html=False, include_plotlyjs='cdn')
        utils.upload_blob(cloud_bucket, f"{local_output_dir}/{city_name_l}-oxford-gva-sectors.html", f"{render_dir}/{city_name_l}-oxford-gva-sectors.html", type='render')

def oe_plot(data_bucket, cloud_bucket, oe_dir, oe_locations_blob, oegc_blob, countries_shp_blob, local_data_dir, country_name, country_name_l, city_name, city_name_l, alternate_city_name, local_output_dir, output_dir, render_dir, font_dict):
    import utils
    import pandas as pd

    utils.download_blob(data_bucket, f'{oe_dir}/{oe_locations_blob}', f'{local_data_dir}/oe_locations.csv', check_exists=True)
    oe_locations = pd.read_csv(f'{local_data_dir}/oe_locations.csv')
    if check_city_in_oxford(oe_locations, country_name, city_name):
        utils.download_blob(data_bucket, f'{oe_dir}/{oegc_blob}', f'{local_data_dir}/oegc.csv', check_exists=True)
        oegc = pd.read_csv(f'{local_data_dir}/oegc.csv')

        bm_cities, bm_cities_countries = find_benchmark_cities(oe_locations, oegc, countries_shp_blob, local_data_dir, country_name, city_name)
        print(bm_cities, bm_cities_countries)
        plot_oegc_pop_growth(cloud_bucket, oegc, local_output_dir, city_name, city_name_l, bm_cities, render_dir, font_dict)
        plot_national_shares(cloud_bucket, oegc, city_name, city_name_l, bm_cities, bm_cities_countries, local_output_dir, render_dir, font_dict)
        plot_emp_growth(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict)
        plot_gdp_growth(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict)
        plot_emp_gva_shares(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict)
        plot_gva_inequality(cloud_bucket, oegc, city_name, city_name_l, bm_cities, local_output_dir, render_dir, font_dict)
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
