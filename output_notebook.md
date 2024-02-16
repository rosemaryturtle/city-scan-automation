    read AOI shapefile



    
![png](output_4_1.png)
    


    AOI Area is 5.762612237272471e-09 kilometer ** 2


    Köppen climate classification:  Csa,  Dsb (See https://en.wikipedia.org/wiki/Köppen_climate_classification for classes)


    /var/folders/tb/lt6mv9zn47973s97jtlwv_b40000gn/T/ipykernel_19908/904168228.py:12: UserWarning: Geometry is in a geographic CRS. Results from 'centroid' are likely incorrect. Use 'GeoSeries.to_crs()' to re-project geometries to a projected CRS before this operation.
    
      centroid = features.centroid.values[0]





<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Location</th>
      <th>Year</th>
      <th>Population</th>
      <th>Source</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>69098</th>
      <td>Shahrisabz</td>
      <td>2015</td>
      <td>101769.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>69044</th>
      <td>Shahrisabz</td>
      <td>2016</td>
      <td>103527.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>68990</th>
      <td>Shahrisabz</td>
      <td>2017</td>
      <td>105129.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>68936</th>
      <td>Shahrisabz</td>
      <td>2018</td>
      <td>134531.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>68882</th>
      <td>Shahrisabz</td>
      <td>2019</td>
      <td>137076.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>68828</th>
      <td>Shahrisabz</td>
      <td>2020</td>
      <td>139113.0</td>
      <td>UN Data</td>
    </tr>
    <tr>
      <th>68774</th>
      <td>Shahrisabz</td>
      <td>2021</td>
      <td>140519.0</td>
      <td>UN Data</td>
    </tr>
  </tbody>
</table>
</div>



    pop: 24,350,210
    ['Cairo', 'Lagos', 'Buenos Aires', 'S�o Paulo', 'Mexico City', 'Los Angeles', 'New York', 'Beijing', 'Chengdu', 'Guangzhou', 'Shanghai', 'Shenzhen', 'Suzhou (Jiangsu)', 'Bengaluru', 'Chennai', 'Delhi', 'Kolkata', 'Osaka-Kyoto', 'Karachi', 'Lahore', 'Manila', 'Seoul', 'Bangkok', 'Tashkent', 'Ho Chi Minh City', 'Paris', 'Moscow', 'Istanbul', 'London', 'Tehran']
    Benchmark cities
                    Location         Country         Indicator        2021
    347941           Bangkok        Thailand  Total population  16438380.0
    192076           Beijing           China  Total population  20075490.0
    267114         Bengaluru           India  Total population  13953030.0
    73237       Buenos Aires       Argentina  Total population  15468100.0
    17887              Cairo           Egypt  Total population  23449150.0
    195924           Chengdu           China  Total population  14769850.0
    270962           Chennai           India  Total population  12633890.0
    272405             Delhi           India  Total population  33926960.0
    204101         Guangzhou           China  Total population  14783030.0
    352754  Ho Chi Minh City         Vietnam  Total population  13730500.0
    465830          Istanbul          Turkey  Total population  15709290.0
    330618           Karachi        Pakistan  Total population  14735180.0
    281544           Kolkata           India  Total population  27461080.0
    51580              Lagos         Nigeria  Total population  15776370.0
    331099            Lahore        Pakistan  Total population  16404570.0
    481224            London  United Kingdom  Total population  12333080.0
    158881       Los Angeles   United States  Total population  13126340.0
    336872            Manila     Philippines  Total population  27545160.0
    121836       Mexico City          Mexico  Total population  20647830.0
    434558            Moscow          Russia  Total population  17426220.0
    163691          New York   United States  Total population  20870600.0
    310887       Osaka-Kyoto           Japan  Total population  16971160.0
    378742             Paris          France  Total population  12235390.0
    341684             Seoul     South Korea  Total population  22843470.0
    232961          Shanghai           China  Total population  24808600.0
    235847          Shenzhen           China  Total population  20844330.0
    237771  Suzhou (Jiangsu)           China  Total population  13084440.0
    92000          S�o Paulo          Brazil  Total population  22718000.0
    349867          Tashkent      Uzbekistan  Total population   3750885.0
    491808            Tehran            Iran  Total population  15163180.0
    
    Nearby non-benchmark cities
                       Location     Country         Indicator         2021
    22700               Mbabane    Eswatini  Total population     86096.13
    111731  Georgetown (Guyana)      Guyana  Total population    137909.00
    9222                  Praia  Cape Verde  Total population    172681.30
    413387            Podgorica  Montenegro  Total population    196428.10
    323880                 Male    Maldives  Total population    196675.90
    ...                     ...         ...               ...          ...
    206987             Hangzhou       China  Total population  12110900.00
    285873               Mumbai       India  Total population  24350210.00
    312330                Tokyo       Japan  Total population  36973620.00
    299823              Jakarta   Indonesia  Total population  38797500.00
    186302                Dhaka  Bangladesh  Total population  50024640.00
    
    [868 rows x 4 columns]
    
    Benchmark footnote text:
    Buenos Aires (Argentina)
    S�o Paulo (Brazil)
    Beijing, Chengdu, Guangzhou, Shanghai, Shenzhen, Suzhou (Jiangsu) (China)
    Cairo (Egypt)
    Paris (France)
    Mumbai, Kolkata, Chennai, Delhi, Bengaluru (India)
    Tehran (Iran)
    Osaka-Kyoto (Japan)
    Mexico City (Mexico)
    Lagos (Nigeria)
    Karachi, Lahore (Pakistan)
    Manila (Philippines)
    Moscow (Russia)
    Seoul (South Korea)
    Bangkok (Thailand)
    Istanbul (Turkey)
    London (United Kingdom)
    Los Angeles, New York (United States)
    Tashkent (Uzbekistan)
    Ho Chi Minh City (Vietnam)


    The city's built-up area grew from 18.77 km^2 in 1985 to 40.63 in 2015 for 116.5% growth
        Year    uba_km2  growth_pct  growth_km2
    0   1985  18.766749         NaN         NaN
    1   1986  18.766749    0.000000    0.000000
    2   1987  19.465923    0.037256    0.699174
    3   1988  19.992260    0.027039    0.526337
    4   1989  20.511484    0.025971    0.519224
    5   1990  21.776115    0.061655    1.264631
    6   1991  22.485247    0.032565    0.709132
    7   1992  23.793265    0.058172    1.308018
    8   1993  24.451897    0.027681    0.658632
    9   1994  25.096304    0.026354    0.644407
    10  1995  25.777696    0.027151    0.681393
    11  1996  26.648286    0.033773    0.870589
    12  1997  26.918567    0.010143    0.270281
    13  1998  27.593558    0.025075    0.674991
    14  1999  28.341810    0.027117    0.748252
    15  2000  29.077258    0.025949    0.735449
    16  2001  29.778567    0.024119    0.701308
    17  2002  30.676184    0.030143    0.897617
    18  2003  31.447908    0.025157    0.771723
    19  2004  32.531165    0.034446    1.083258
    20  2005  33.662789    0.034786    1.131624
    21  2006  34.629400    0.028715    0.966610
    22  2007  35.319327    0.019923    0.689928
    23  2008  35.960889    0.018165    0.641562
    24  2009  36.969464    0.028046    1.008575
    25  2010  37.532787    0.015238    0.563323
    26  2011  38.060546    0.014061    0.527759
    27  2012  38.973811    0.023995    0.913265
    28  2013  39.342247    0.009453    0.368436
    29  2014  39.988076    0.016416    0.645829
    30  2015  40.630349    0.016062    0.642273



    
![png](output_12_1.png)
    



    
![png](output_16_0.png)
    

