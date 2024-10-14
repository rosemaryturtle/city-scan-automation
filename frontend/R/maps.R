# Generating LGCRRP Maps

# setwd("lgcrrp-mille-feuille/frontend")
source("R/setup.R")
source("R/pre-mapping.R")

# Set static map visualization parameters
layer_alpha <- 0.8
map_width <- 6.9
map_height <- 5.9
aspect_ratio <- map_width / map_height

# Define map extent and zoom level
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)
zoom <- round(14.6 + -0.00015 * (sqrt(expanse(aoi)))) + 1
tiles <- annotation_map_tile(type = "cartolight", zoom = zoom, progress = "none")

# Initiate plots list ----------------------------------------------------------
plots <- list()

# Plot AOI & wards -------------------------------------------------------------
if(is.null(wards)) {
  plots$aoi <- plot_layer(aoi_only = T, plot_aoi = T)
} else {
  ward_labels <- site_labels(wards, simplify = F)
  plots$aoi <- plot_layer(aoi_only = T, plot_aoi = F, plot_wards = T) +
    # geom_spatvector_text(data = wards, aes(label = as.numeric(str_extract(WARD_NO, "\\d*$"))))
    geom_spatvector_text(data = ward_labels, aes(label = WARD_NO), size = 2, fontface = "bold")
  save_plot(plot = plots$aoi, filename = "aoi.png",
            directory = styled_maps_dir)
}

# Plot landmarks
landmarks <- fuzzy_read(user_input_dir, "Landmark")
if (inherits(landmarks, "SpatVector")) {
  landmarks <- landmarks %>% project("epsg:4326") %>% select(Name)
  landmarks_df <- mutate(landmarks, x = geom(landmarks)[,"x"], y = geom(landmarks)[,"y"])

  # Combine landmark labels, ward labels, and ward lines, to reduce text overlaps
  landmarks_and_points_to_avoid <-
    rbind(
      mutate(landmarks, label = Name, type = "landmark", fface = "italic", fsize = 1.5),
      mutate(ward_labels, label = WARD_NO, type = "ward", fface = "bold", fsize = 2),
      mutate(as.points(wards) %>% .[rep(c(T, F, F), nrow(.))], label = "", type = "perimeter")
      ) %>%
    mutate(x = geom(.)[,"x"], y = geom(.)[,"y"])
  plots$landmarks <- plot_layer(aoi_only = T, plot_aoi = F, plot_wards = T) +
    geom_spatial_point(data = landmarks_df, crs = "epsg:4326", aes(x = x, y = y), size = 0.25) +
    geom_spatial_text_repel(data = landmarks_and_points_to_avoid, crs = "epsg:4326",
      aes(
        x = x, y = y, fontface = fface, size = fsize,
        label = break_lines(label, width = 12, newline = "\n")),
      segment.size = 0.1, box.padding = 0.1, min.segment.length = 0.2, max.time = 2,
      force_pull = 0.1, max.overlaps = 10,
      lineheight = 0.9) +
    scale_size(range = c(1.5, 2), guide = "none")
  save_plot(plot = plots$landmarks, filename = "landmarks.png",
            directory = styled_maps_dir)
}

# Standard plots ---------------------------------------------------------------
unlist(lapply(layer_params, \(x) x$fuzzy_string)) %>%
  # keep_at("land_cover") %>%
  map2(names(.), \(fuzzy_string, yaml_key) {
    tryCatch({
      data <- fuzzy_read(spatial_dir, fuzzy_string) %>% vectorize_if_coarse()
      plot <- plot_layer(
        data = data, yaml_key = yaml_key,
        plot_aoi = is.null(wards), plot_wards = !is.null(wards))
      plots[[yaml_key]] <<- plot
      message(paste("Success:", yaml_key))
    },
    error = \(e) {
      warning(glue("Error on {yaml_key}: {e}"))
    })
  }) %>% unlist() -> plot_log

# Elevation --------------------------------------------------------------------
elevation_breaks <- fuzzy_read(process_output_dir, "elevation.csv", read_csv, col_types = "cd")$Bin %>%
  str_extract_all("\\d+") %>% unlist() %>% unique() %>% as.numeric()
elevation_data <- fuzzy_read(spatial_dir, layer_params$elevation$fuzzy_string) %>%
        # aggregate_if_too_fine(threshold = 1e6, fun = \(x) Mode(x, na.rm = T)) %>%
        vectorize_if_coarse(threshold = 1e6)
