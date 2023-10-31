script_list = ["accessibility.py",
               "gee_forest.py",
               "gee_lst.py",
               "gee_ndvi.py",
               "gee_nightlight.py",
               "raster_processing.py",
               "road_network.py",
               "rwi.py"]

for s in script_list:
    with open(s) as f:
        exec(f.read())
