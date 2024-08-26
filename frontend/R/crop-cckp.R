# Crop CCKP raster to Bangladesh's extent

source("R/setup.R")

boundaries_admin0_path <- "/Users/bennotkin/Documents/world-bank/WB_Boundaries_GeoJSON_lowres/WB_countries_Admin0_lowres.geojson"
country_extent <- ext(vect(boundaries_admin0_path) %>% .[str_detect(.$FORMAL_EN, "Bang")])

codes <- c("tas", "txx", "wsdi", "csdi", "r20mm", "r50mm", "hdtr", "rx5day-extremes")
paste0("source-data/", codes, "-bgd") %>% lapply(dir.create)

lapply(codes, \(code) {
  # browser()
  list.files(file.path("source-data/", code), full.names = T) %>%
  # .[1] %>%
  lapply(\(path) {
    # browser()
    read_path <- file.path(
      "source-data", code,
      str_extract(c(path), "[^/]+$"))
    write_path <- file.path(
      "source-data", paste0(code, "-bgd"),
      str_extract(c(path), "[^/]+$"))
    r <- rast(read_path)
    r <- terra::crop(r, country_extent, snap = "out")
    # browser()
    writeCDF(r, write_path, overwrite = T)
  })
})