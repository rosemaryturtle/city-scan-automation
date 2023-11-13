script_list = ["accessibility.py",
               "gee_forest.py",
               "gee_landcover.py",
               "gee_lst.py",
               "gee_ndvi.py",
               "gee_nightlight.py",
               "raster_processing.py",
               "rwi.py",
               "road_network.py"]

for s in script_list:
    with open(s) as f:
        exec(f.read())
