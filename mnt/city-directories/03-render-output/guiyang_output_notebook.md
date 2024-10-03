## Text begins


    
![png](output_4_0.png)
    



      File /var/folders/tb/lt6mv9zn47973s97jtlwv_b40000gn/T/ipykernel_43539/1374161815.py:62
        fig.update_traces(selector=dict(name=city), line=dict(dash='solid', color='black', width=2), mode='lines',line=dict(color='black'))
                                                                                                                  ^
    SyntaxError: keyword argument repeated: line




    ---------------------------------------------------------------------------

    SyntaxError                               Traceback (most recent call last)

    Cell In[296], line 9
          7     global_inputs = yaml.safe_load(f)
          8 # run scan assembly and toolbox
    ----> 9 get_ipython().run_line_magic('run', "'scan_assembly.ipynb'")
         10 get_ipython().run_line_magic('run', "'toolbox.ipynb'")
         12 # load city inputs files, to be updated for each city scan


    File ~/mambaforge/envs/geo/lib/python3.11/site-packages/IPython/core/interactiveshell.py:2417, in InteractiveShell.run_line_magic(self, magic_name, line, _stack_depth)
       2415     kwargs['local_ns'] = self.get_local_scope(stack_depth)
       2416 with self.builtin_trap:
    -> 2417     result = fn(*args, **kwargs)
       2419 # The code below prevents the output from being displayed
       2420 # when using magics with decodator @output_can_be_silenced
       2421 # when the last Python token in the expression is a ';'.
       2422 if getattr(fn, magic.MAGIC_OUTPUT_CAN_BE_SILENCED, False):


    File ~/mambaforge/envs/geo/lib/python3.11/site-packages/IPython/core/magics/execution.py:722, in ExecutionMagics.run(self, parameter_s, runner, file_finder)
        720     with preserve_keys(self.shell.user_ns, '__file__'):
        721         self.shell.user_ns['__file__'] = filename
    --> 722         self.shell.safe_execfile_ipy(filename, raise_exceptions=True)
        723     return
        725 # Control the response to exit() calls made by the script being run


    File ~/mambaforge/envs/geo/lib/python3.11/site-packages/IPython/core/interactiveshell.py:2939, in InteractiveShell.safe_execfile_ipy(self, fname, shell_futures, raise_exceptions)
       2937 result = self.run_cell(cell, silent=True, shell_futures=shell_futures)
       2938 if raise_exceptions:
    -> 2939     result.raise_error()
       2940 elif not result.success:
       2941     break


    File ~/mambaforge/envs/geo/lib/python3.11/site-packages/IPython/core/interactiveshell.py:266, in ExecutionResult.raise_error(self)
        264 """Reraises error if `success` is `False`, otherwise does nothing"""
        265 if self.error_before_exec is not None:
    --> 266     raise self.error_before_exec
        267 if self.error_in_exec is not None:
        268     raise self.error_in_exec


    File ~/mambaforge/envs/geo/lib/python3.11/site-packages/IPython/core/interactiveshell.py:3446, in InteractiveShell.run_ast_nodes(self, nodelist, cell_name, interactivity, compiler, result)
       3440     mod = ast.Interactive([node])  # type: ignore
       3441 with compiler.extra_flags(
       3442     getattr(ast, "PyCF_ALLOW_TOP_LEVEL_AWAIT", 0x0)
       3443     if self.autoawait
       3444     else 0x0
       3445 ):
    -> 3446     code = compiler(mod, cell_name, mode)
       3447     asy = compare(code)
       3448 if await self.run_code(code, result, async_=asy):


    File ~/mambaforge/envs/geo/lib/python3.11/codeop.py:118, in Compile.__call__(self, source, filename, symbol)
        117 def __call__(self, source, filename, symbol):
    --> 118     codeob = compile(source, filename, symbol, self.flags, True)
        119     for feature in _features:
        120         if codeob.co_flags & feature.compiler_flag:


    SyntaxError: keyword argument repeated: line (1374161815.py, line 62)


## City Subdistricts available?


    
![png](output_6_0.png)
    


    city subdistricts are larger than guiyang: Not available


