import os

# Set the environment variable in your code
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:/Users/Owner/OneDrive/Documents/Career/World Bank/CRP/other/google-cloud-city-scan-service-account-key.json"

# TODO: create city folder and 3 subdirectories in crp-city-scan

# TODO: make sure AOI is a polygon of an appropriate size
# TODO: if an AOI includes several polygons, make it a multipolygon

script_list = ["burned_area.py",
               'fwi.py',
               "gee_forest.py",
               "gee_landcover.py",
               "gee_lst_winter.py",
               "gee_lst.py",
               "gee_ndmi.py",
               "gee_ndvi.py",
               "gee_nightlight.py",
               "landcover_burnability.py",
               "raster_processing.py",
               "road_network.py",
               "rwi.py",
               "soil_salinity.py",
               "contour_elev_stats.py",
               'slope.py',
               'flood_stats.py'
               ]
# script_list = ['landcover_burnability_gcp.py']

for s in script_list:
    with open(s) as f:
        exec(f.read())
