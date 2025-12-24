# frontend data processing

if (dir.exists("frontend")) setwd("frontend")
source("R/setup.R")

Sys.setenv(GOOGLE_APPLICATION_CREDENTIALS = ".access/city-scan-gee-test-5c6f7cb48c49.json")

# Functions are defined at top; SCROLL TO BOTTOM for function calls

# Rules / practices for data collection and stats functions:
# - For collect functions, arguments should include
#   - aoi (if you don't want to mask, or want to use larger extent, just pass a larger aoi)
#   - write
# - For stats functions, arguments should include
#   - x, which is either the data object itself or a path to where it is stored
# - When the raster file is written to disk, re-read the file before returning
#   to reduce memory usage
# - When possible, write stats functions generically (such as stats_cumulative_area()
#   instead of stats_wsf_tracker())
# - Should we attach metadata text to the output files?
# - Should we mask here or later? Now for analysis reasons?

#### WSF Tracker ----------------------------------------------------------------

# gcs_folder <- "gs://city-scan-global-private/wsf_tracker"
# on_gcs <- system2('bash', c('-c', shQuote(sprintf('gcloud storage ls "%s"', gcs_folder))), stdout = TRUE, stderr = TRUE)

# wsf_file_list[basename(wsf_file_list) %in% basename(on_gcs)]
# on_gcs[basename(on_gcs) %in% basename(wsf_file_list)]

# rast(file.path(source, basename(on_gcs)[2]))

# Currently runs locally and only for Africa (other data is downloaded already)
# collect_wsf_tracker <- function(aoi, output_dir = NULL, source = "/Volumes/notkin-ssd/world-bank/data/wsf-tracker/Global") {
collect_wsf_tracker <- function(aoi, output_dir = NULL, source = "/vsigs/city-scan-global-private/wsf_tracker") {

  # Get extent
  aoi_ext <- ext(aoi)
  minx <- aoi_ext[1]
  maxx <- aoi_ext[2]
  miny <- aoi_ext[3]
  maxy <- aoi_ext[4]

  # Create sequences for x and y
  x_seq <- seq(floor(minx - minx %% 2), ceiling(maxx), by = 2)
  y_seq <- seq(floor(miny - miny %% 2), ceiling(maxy), by = 2)

  # # Faster but less legible
  # x_seq <- 2 * head(seq(floor(minx/2), ceiling(maxx/2)), -1)
  # y_seq <- 2 * head(seq(floor(miny/2), ceiling(maxy/2)), -1)

  # Create all combinations of x and y
  xy_grid <- expand.grid(x = x_seq, y = y_seq)

  # Find relevant tiles
  wsf_file_list <- file.path(source, glue("WSFtracker_20160701-20250701_{xy_grid$x}_{xy_grid$y}.tif"))

  # Merge tiles if needed, crop to AOI extent
  if (length(wsf_file_list) == 1) {
    # file.copy(wsf_file_list, file.path(tempdir(), basename(wsf_file_list)), overwrite = TRUE)
    wsf_tracker <- crop(rast(wsf_file_list), aoi, mask = T)
  } else {
    wsf_tracker_sprc <- sprc(wsf_file_list)
    wsf_tracker <- merge(wsf_tracker_sprc, filename = file.path(tempdir(), "wsf_tracker_20160701-20250701_merge.tif"), overwrite = TRUE)
    wsf_tracker <- crop(wsf_tracker, aoi, mask = T)
  }

  # Clean data for mapping
  NAflag(wsf_tracker) <- 0
  wsf_tracker$era <- seq(from = 2016.5, by = .5, length = global(wsf_tracker$mode, "max", na.rm = TRUE))[wsf_tracker$mode[,,1]]

  # Save map-ready output
  if (!is.null(output_dir)) {
    path <- file.path(output_dir, paste0(city_string, "_wsf_tracker.tif"))
    wsf_tracker %>% writeRaster(path, overwrite = TRUE, datatype = "FLT4S")
    wsf_tracker <- rast(path)
  }

  return(wsf_tracker)
}

# Create table of cumulative built-up area over time
stats_wsf_tracker <- function(x) {
  if (is.character(x)) x <- rast(x)
  x$area <- cellSize(x)
  df <- as_tibble(x) %>%
      filter(!is.na(era)) %>%
      arrange(era) %>%
      summarize(.by = era, AREA_sq_km = sum(area) / 1e6) %>%
      mutate(AREA_sq_km = cumsum(AREA_sq_km)) %>%
      mutate(.keep = "unused", year = floor(era), month = if_else(era %% 1 == 0, 1L, 7L)) %>%
      select(year, month, AREA_sq_km)
  return(df)
}