plots$elevation <- plot_layer(data = elevation_data, yaml_key = "elevation", breaks = elevation_breaks)

# Deforestation ----------------------------------------------------------------
deforest <- fuzzy_read(spatial_dir, layer_params$deforest$fuzzy_string, rast)
if (inherits(deforest, c("SpatVector", "SpatRaster"), which = F)) {
  values(deforest) <- values(deforest) + 2000 # Move to pre-mapping
  plots$deforest <- plot_layer(
    data = deforest, yaml_key = "deforest",
    plot_aoi = is.null(wards), plot_wards = !is.null(wards))
  plots$forest_deforest <- plot_layer(deforest, "deforest", baseplot = plots$forest)
}

# Flooding ---------------------------------------------------------------------

plot_flooding <- function(flood_type) {
  file <- fuzzy_read(spatial_dir, glue("{flood_type}_2020.tif$"), paste)
  if (is.na(file)) return(NULL)
  flood_data <- terra::crop(rast(file), vect(static_map_bounds))
  # Temporary fix for if layer is all NAs
  if (all(is.na(values(flood_data)))) values(flood_data)[1] <- 0
  plots[[flood_type]] <<- plot_layer(
    flood_data, yaml_key = flood_type,
    plot_aoi = is.null(wards), plot_wards = !is.null(wards))
  plots[[glue("{flood_type}_population")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$population)
  plots[[glue("{flood_type}_wsf")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$wsf)
  plots[[glue("{flood_type}_infrastructure")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$infrastructure)
}

flooding_yaml_keys <- c("fluvial", "pluvial", "coastal", "combined_flooding")
walk(flooding_yaml_keys, plot_flooding)

# Historical Fire --------------------------------------------------------------
historical_fire_data <- fuzzy_read(spatial_dir, "globfire")
if (inherits(historical_fire_data, c("SpatVector", "SpatRaster"), which = F)) {
  historical_fire_data_3857 <- project(historical_fire_data, "epsg:3857") %>%
    mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
  fire_bbox <- aspect_buffer(st_bbox(historical_fire_data), aspect_ratio, buffer_percent = 0.05)
  fire_bbox_3857 <- st_bbox(st_transform(fire_bbox, crs = "epsg:3857"))

  fire_breaks <- scales::rescale((0:5/5)^3)

  plots$burnt_area <- ggplot() +
    geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
      # coord_sf(expand = F) +
    annotation_map_tile(type = "cartolight", zoom = zoom - 5) +
    stat_density_2d(
      data = historical_fire_data_3857,
      geom = "raster",
      aes(x = x, y = y, fill = after_stat(ndensity)),
      contour = FALSE, n = 200) +
    scale_fill_stepsn(
      name = "History of fire",
      limits = c(0, 1),
      breaks = fire_breaks[-1],
      colors = c("#4B90C1", "#A6C19D", "#FBFA7C", "#EB9148", "#D63228"),
      labels = c("Very low", "Low", "Medium", "High", "Very high"),
      values = breaks_midpoints(fire_breaks),
      guide = "legend",
      na.value = "transparent") +
    geom_spatvector(data = historical_fire_data_3857, shape = 1, color = "black") +
    geom_spatvector(data = aoi, color = "black", fill = NA, linetype = "solid") +
    annotation_north_arrow(style = north_arrow_minimal, location = "br", height = unit(1, "cm")) +
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm")) +        
    theme_custom() +
    coord_sf(
      crs = "epsg:3857",
      xlim = range(historical_fire_data_3857$x),
      ylim = range(historical_fire_data_3857$y),
      expand = F)

  plots$burnt_area_smooth <- plots$burnt_area +
    scale_fill_gradientn(
      name = "History of fire",
      limits = c(0, 1),
      breaks = fire_breaks[-1],
      colors = c("#4B90C1cc", "#A6C19Dcc", "#FBFA7Ccc", "#EB9148cc", "#D63228cc"),
      labels = c("Very low", "Low", "Medium", "High", "Very high"),
      values = (fire_breaks[-1]),
      guide = "legend",
      na.value = "transparent")
}

# Save plots -------------------------------------------------------------------
plots %>% walk2(names(.), \(plot, name) {
  save_plot(plot, filename = glue("{name}.png"), directory = styled_maps_dir)
})

unmapped <- setdiff(c(names(layer_params), "aoi", "forest_deforest", "burnt_area"), names(plots))
if (length(unmapped) > 0) warning(paste(length(unmapped), "layers not mapped (not counting flood overlays):\n-", paste(unmapped, collapse = "\n- ")))
