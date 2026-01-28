# Set up session for running maps.R

# 1. Load packages
# 2. Load functions
# 3. Set directories
#   - check to either local or GCS directories
# 4. Load map layer parameters
# 5. Load city parameters
# 6. Read AOI & wards

message("\n=== Starting Setup ===")

# 1. Load packages -------------------------------------------------------------
# Install packages from CRAN using librarian

if (!"librarian" %in% installed.packages()) install.packages("librarian")
librarian::shelf(quiet = T,
  # Read-in
  readxl,
  readr,
  yaml, 

  # Basic
  stringr,
  glue,
  tidyr,
  purrr,
  forcats,
  units,
  dplyr,
  zoo,
  lubridate,

  # Plots
  ggplot2, # 3.5 or higher
  ggrepel,
  directlabels,
  ggh4x,
  ggtext,
  plotly, 
  cowplot,
  ggpackets,
  ggridges,

  # Spatial
  sf,
  rspatial/terra, # Only the github version of leaflet supports terra, in place of raster, which is now required as sp (on which raster depends) is being deprecated
  tidyterra, 
  leaflet, 
  leafem,
  ggspatial, 
  jsonlite,
  geojsonsf,


  # Web
  curl,
  rvest,

  # GCS access
  googleCloudStorageR, 
  gargle
  )

librarian::stock(quiet = T,
  ggnewscale, # 4.10 or higher
  prettymapr
)

# 2. Load functions ------------------------------------------------------------
source("R/fns.R", local = T)

if (!exists("USE_GCS", where = .GlobalEnv)) {
    USE_GCS <<- Sys.getenv("USE_GCS", "false") == "true"
  }


# 3.A Set directories -----------------------------------------------------------
city_dir <- readLines("city-dir.txt")[1]

# subdirectorie pattern
user_input_dir <-     "01-user-input"
process_output_dir <- "02-process-output"
output_dir <-         "03-render-output"

spatial_dir <- paste0(process_output_dir, "/spatial")
fgb_dir <- paste0(process_output_dir, "/spatial-fgb")
tabular_dir <- paste0(process_output_dir, "/tabular")

styled_maps_dir <- file.path(output_dir, "maps/")
charts_dir <- file.path(output_dir, "plots/")

if (!dir.exists(user_input_dir)) dir.create(user_input_dir, recursive = T)
if (!dir.exists(spatial_dir)) dir.create(spatial_dir, recursive = T) 
if (!dir.exists(tabular_dir)) dir.create(tabular_dir, recursive = T) 
if (!dir.exists(fgb_dir)) dir.create(fgb_dir, recursive = T)
if (!dir.exists(styled_maps_dir)) dir.create(styled_maps_dir, recursive = T)
if (!dir.exists(charts_dir)) dir.create(charts_dir, recursive = T)


# 3.B Check GCS -----------------------------------------------------------
# assigning scan-id - can remove if we add scan_id to city_input.yml
scan_id <- Sys.getenv("SCAN_ID", "")

if (scan_id == "") {
  scan_id <- if (city_dir == ".") basename(getwd()) else basename(city_dir)
}

# Validate format and fall back to user-inputs.R if invalid
if (!grepl("^[0-9]{4}-[0-9]{2}-[a-z]+-[a-z-]+$", tolower(scan_id)) ||
    scan_id == "" || is.na(scan_id)) {

  if (file.exists("R/user-inputs.R")) {
    invisible(source("R/user-inputs.R", local = F))
  } else {
    stop("\nCannot determine valid scan_id")
  }
}

message("\nInitializing for ", scan_id)
invisible(NULL)

# If USE GCS, authenticate and use gcs-overrides
message(paste('USE GCS:', USE_GCS))

if(length(list.files(spatial_dir)) < 20) {
  USE_GCS <- TRUE
  message("\nSwitching to GCS mode as local data appears incomplete.")
}


if(USE_GCS) { 
  
  source("R/gcs-auth.R")

  } else  {
  # If USE_GCS is false, reassign all directories to city_dir
  for (var in c("user_input_dir", "process_output_dir", "output_dir", "spatial_dir", "fgb_dir", "tabular_dir", "styled_maps_dir", "charts_dir")) {
    assign(var, file.path(city_dir, get(var)))
  }

}

# setup directories for global data path
source("R/global-data-paths.R")


# 4. Load map layer parameters -------------------------------------------------
# this should be a local file 
layer_params_file <- 'source/layers.yml' # Also used by fns.R
layer_params <- read_yaml(layer_params_file)


# 5. Load city parameters ------------------------------------------------------
city_params <- read_yaml(file.path(user_input_dir, "city_inputs.yml"))
city <- str_to_title(city_params$city_name)
message(glue("City set to {city} (City directory: {city_dir})"))
city_string <- tolower(city) %>% stringr::str_replace_all(" ", "-")
country <- str_to_title(city_params$country_name)

bm_cities_manual <- c(city_params$bm_cities_manual)
nearby_countries_string <- city_params$nearby_countries

basic_info <- fuzzy_read(tabular_dir, "basic_info.yml", read_yaml)
if (length(country) == 0 && is.list(basic_info)) country <- basic_info$country


# 6. Read AOI & wards ----------------------------------------------------------
message("\nReading AOI and wards data...")
# Defining layer because of bug where AOI always includes South Jakarta shapefile;
# ideally would not need to specify like this, for greater flexibility
aoi <- fuzzy_read(user_input_dir, "AOI", layer = city_params$AOI_shp_name) %>%
  project("epsg:4326")
message("AOI Ready!")

wards <- tryCatch(fuzzy_read(user_input_dir, "wards") %>% project("epsg:4326"), error = \(e) NULL)

writeVector(aoi, file.path(fgb_dir, "aoi.fgb"), overwrite = T, filetype = "FlatGeobuf") 

message("Setup complete.\n")