#### WorldPop ------------------------------------------------------------------

collect_worldpop <- function(aoi, output_dir = NULL, source = "/vsigs/city-scan-global-public/world_population/WorldPop-Global-2") {

  iso <- countrycode::countrycode(country, "country.name", "iso3c")
  years <- 2015:2030

  # # For downloading from WorldPop directly
  # # Task: Only download from WorldPop if the files don't already exist on cloud
  # # Check if files exist on cloud and if not, proceed, uploading them to cloud
  # temp_dir <- "WorldPop-Global2"
  # dir.create(temp_dir, showWarnings = F)
  # country_rasters_urls <- glue::glue("https://data.worldpop.org/GIS/Population/Global_2015_2030/R2025A/{years}/{iso}/v1/100m/constrained/{tolower(iso)}_pop_{years}_CN_100m_R2025A_v1.tif")
  # rast_paths <- file.path(temp_dir, basename(country_rasters_urls))
  # map2(country_rasters_urls[!file.exists(rast_paths)], rast_paths[!file.exists(rast_paths)], \(url, local) {
  #   curl::curl_download(url, destfile = local)
  # })

  rast_paths <- glue::glue("{source}/{tolower(iso)}_pop_{years}_CN_100m_R2025A_v1.tif")
  country_rasters <- rast(rast_paths)
  names(country_rasters) <- str_extract(names(country_rasters), "pop_\\d{4}")
  # country_rasters <- reduce(country_rasters, c)

  # Crop and mask to AOI
  worldpop_2015_2030 <- crop(country_rasters, aoi, mask = T)
  
  if (!is.null(output_dir)) {
    path <- file.path(output_dir, paste0(city_string, "_worldpop_2015_2030.tif"))
    writeRaster(worldpop_2015_2030, filename = path, overwrite = T)
    # writeRaster(worldpop_2015_2030$pop_2025, filename = file.path(output_dir, paste0(city_string, "_worldpop_2025.tif")), overwrite = T)
    worldpop_2015_2030 <- rast(path)
  }

  return(worldpop_2015_2030)
}

stats_worldpop <- function(x) {
  if (is.character(x)) x <- rast(x)
  worldpop_df <- as_tibble(x) %>%
    summarize(.by = NULL, across(everything(), ~ sum(.x, na.rm = T))) %>%
    t() %>% as.data.frame() %>%
  mutate(year = rownames(.), population = V1, .keep = "none") %>%
  as_tibble()
  return(worldpop_df)
}

#### Air quality ---------------------------------------------------------------

collect_air <- function(aoi, output_dir = NULL, source = "/vsigs/city-scan-global-public/air_quality") {

  years <- 1998:2022
  rast_paths <- glue::glue("{source}/sdei-global-annual-gwr-pm2-5-modis-misr-seawifs-viirs-aod-v5-gl-04-{years}-geotiff.tif")
  air <- crop(rast(rast_paths), aoi, mask = T)

  air$mean <- app(air, "mean", na.rm = TRUE) %>% setNames("mean_1998_2022")
  air$mean_2013_2022 <- app(air[[16:25]], "mean", na.rm = TRUE)
  air$trend_2013_2022 <- regress(air[[16:25]], x = 2013:2022, na.rm = TRUE)$x
  air <- select(air, mean, mean_2013_2022, trend_2013_2022, everything())

  if (is.character(output_dir)) {
    path <- file.path(output_dir, paste0(city_string, "_air_quality_pm2_5.tif"))
    writeRaster(air, filename = path, overwrite = TRUE)
    air <- rast(path)
  }
  return(air)
}

stats_air <- function(x) {
  if (is.character(x)) x <- rast(x)
  bind_cols(
      global(x, c("max", "mean"), na.rm = TRUE),
      global(x, median, na.rm = TRUE)) %>%
    mutate(year = str_extract(rownames(.), "\\d{4}")) %>%
    as_tibble() %>%
    select(year, pm2_5_max = max, pm2_5_mean = mean, pm2_5_median = global)
}

#### Function calls ------------------------------------------------------------

wsf_tracker <- collect_wsf_tracker(aoi, spatial_dir)
stats_wsf_tracker(wsf_tracker) %>%
  write_csv(file.path(tabular_dir, paste0(city_string, "_wsf_tracker.csv")))

worldpop <- collect_worldpop(aoi, spatial_dir)
stats_worldpop(worldpop) %>%
  write_csv(file.path(tabular_dir, paste0(city_string,"_worldpop_2015_2030.csv")))

air <- collect_air(aoi, spatial_dir)
stats_air(air) %>%
  write_csv(file.path(tabular_dir, paste0(city_string, "_air_quality_pm2_5.csv")))
