def calculate_aoi_area(aoi_file):
    return float(aoi_file.to_crs(epsg=6933).area.sum() / 1e6)

def get_koeppen_classification(features, data_bucket, koeppen_blob, local_data_dir):
    import pandas as pd
    import utils

    centroid = features.centroid.values[0]
    coords = {' Lon': centroid.x, 'Lat': centroid.y}

    utils.download_blob(data_bucket, koeppen_blob, f'{local_data_dir}/koeppen.csv')
    koeppen = pd.read_csv(f'{local_data_dir}/koeppen.csv')

    lon_min, lon_max = coords[' Lon'] - 0.5, coords[' Lon'] + 0.5
    lat_min, lat_max = coords['Lat'] - 0.5, coords['Lat'] + 0.5
    koeppen_city = koeppen[
        (koeppen[' Lon'].between(lon_min, lon_max)) &
        (koeppen['Lat'].between(lat_min, lat_max))
    ][' Cls'].unique()

    koeppen_text = ', '.join(koeppen_city)
    print(f"Köppen climate classification: {koeppen_text} (See https://en.wikipedia.org/wiki/Köppen_climate_classification for classes)")
    return koeppen_text
