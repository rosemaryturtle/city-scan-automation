script_list = ["accessibility.py",
               "burned_area.py",
               "cover_image.py",
            #    "demographics.py",
               "gee_forest.py",
               "gee_landcover.py",
               "gee_lst.py",
               "gee_ndmi.py",
               "gee_ndvi.py",
               "gee_nightlight.py",
               "landcover_burnability.py",
               "raster_processing.py",
               "road_network.py",
               "rwi.py"]

for s in script_list:
    with open(s) as f:
        exec(f.read())
