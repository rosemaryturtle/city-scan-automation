# Download & convert Bing buildings
# https://github.com/microsoft/GlobalMLBuildingFootprints?tab=readme-ov-file
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
import os
import math

country = 'Ukraine'
aoi_path = '/Users/bennotkin/Documents/world-bank/crp/city-scans/01-current-scans/2025-05-ukraine-makariv/AOI'

# Originally used https://labs.mapbox.com/what-the-tile/https://labs.mapbox.com/what-the-tile/ to find quadkeys
def get_quadkey(lat, lng, zoom):
    x = int((lng + 180) / 360 * (1 << zoom))
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * (1 << zoom))
    quadkey = ''
    for i in range(zoom, 0, -1):
        digit = 0
        mask = 1 << (i - 1)
        if (x & mask) != 0:
            digit += 1
        if (y & mask) != 0:
            digit += 2
        quadkey += str(digit)
        quadkey_int = int(quadkey)
    return quadkey_int

def get_quadkeys(file, zoom):
    aoi = gpd.read_file(file)
    # Initialize list to store quadkeys for this file
    quadkeys = []
    # Process each geometry in the shapefile
    for geom in aoi.geometry:
        if geom is None:
            continue
        # Extract coordinates based on geometry type
        coords = []
        # Point
        if geom.geom_type == 'Point':
            coords = [(geom.y, geom.x)]
        # LineString
        elif geom.geom_type == 'LineString':
            coords = [(y, x) for x, y in geom.coords]
        # Polygon
        elif geom.geom_type == 'Polygon':
            for ring in [geom.exterior] + list(geom.interiors):
                coords.extend([(y, x) for x, y in ring.coords])
        # Multi-geometries
        elif geom.geom_type in ['MultiPoint', 'MultiLineString', 'MultiPolygon']:
            for part in geom.geoms:
                if part.geom_type == 'Point':
                    coords.append((part.y, part.x))
                elif part.geom_type == 'LineString':
                    coords.extend([(y, x) for x, y in part.coords])
                elif part.geom_type == 'Polygon':
                    for ring in [part.exterior] + list(part.interiors):
                        coords.extend([(y, x) for x, y, *_ in ring.coords])
        # Get quadkey for each coordinate
        for lat, lng in coords:
            quadkey = get_quadkey(lat, lng, zoom)
            if quadkey not in quadkeys:
                quadkeys.append(quadkey)
    print(f"Found {len(quadkeys)} unique quadkeys in AOI")
    print(quadkeys)
    return quadkeys

def main():

    # this is the name of the geography you want to retrieve. update to meet your needs
    quadkeys = get_quadkeys(aoi_path, 9)
    # quadkeys = [
    #     120303210, # Bucha, Makariv
    #     120303211, # Bucha
    #     120321301, # Mykolaiv
    #     120330021, # Zaporizhzhia
    #     120330030, # Zaporizhzhia
    #     120312322, # Izyum
    #     120312323, # Izyum
    # ]

    dataset_links = pd.read_csv("https://minedbuildings.z5.web.core.windows.net/global-buildings/dataset-links.csv")
    for quadkey in quadkeys:
        # quadkey = int(quadkey)
        if os.path.exists(f"building-tiles/{quadkey}.fgb"):
            print(f"File for quadkey {quadkey} already exists. Skipping...")
            continue
        country_links = dataset_links[(dataset_links.Location == country) & (dataset_links.QuadKey == quadkey)]
        for _, row in country_links.iterrows():
            df = pd.read_json(row.Url, lines=True)
            df['geometry'] = df['geometry'].apply(shape)
            gdf = gpd.GeoDataFrame(df, crs=4326)
            gdf.to_file(f"building-tiles/{country}-{row.QuadKey}.fgb", driver="FlatGeobuf")

if __name__ == "__main__":
    main()
