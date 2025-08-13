# Finding an AOI

The AOI, or area of interest, is the polygon, or polygons, that defines the boundaries for a City Scan. Except for a few analysis layers, data is only collected and visualized for the area within the AOI. This focus improves legibility and clarifies narratives, but it also perpetuates the false notion that cities are disconnected from their surrounding areas. Physical and demographic phenomena rarely follow administrative divisions, and what happens outside the AOI often affects and is affected by what happens inside the AOI. Sometimes an AOI will correspond to the city's administrative boundaries, but these boundaries are often hard to find or verify.

For finding an AOI, there are multiple possible sources:

- Geoboundaries, via API or [geoboundaries.org](https://www.geoboundaries.org/)
- OpenStreetMap, via API or [osm-boundaries.com](https://osm-boundaries.com)
- GADM, via API or [gadm.org](https://gadm.org/index.html)
- Humanitarian Data Exchange

Once you have found a possible AOI, confirm it with the TTL who requested the City Scan by sharing an image of the AOI on a vector or orthophoto basemap. With OpeenStreetMap, you can grab a screenshot from [Nominatim search engine](https://nominatim.openstreetmap.org/ui/search.html) or [OSM Boundaries](https://osm-boundaries.com) to share before actually downloading the AOI.

As of now, AOIs must be saved as a shapefile for use in the backend processing. If the file downloaded is of another format, you must convert it to a shapefile.

For specific steps on using the Geoboundaries or OpenStreetMap APIs, see the sections below.

## Geoboundaries

I find the easiest way to search for and retrieve an AOI is with Geoboundaries' API. In R, you can use the following function to search for a city and download its AOI. To use the function, you must provide the alphabetic ISO code for the country (e.g., "CMR" for Cameroon) and a string that matches the city name. The string can be regex to account for various spellings of the city name (but forward slashes must be duplicated: e.g., "\\s" instead of "\s").

```r
librarian::shelf(httr2, glue, terra, stringr, magrittr)
get_geoboundary <- function(iso, string, boundary_type = "ADM3", release_type = "gbOpen", response = F) {
  # browser()
  req <- httr2::request(
    glue::glue("https://www.geoboundaries.org/api/current/{release_type}/{iso}/{boundary_type}/")) %>%
    httr2::req_perform()
  resp <- httr2::resp_body_json(req)
  if (response) return(resp)
  v <- terra::vect(resp$simplifiedGeometryGeoJSON)
  v[ stringr::str_detect(tolower(v$shapeName), string) ]
}
get_geoboundary("CMR", "yaound")
```

You can also retrieve all available boundaries for a country and then manually look through them to find relevant boundaries:

```r
cameroon_boundaries <- get_geoboundary("CMR", ".")
sort(cameroon_boundaries$shapeName)
```

The function defaults to the third-level administrative boundary (ADM3), which is usually the city, but you can change it to ADM1 or ADM2: `get_geoboundary("CMR", "yaound", boundary_type = "ADM2")`.

## OpenStreetMap

Nominatim is a search engine for OpenStreetMap, which lets you quickly find polygons for cities. It is, however, impossible to download the found polygons directly, so you'll need to download from OpenStreetMap with an API. With R, you can use the osmdata package. 

1. Search for AOI on https://nominatim.openstreetmap.org/ui/search.html and share screenshot with client TTL for approval.
2. Using the city name listed on Nominatim, download AOI using R:

```r
librarian::shelf(osmdata, sf, magrittr)
get_osm_boundary <- function(city, country) {
  # Limit search to a bounding box around the city
  bounding_box <- getbb(paste(city, country)) %>% (\(x) {
    matrix(c(-1, -1, 1, 1), nrow = 2) * .01 * x + x
  })()

  # Get all OpenStreetMap features with the city name
  data <- opq(bbox = bounding_box) %>%
    add_osm_feature(key = "name:en", value = city, value_exact = FALSE)  %>%
    osmdata_sf()
}

# Use the name of the city as it appears in Nominatim; make note of whether you 
# are using the English name (name:en), or a different language's name (e.g., 
# name:fr for French), which you can find in the search results "details".
data <- get_osm_boundary("Yaoundé", "Cameroon")

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