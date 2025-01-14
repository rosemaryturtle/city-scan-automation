def calculate_aoi_area(aoi_file):
    utm_crs = aoi_file.estimate_utm_crs()
    area_km2 = aoi_file.to_crs(utm_crs).geometry.area.sum() / 1e6

    return area_km2

def get_koeppen_classification(aoi_file, koeppen_file_path):
    import pandas as pd

    centroid = aoi_file.unary_union.centroid

    # koeppen_file_path = global_inputs.get('koeppen_source')
    koeppen = pd.read_csv(koeppen_file_path)

    lon_min, lon_max = centroid.x - 0.5, centroid.x + 0.5
    lat_min, lat_max = centroid.y - 0.5, centroid.y + 0.5
    koeppen_city = koeppen[
        (koeppen[' Lon'].between(lon_min, lon_max)) &
        (koeppen['Lat'].between(lat_min, lat_max))
    ][' Cls'].unique()


    # koeppen_text = ', '.join(koeppen_city)
    # print(f"Köppen climate classification: {koeppen_text} (See https://en.wikipedia.org/wiki/Köppen_climate_classification for classes)")
    return koeppen_city

def check_city_in_oxford(city, country, oxford_locations, oxford_global_source):
    import pandas as pd
    # oxford_locations = pd.read_csv(global_inputs['oxford_locations_source'])
    oxford_locations_in_country = oxford_locations[oxford_locations['Country'] == country]
    in_oxford = city in oxford_locations_in_country['Location'].values
    
    if not in_oxford:
        print(f"{city} is not in Oxford Locations.")

    oxford_full = pd.read_csv(oxford_global_source)
        
    if in_oxford:
        city_pop = (oxford_full[(oxford_full['Location'] == city) & 
                                (oxford_full['Indicator'] == 'Total population')]['2021'] * 1000).values[0]
        print(f"The population of {city} is {city_pop}")
    else:
        print(f"Population data for {city} does not exist in Oxford Economics. Check citypopulation.de or add manually")
    
    # return in_oxford, oxford_full
    return # the texts?

def find_benchmark_cities(city, country, nearby_countries_string, oxford_locations_source, oxford_global_source):
    import pandas as pd
    
    try:
        oxford_locations = pd.read_csv(oxford_locations_source)
        oxford_full = pd.read_csv(oxford_global_source)

        nearby_cities = oxford_locations[
            oxford_locations['Country'].str.lower().str.contains(nearby_countries_string) &
            (oxford_locations['Location'] != country) &
            (~oxford_locations['Location'].str.contains("Total"))
        ]['Location'].tolist()
        print("Nearby cities:", nearby_cities)

        city_pop_df = oxford_full[
            (oxford_full['Location'] == city) & 
            (oxford_full['Indicator'] == 'Total population')
        ]
        
        if city_pop_df.empty:
            raise ValueError(f"No population data found for {city}.")

        city_pop = city_pop_df['2021'].values[0] * 1000
        bm_cities_df = oxford_full[
            (oxford_full['Location'].isin(nearby_cities)) &
            (oxford_full['Indicator'] == "Total population") &
            (
                (oxford_full['2021'].between(city_pop * 0.5 / 1000, city_pop * 1.5 / 1000)) |
                (oxford_full['Country'] == country)
            ) &
            (oxford_full['Location'] != city)
        ]

        if bm_cities_df.empty:
            print(f"No benchmark cities found for {city}. Proceed to next step of adding manual benchmark cities")


        bm_cities = bm_cities_df['Location'].tolist()
        return bm_cities

    except Exception:
        print(f"Error finding benchmark cities. Proceed to next step of adding manual benchmark cities")
        return []