## Lowest admin level available?

    Not available
    'pre_clip_area'


    /Users/ipshitakarmakar/mambaforge/envs/geo/lib/python3.11/site-packages/shapely/set_operations.py:133: RuntimeWarning:
    
    invalid value encountered in intersection
    
    /Users/ipshitakarmakar/mambaforge/envs/geo/lib/python3.11/site-packages/geopandas/geodataframe.py:1538: SettingWithCopyWarning:
    
    
    A value is trying to be set on a copy of a slice from a DataFrame.
    Try using .loc[row_indexer,col_indexer] = value instead
    
    See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
    


## Area of the city

    Area of the city of guiyang is 2531.550104 sq.km


## Koppen Climate

    Köppen climate classification:  Cwa (See https://en.wikipedia.org/wiki/Köppen_climate_classification for classes)





    array([' Cwa'], dtype=object)



## Population in Oxford economics

    The population of Guiyang is 4279620.0


## Population from citypopulation.de

    'NoneType' object has no attribute 'find'
    Guiyang population data could not be retrieved from CityPopulation.de. Try manual entry instead.
    'NoneType' object has no attribute 'find'


### City Population Growth




    
![png](output_19_1.png)
    


    An error occurred while calculating growth text: 'NoneType' object has no attribute 'iloc', try manual method instead


## Benchmark cities 

    Nearby cities: ['Kazakhstan', 'Almaty', 'Nur-Sultan', 'Myanmar', 'Mandalay', 'Nay Pyi Taw', 'Yangon', 'Kathmandu', 'Dushanbe', 'Can Tho', 'Da Nang', 'Hanoi', 'Haiphong', 'Ho Chi Minh City', 'Astrakhan', 'Barnaul', 'Chelyabinsk', 'Ekaterinburg', 'Irkutsk', 'Izhevsk', 'Kazan', 'Khabarovsk', 'Krasnodar', 'Krasnoyarsk', 'Lipetsk', 'Makhachkala', 'Moscow', 'Nizhniy Novgorod', 'Novokuznetsk', 'Novosibirsk', 'Omsk', 'Orenburg', 'Penza', 'Perm', 'Rostov-on-Don', 'Ryazan', 'Samara', 'Saratov', 'St Petersburg', 'Tomsk', 'Tula', 'Tyumen', 'Ufa', 'Ulyanovsk', 'Vladivostok', 'Volgograd', 'Voronezh', 'Yaroslavl']
    ['Mandalay', 'Kathmandu', 'St Petersburg']


## Bechmark cities Manual

    ['Beijing', 'Guangzhou', 'Kathmandu', 'Mandalay', 'Shanghai', 'Shanxi', 'St Petersburg', 'Taiyuan']


## Population Density Manual


    
![png](output_28_0.png)
    







    
![png](output_29_1.png)
    



    
![png](output_30_0.png)
    





    
![png](output_31_0.png)
    





    
![png](output_32_0.png)
    





    
![png](output_33_0.png)
    





    
![png](output_34_0.png)
    




## Population distribution by age and sex



    under5: 9.17%
    youth (15-24): 24.90%
    working_age (15-64): 0.72%
    elderly (60+): 31.32%
    reproductive_age, percent of women (15-50): 53.75%
    sex_ratio: -97.94 males to 100 females


## Population Density

## Economic Activity

    Values range from 0.00 units to 8766.09 units


## Change in Economic Activity 

## Urban Extent and Change



    The city's built-up area grew from 110.96 sq. km in 1985 to 397.06 in 2015 for 257.84% growth


## Land Cover



    The first highest landcover value is Tree cover with 55.16% of the total land area
    The second highest landcover value is Grassland with 16.86% of the total land area
    The third highest landcover value is Cropland with 12.43% of the total land area


## Photovoltaic Power Potential

    Seasonality is low to moderate, making solar energy available in only some of the months




## Land Surface Temperature

    Values range from 19.92 to 57.31


## Green Spaces

    Values range from -0.19 units to 0.54 units


## Elevation



    Highest percentage entry for Elevation is 50.22% in the bin range 1200-1360


## Slope

    Values range from 0.00 units to 63.84 units




    Highest percentage entry for Slope is 33% in the bin range 10-20


## NDMI

    Values range from -0.39 units to 0.47 units


## Flooding 

    Tally of flood events
    DEAD             6773
    DISPLACED    21322670
    BEGAN              21
    dtype: int64




### Pluvial and OSM

    5 of 26 (19.23%) health are located in a riverine flood risk zone with a minimum depth of 15 cm.
    4 of 6 (66.67%) police are located in a riverine flood risk zone with a minimum depth of 15 cm.
    0 of 2 (0.00%) fire are located in a riverine flood risk zone with a minimum depth of 15 cm.
    23 of 138 (16.67%) schools are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Statistics saved to ../mnt/city-directories/02-process-output/pu_osmpt.xlsx


### Pluvial Flooding and WSF

    PNG saved to ../mnt/city-directories/03-render-output/guiyang_pu_wsf.png




    As of 2015, 103.41 sq.km of the city’s built-up area (26.04%) was exposed to surface water flooding.


### Pluvial and Population

    60th Percentile of Population Data (excluding zeros): 39.820377349853516
    6.66% of densely populated areas are located within the rainwater flood risk zone with a minimum depth of 15 cm
    Result saved to ../mnt/city-directories/02-process-output/pu_pop_area.csv


### Fluvial and OSM

    2 of 26 (7.69%) health are located in a riverine flood risk zone with a minimum depth of 15 cm.
    0 of 6 (0.00%) police are located in a riverine flood risk zone with a minimum depth of 15 cm.
    0 of 2 (0.00%) fire are located in a riverine flood risk zone with a minimum depth of 15 cm.
    3 of 138 (2.17%) schools are located in a riverine flood risk zone with a minimum depth of 15 cm.
    Statistics saved to ../mnt/city-directories/02-process-output/fu_osmpt.xlsx


### Fluvial and WSF

    810.354708629123
    PNG saved to ../mnt/city-directories/03-render-output/Guiyang_fu_wsf.png




    In 2015, 7.62 sq.m of the city’s cumulative built-up area (1.92%) was exposed to fluvial flooding.
    In 1985, 3.06 sq.m of the city’s cumulative built-up area (2.76%) was exposed to fluvial flooding.


### Fluvial and Population

    60th Percentile of Population Data (excluding zeros): 39.820377349853516
    0.16% of densely populated areas are located within the fluvial flood risk zone with a minimum depth of 15 cm
    Result saved to ../mnt/city-directories/02-process-output/fu_pop_area.csv


## Combined Flooding

### Combined Flooding and WSF

    PNG saved to ../mnt/city-directories/03-render-output/guiyang_comb_wsf.png




    In 2015, 109.25 sq.km of the city’s cumulative built-up area (27.52%) was exposed to combined flooding.
    In 1985, 30.57 sq.km of the city’s cumulative built-up area (27.55%) was exposed to combined flooding.


### Combined flooding and Population

    60th Percentile of Population Data (excluding zeros): 39.820377349853516
    40.00% of densely populated areas are located within the combined flood risk zone with a minimum depth of 15 cm
    Result saved to ../mnt/city-directories/02-process-output/comb_pop_area.csv


### Combined flooding and Infrastructure

    26 of 26 (100.00%) health are located in a combined flood risk zone with a minimum depth of 15 cm.
    6 of 6 (100.00%) police are located in a combined flood risk zone with a minimum depth of 15 cm.
    2 of 2 (100.00%) fire are located in a combined flood risk zone with a minimum depth of 15 cm.
    138 of 138 (100.00%) schools are located in a combined flood risk zone with a minimum depth of 15 cm.
    Statistics saved to ../mnt/city-directories/02-process-output/comb_osmpt.xlsx


## Earthquake


    
![png](output_92_0.png)
    




    Base directory for organizing files: ../mnt/city-directories/03-render-output
    Creating folders:
    - ../mnt/city-directories/03-render-output/plots
    - ../mnt/city-directories/03-render-output/plots/html
    - ../mnt/city-directories/03-render-output/plots/png
    Moved guiyang_urban_built_up_area.png to ../mnt/city-directories/03-render-output/plots/png
    Moved guiyang_urban_built_up_area.html to ../mnt/city-directories/03-render-output/plots/html

