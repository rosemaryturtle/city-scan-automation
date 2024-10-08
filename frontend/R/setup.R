# Set up session for running maps.R and plots.R

# 1. Load packages
# 2. Load functions
# 3. Set directories
# 4. Load city parameters
# 5. Read AOI & wards
# 6. CCKP data: set SSP numbers and list file paths

# 1. Load packages -------------------------------------------------------------
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

# 2. Load functions ------------------------------------------------------------
source("source/fns.R")

# 3. Set directories -----------------------------------------------------------
city_dir <- file.path("mnt/", readLines("city-dir.txt"))
user_input_dir <- file.path(city_dir, "01-user-input/")
process_output_dir <- file.path(city_dir, "02-process-output/")
spatial_dir <- file.path(process_output_dir, "spatial/")
tabular_dir <- file.path(process_output_dir, "tabular/")
output_dir <- file.path(city_dir, "03-render-output/")
styled_maps_dir <- file.path(output_dir, "styled-maps/")
charts_dir <- file.path(output_dir, "charts/")

dir.create(styled_maps_dir, recursive = T)
dir.create(charts_dir, recursive = T)

# 4. Load city parameters ------------------------------------------------------
city_params <- read_yaml(file.path(user_input_dir, "city_inputs.yml"))
city <- city_params$city_name
city_string <- tolower(city) %>% stringr::str_replace_all(" ", "-")
country <- city_params$country_name

# 5. Read AOI & wards ----------------------------------------------------------
aoi <- fuzzy_read(user_input_dir, "AOI") %>% project("epsg:4326")

# 6. CCKP data: set SSP numbers and list file paths
scenario_numbers <- c(126, 245, 370)
generic_paths <- generate_generic_paths()
