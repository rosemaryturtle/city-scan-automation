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
tabular_dir <- file.path(process_output_dir, "tabular/")
output_dir <- file.path(city_dir, "03-render-output/")
styled_maps_dir <- file.path(output_dir, "styled-maps/")
charts_dir <- file.path(output_dir, "charts/")

# Load city parameters
city_params <- read_yaml(file.path(user_input_dir, "city_inputs.yml"))
# cities <- list.files("cities")
city <- city_params$city_name
city_string <- tolower(city) %>% stringr::str_replace_all(" ", "-")
country <- city_params$country_name

# Read AOI & wards
aoi <- fuzzy_read(user_input_dir, "AOI") %>% project("epsg:4326")
wards <- fuzzy_read(user_input_dir, "wards") %>% project("epsg:4326")
# SSP numbers
scenario_numbers <- c(126, 245, 370)

# Core functions
generate_generic_paths <- function() {
    cmip6_paths <- paste0(
      "cmip6-x0.25/{codes}/ensemble-all-ssp", scenario_numbers,
      "/timeseries-{codes}-annual-mean_cmip6-x0.25_ensemble-all-ssp", scenario_numbers,
      "_timeseries-smooth_") %>%
    lapply(\(x) paste0(x, c("median", "p10", "p90"))) %>%
    unlist() %>%
    paste0("_2015-2100.nc")

  era5_paths <- "era5-x0.25/{codes}/era5-x0.25-historical/timeseries-{codes}-annual-mean_era5-x0.25_era5-x0.25-historical_timeseries_mean_1950-2022.nc"

  paths <- c(cmip6_paths, era5_paths)
  return(paths)
}
generic_paths <- generate_generic_paths()

# Extract time series data
extract_ts <- \(file) {
    r <- rast(file)
    terra::extract(r, aoi, snap = "out", exact = T) %>%
      mutate(fraction = fraction/sum(fraction)) %>%
      mutate(across(-c(ID, fraction), \(x) fraction * x)) %>%
      summarize(across(-c(ID, fraction), \(x) sum(x))) %>%
      unlist() %>%
      { tibble(date = time(r), value = ., file = file) }
}
