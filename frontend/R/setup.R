# Packages

# Install packages from CRAN using librarian
if (!"librarian" %in% installed.packages()) install.packages("librarian")
librarian::shelf(
  # Read-in
  readxl,
  readr,
  yaml, 
  
  # Plots
  ggplot2, # 3.5 or higher
  ggrepel,
  directlabels,
  ggh4x,
  plotly, 
  cowplot,

  # Spatial
  sf,
  terra,
  tidyterra, 
  leaflet, 
  ggspatial, 

  # Web
  curl,
  rvest,

  # Basic
  stringr,
  glue,
  tidyr,
  purrr,
  forcats,
  units,
  dplyr)

librarian::stock(
  ggnewscale, # 4.10 or higher
  pammtools) # Only used for geom_stepribbon(), not currently used

source("source/fns.R")
source("source/helpers.R")

# Set directories
city_dir <- file.path("mnt/", readLines("city-dir.txt"))
user_input_dir <- file.path(city_dir, "01-user-input/")
process_output_dir <- file.path(city_dir, "02-process-output/")
spatial_dir <- file.path(process_output_dir, "spatial/")
output_dir <- file.path(city_dir, "03-render-output/")
# styled_maps_dir <- file.path(output_dir, "styled-maps/")
styled_maps_dir <- file.path("maps")

# Load city parameters
city_params <- read_yaml(file.path(user_input_dir, "city_inputs.yml"))
# cities <- list.files("cities")
city <- city_params$city_name
city_string <- tolower(city) %>% stringr::str_replace_all(" ", "-")
country <- city_params$country_name

# Read AOI
aoi <- fuzzy_read(user_input_dir, "AOI")

