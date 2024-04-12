##Text begins


    
![png](output_4_0.png)
    


    Merged pluvial data saved as mnt/city-directories/02-process-output/goris_merged_pluvial_data.tif
    Merged pluvial data saved as mnt/city-directories/02-process-output/goris_merged_pluvial_data_utm.tif
    Merged fluvial data saved as mnt/city-directories/02-process-output/goris_merged_fluvial_data.tif
    Merged fluvial data saved as mnt/city-directories/02-process-output/goris_merged_fluvial_data_utm.tif
    city name: goris
    country name:armenia


##City Subdistricts available?


    
![png](output_6_0.png)
    


    city subdistricts are larger than goris: Not available


##Lowest admin level available?

    /var/folders/tb/lt6mv9zn47973s97jtlwv_b40000gn/T/ipykernel_16043/2994944802.py:16: UserWarning:
    
    The `geometries` module and `geometries_from_X` functions have been renamed the `features` module and `features_from_X` functions. Use these instead. The `geometries` module and function names are deprecated and will be removed in a future release.
    


    Not available
    aspect must be finite and positive 


    /Users/ipshitakarmakar/mambaforge/envs/geo/lib/python3.11/site-packages/geopandas/geodataframe.py:1538: SettingWithCopyWarning:
    
    
    A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead
    
    See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    



    
![png](output_9_3.png)
    


Area of the city

    Area of the city of goris is 1.4398561252041046e-09 kilometer ** 2


Koppen Climate

    Köppen climate classification:  Dfb,  Cfa,  Dfa (See https://en.wikipedia.org/wiki/Köppen_climate_classification for classes)





    array([' Dfb', ' Cfa', ' Dfa'], dtype=object)



Population distribution by age and sex



    under5: 9.40%
    youth (15-24): 21.01%
    working_age (15-64): 0.00%
    elderly (60+): 39.65%
    reproductive_age, percent of women (15-50): 45.97%
    sex_ratio: 0.0 males to 100 females


Population Density



    Cluster labels shape: (71, 80)
    The cluster with the highest value is located in the center of the city.
    The cluster with the lowest value is located in the south east of the city.
    Values range from 7.36 units to 47.96 units
    Regression is not significant. Results may not be reliable.


Economic Activity



    Cluster labels shape: (66, 74)
    The cluster with the highest value is located in the center of the city.
    The cluster with the lowest value is located in the south east of the city.
    Values range from 0.00 units to 1329.00 units


Change in Economic Activity 



    Cluster labels shape: (66, 74)
    The cluster with the highest value is located in the center of the city.
    The cluster with the lowest value is located in the south east of the city.
    Values range from -0.10 units to 1.76 units


Urban Extent and Change



    The city's built-up area grew from 1.98 sq. km in 1985 to 4.2 in 2015 for 112.33% growth


Land Cover



    The first highest landcover value is Tree cover with 49.16% of the total land area
    The second highest landcover value is Grassland with 31.40% of the total land area
    The third highest landcover value is Built-up with 17.66% of the total land area


Photovoltaic Power Potential

    Seasonality is low to moderate, making solar energy available in only some of the months




Land Surface Temperature

    Values range from 0.00 units to 47.84 units


Green Spaces

    Values range from -0.04 units to 0.53 units


Elevation

          legend  count   percent Percent  Elevation
    0  1160-1290   1581  0.096520     10%       1160
    1  1290-1410   5121  0.312637     31%       1290
    2  1410-1530   5101  0.311416     31%       1410
    3  1530-1640   4577  0.279426     28%       1530
    4  1640-1780   3447  0.210440     21%       1640




    Highest percentage entry for Elevation:
    legend       1290-1410
    count             5121
    percent       0.312637
    Percent            31%
    Elevation         1290
    Name: 1, dtype: object


Slope



    Cluster labels shape: (66, 74)
    The cluster with the highest value is located in the center of the city.
    The cluster with the lowest value is located in the north west of the city.
    Values range from 0.00 units to 65535.00 units




    Highest percentage entry for Slope:
    legend        10-20
    count          6627
    percent    0.345084
    Percent         35%
    Slope          10.0
    Name: 3, dtype: object


NDMI

    Values range from -0.22 units to 0.31 units


Flooding 

Pluvial and OSM

    0 of 3 (0.00%) health are located in a riverine flood risk zone with a minimum depth of 15 cm.
    2 of 3 (66.67%) police are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Fire stations do not exist
    6 of 10 (60.00%) schools are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Statistics saved to mnt/city-directories/02-process-output/pu_osmpt.xlsx
    Total length of highways intersecting pluvial data: 0.04 meters
    Percentage of highways intersecting pluvial data: 0.0011%



    <Figure size 640x480 with 0 Axes>


Pluvial Flooding and WSF

    Statistics by year saved to mnt/city-directories/02-process-output/goris_pu_wsf_areas_by_year.xlsx
    PNG saved to mnt/city-directories/03-render-output/pu_wsf.png




    In 2015, 152792.80 sq.m of the city’s built-up area (15.33%) was exposed to surface water flooding.


Pluvial and Population

    9.90% of densely populated areas are located within the rainwater flood risk zone with a minimum depth of 15 cm
    Result saved to mnt/city-directories/02-process-output/pu_pop_area.csv


Fluvial and OSM

    0 of 3 (0.00%) health are located in a riverine flood risk zone with a minimum depth of 15 cm.
    0 of 3 (0.00%) police are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Fire stations do not exist
    0 of 10 (0.00%) schools are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Statistics saved to mnt/city-directories/02-process-output/fu_osmpt.xlsx
    Total length of highways flooded due to pluvial conditions: 0.00 meters
    Percentage of highways flooded due to pluvial conditions: 0.00%


Fluvial and WSF

    Statistics by year saved to mnt/city-directories/02-process-output/goris_fu_wsf_areas_by_year.xlsx
    PNG saved to mnt/city-directories/03-render-output/fu_wsf.png





    ---------------------------------------------------------------------------

    ZeroDivisionError                         Traceback (most recent call last)

    Cell In[71], line 52
         50     total_built_up_area = sum(stats_by_year.values())
         51     flooded_area_2015 = stats_by_year.get(2015, 0)
    ---> 52     percentage_2015 = (flooded_area_2015 / total_built_up_area) * 100
         53     print(f"In 2015, {flooded_area_2015:.2f} sq.m of the city’s built-up area ({percentage_2015:.2f}%) was exposed to surface water flooding.")
         54 else:


    ZeroDivisionError: float division by zero


Fluvial and Population

    6.72% of densely populated areas are located within the fluvial flood risk zone with a minimum depth of 10 cm
    Result saved to mnt/city-directories/02-process-output/fu_pop_area.csv

