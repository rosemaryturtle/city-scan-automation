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

# SSP numbers
scenario_numbers <- c(126, 245, 370)

# Core functions
generate_generic_paths <- function() {
    cmip6_paths <- paste0(
      "cmip6-x0.25/{codes}/ensemble-all-ssp", scenario_numbers,
      "/timeseries-{codes}-annual-mean_cmip6-x0.25_ensemble-all-ssp", scenario_numbers,
      "_timeseries-smooth_") %>%
    lapply(\(x) paste0(x, c(
      "median", "p10", "p90"
      ))) %>%
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

tolatin <- function(x) stringi::stri_trans_general(x, id = "Latin-ASCII")


ggdonut <- function(data, category_column, quantities_column, colors, title) {
  data <- as.data.frame(data) # tibble does weird things with data frame, not fixing now
  data <- data[!is.na(data[,quantities_column]),]
  data <- data[data[,quantities_column] > 0,]
  # data <- data[rev(order(data[,quantities_column])),]
  data$decimal <- data[,quantities_column]/sum(data[,quantities_column], na.rm = T)
  data$max <- cumsum(data$decimal) 
  data$min <- lag(data$max)
  data$min[1] <- 0
  data$label <- scales::label_percent(0.1)(data$decimal)
  data$label[data$decimal < .02] <- "" 
  data$label_position <- (data$max + data$min) / 2
  data[,category_column] <- factor(data[,category_column], levels = data[,category_column])
  breaks <- data[data[,"decimal"] > 0.2,] %>%
    { setNames(.$label_position, .[,category_column]) }

  donut_plot <- ggplot(data) +
    geom_rect(
      aes(xmin = .data[["min"]], xmax = .data[["max"]], fill = .data[[category_column]],
      ymin = 0, ymax = 1),
      color = "white") +
    geom_text(y = 0.5, aes(x = label_position, label = label)) +
    # theme_void() +
    # scale_x_continuous(guide = "none", name = NULL) +
    scale_y_continuous(guide = "none", name = NULL) +
    scale_fill_manual(values = colors) +
    scale_x_continuous(breaks = breaks, name = NULL) +
    coord_radial(expand = F, inner.radius = 0.3) +
    guides(theta = guide_axis_theta(angle = 0)) +
    labs(title = paste(city, title)) +
    theme(axis.ticks = element_blank())
  return(donut_plot)
}
