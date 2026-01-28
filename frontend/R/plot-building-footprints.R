#!/usr/bin/env Rscript
# Plot building footprints for any city
# Usage: Rscript plot-building-footprints.R <city-directory-name>
# Example: Rscript plot-building-footprints.R 2025-10-senegal-matam

# Load required libraries
suppressPackageStartupMessages({
  library(terra)
  library(ggplot2)
  library(dplyr)
  library(tidyterra)
  library(stringr)
})

# Helper function to calculate quadkeys
get_quadkey <- function(lat, lng, zoom) {
  x <- as.integer((lng + 180) / 360 * (2^zoom))
  y <- as.integer((1 - log(tan(pi/180 * lat) + 1 / cos(pi/180 * lat)) / pi) / 2 * (2^zoom))
  quadkey <- ""
  for (i in seq(zoom, 1, -1)) {
    digit <- 0
    mask <- bitwShiftL(1, i - 1)
    if (bitwAnd(x, mask) != 0) {
      digit <- digit + 1
    }
    if (bitwAnd(y, mask) != 0) {
      digit <- digit + 2
    }
    quadkey <- paste0(quadkey, digit)
  }
  quadkey
}

# Extract country from directory name
extract_country <- function(city_dir_name) {
  match <- str_match(city_dir_name, "\\d{4}-\\d{2}-([a-z]+)-")
  if (!is.na(match[1, 2])) {
    # Capitalize first letter
    country <- match[1, 2]
    return(paste0(toupper(substr(country, 1, 1)), substr(country, 2, nchar(country))))
  }
  return(NULL)
}

# Extract city name from directory
extract_city <- function(city_dir_name) {
  match <- str_match(city_dir_name, "\\d{4}-\\d{2}-[a-z]+-(.+)$")
  if (!is.na(match[1, 2])) {
    city <- match[1, 2]
    return(paste0(toupper(substr(city, 1, 1)), substr(city, 2, nchar(city))))
  }
  return("city")
}

# Main script
main <- function() {
  # Get command line arguments
  args <- commandArgs(trailingOnly = TRUE)

  if (length(args) < 1) {
    cat("Usage: Rscript plot-building-footprints.R <city-directory-name>\n")
    cat("Example: Rscript plot-building-footprints.R 2025-10-senegal-matam\n")
    quit(status = 1)
  }

  city_dir_name <- args[1]

  # Set up paths
  script_dir <- getwd()
  city_dir <- file.path(script_dir, "mnt", city_dir_name)
  building_tiles_dir <- file.path(script_dir, "building-tiles")

  # Validate paths
  if (!dir.exists(city_dir)) {
    cat("❌ Error: City directory not found:", city_dir, "\n")
    quit(status = 1)
  }

  aoi_path <- file.path(city_dir, "01-user-input/AOI")
  if (!dir.exists(aoi_path)) {
    cat("❌ Error: AOI not found:", aoi_path, "\n")
    quit(status = 1)
  }

  # Extract country and city names
  country <- extract_country(city_dir_name)
  city_name <- extract_city(city_dir_name)

  if (is.null(country)) {
    cat("❌ Error: Could not extract country from directory name:", city_dir_name, "\n")
    cat("Expected format: YYYY-MM-country-city (e.g., 2025-10-senegal-matam)\n")
    quit(status = 1)
  }

  cat("📍 Processing:", city_dir_name, "\n")
  cat("🌍 Country:", country, "\n")
  cat("🏙️  City:", city_name, "\n\n")

  # Read AOI
  cat("📂 Reading AOI...\n")
  aoi <- vect(aoi_path)
  focus <- ext(aoi)
  cat("  Extent:", paste(as.vector(focus), collapse = ", "), "\n\n")

  # Check for roads data
  cat("🛣️  Reading road network...\n")
  roads_path <- file.path(city_dir, "02-process-output/spatial/edges-edit.gpkg")

  if (!file.exists(roads_path)) {
    cat("⚠️  Warning: Roads file not found, will plot without roads\n")
    cat("  Looking for:", roads_path, "\n")
    roads <- NULL
  } else {
    roads <- vect(roads_path)
    roads <- roads[focus]  # Fast extent-based clip
    cat("  ✓ Loaded", nrow(roads), "road segments\n\n")
  }

  # Get quadkeys
  cat("🔢 Calculating quadkeys...\n")
  focus_vect <- vect(focus, crs = crs(aoi))
  quadkeys <- unique(apply(geom(focus_vect), 1, function(x) get_quadkey(x["y"], x["x"], 9)))
  cat("  Quadkeys:", paste(quadkeys, collapse = ", "), "\n\n")

  # Load building data
  cat("🏢 Loading building footprints...\n")
  buildings_list <- lapply(quadkeys, function(qk) {
    qk_char <- as.character(as.numeric(qk))
    pattern <- paste0(country, "-", qk_char, "\\.fgb")
    files <- list.files(building_tiles_dir, pattern = pattern, full.names = TRUE)

    if (length(files) == 0) {
      cat("  ⚠️  No file found for quadkey", qk_char, "\n")
      cat("  Expected:", file.path(building_tiles_dir, paste0(country, "-", qk_char, ".fgb")), "\n")
      return(NULL)
    }

    cat("  Loading", basename(files[1]), "...\n")
    v <- vect(files[1], extent = focus)
    return(v)
  })

  # Remove NULL entries and combine
  buildings_list <- buildings_list[!sapply(buildings_list, is.null)]

  if (length(buildings_list) == 0) {
    cat("❌ Error: No building data loaded!\n")
    cat("Make sure to run: python download-buildings.py", city_dir_name, "\n")
    quit(status = 1)
  }

  buildings <- do.call(rbind, buildings_list)
  cat("  ✓ Loaded", nrow(buildings), "buildings\n\n")

  # Create the plot
  cat("🎨 Creating plot...\n")
  p <- ggplot() +
    geom_spatvector(data = buildings, color = NA, fill = "#FF9C28") +
    theme_void() +
    theme(panel.background = element_rect(fill = "black"))

  # Add roads if available
  if (!is.null(roads)) {
    p <- p + geom_spatvector(data = roads, color = "white", size = 0.0125)
  }

  cat("  ✓ Plot created\n\n")

  # Save the plot
  output_dir <- file.path(city_dir, "03-render-output/maps")
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
    cat("  Created output directory:", output_dir, "\n")
  }

  output_file <- file.path(output_dir, paste0(tolower(city_name), "_building_footprints.png"))
  cat("💾 Saving plot...\n")
  cat("  Output:", output_file, "\n")

  ggsave(
    filename = output_file,
    plot = p,
    width = 8.77,
    height = 7.55,
    dpi = 200
  )

  file_size <- file.info(output_file)$size / (1024 * 1024)  # MB
  cat("\n✅ Success!\n")
  cat("  📊", nrow(buildings), "buildings plotted\n")
  cat("  💾", sprintf("%.1f", file_size), "MB\n")
  cat("  📁", output_file, "\n")
}

# Run main function
main()
