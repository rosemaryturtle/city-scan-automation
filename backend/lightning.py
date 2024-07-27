import rasterio
import rasterio.mask
import numpy as np
from pathlib import Path

cities = ['Cumilla', 'Chattogram', 'Gazipur', 'Narayanganj', 'Khulna', 'Rajshahi',
          'Barishal', 'Mymensingh', 'Rangpur', 'Sylhet']

def avg_l(city):
    city_nospace = city.replace(" ", "_").lower()
    temp_file = Path('../mnt/city-directories/02-process-output') / (city_nospace + '_lightning.tif')
    temp = rasterio.open(temp_file)
    temp_array = temp.read(1)
    temp_array = temp_array[temp_array >= 0]
    return np.nanmean(temp_array)
cities_avg_l = {}

for city in cities:
    cities_avg_l[city] = avg_l(city)
print(cities_avg_l)

with open('../mnt/city-directories/02-process-output/avg_lightning.csv', 'w') as f:
    f.write('city,avg\n')
    for city in cities_avg_l:
        f.write("%s,%s\n"%(city, cities_avg_l[city]))