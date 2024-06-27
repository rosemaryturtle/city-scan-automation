# DETERMINE WHETHER TO RUN THIS SCRIPT ##############
import yaml

# load menu
with open("../mnt/city-directories/01-user-input/menu.yml", 'r') as f:
    menu = yaml.safe_load(f)

if menu['erosion']:
    print('run erosion')

    import os
    import pandas as pd
    import geopandas as gpd
    from pathlib import Path
    from os.path import exists
