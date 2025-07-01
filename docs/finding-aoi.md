# Finding an AOI

I find the easiest way to find an AOI is to search OpenStreetMap with Nominatim and download it using R.

1. Search for AOI on https://nominatim.openstreetmap.org/ui/search.html and share screenshot with client TTL for approval.
2. Using the city name listed on Nominatim, download AOI using R:

```r
librarian::shelf
city <- "city name"
country <- "country name">

# Limit search to a bounding box around the city
bounding_box <- getbb(paste(city, country)) %>% (\(x) {
  matrix(c(-1, -1, 1, 1), nrow = 2) * .01 * x + x
})()

# Get all OpenStreetMap features with the city name
data <- opq(bbox = bounding_box) %>%
  add_osm_feature(key = "name:en", value = city, value_exact = FALSE)  %>%
  osmdata_sf()

# data may include many different features, so you'll need to inspect them
# First see data's contents and then plot to confirm the shape
# The right feature will probably be in data$osm_multipolygons or data$osm_polygons
str(data)
plot(data$osm_multi_polygons[1,])

# Save the AOI as a shapefile
# For example, if the right boundary is data$osm_multipolygons[1,]:
writeVector(data$osm_multipolygons[1,], "path/to/aoi.shp", driver = "ESRI Shapefile")
```

## Alternatives

1. You can also find boundary files at the [Humanitarian Data Exchange](https://data.humdata.org/group) (use the Locations tab) or [GADM](https://gadm.org/index.html) (use Maps to find see if there is an appropriate sub-division and then use Data to download all divisions for the country). These two alternative sources don't include a basemap viewer, so plot these on a basemap before sharing with the TTL. 
2. [OSM-Boundaries](https://osm-boundaries.com) is another way to find OpenStreetMap files. Helpfully, it lets you download the file directly from the web instead of requiring an API. However, its dataset is limited and does not include all OpenStreetMap boundaries.