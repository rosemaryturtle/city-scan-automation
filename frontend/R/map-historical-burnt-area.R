# Historical Fire --------------------------------------------------------------
historical_fire_params <- prepare_parameters("burnt_area")
historical_fire_data <- fuzzy_read(spatial_dir, historical_fire_params$fuzzy_string)
if (inherits(historical_fire_data, c("SpatVector", "SpatRaster"), which = F)) {
  historical_fire_data_3857 <- project(historical_fire_data, "epsg:3857") %>%
     mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
  fire_bbox <- aspect_buffer(historical_fire_data, aspect_ratio, buffer_percent = 0.05)

  fire_breaks <- scales::rescale((0:5/5)^3)

  plots$burnt_area <- ggplot() +
    geom_spatvector(data = project(static_map_bounds, "epsg:3857"), fill = NA, color = NA) +
      # coord_sf(expand = F) +
    annotation_map_tile(type = "cartolight", zoom = get_zoom_level(fire_bbox, cap = 8)) +
    stat_density_2d(
      data = historical_fire_data_3857,
      geom = "raster",
      aes(x = x, y = y, fill = after_stat(ndensity)),
      contour = FALSE, n = 200) +
    scale_fill_stepsn(
      name = format_title(historical_fire_params$title, historical_fire_params$subtitle),
      limits = c(0, 1),
      breaks = fire_breaks[-1],
      colors = historical_fire_params$palette,
      labels = historical_fire_params$labels,
      values = breaks_midpoints(fire_breaks),
      guide = "legend",
      na.value = "transparent") +
    geom_spatvector(data = historical_fire_data_3857, shape = 1, color = "black") +
    geom_spatvector(data = aoi, color = "black", fill = NA, linetype = "solid") +
    annotation_north_arrow(style = north_arrow_minimal, location = "br", height = unit(1, "cm")) +
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm")) +        
    theme_custom() +
    coord_3857_bounds(extent = fire_bbox, expansion = 0.6)

#   plots$burnt_area_smooth <- plots$burnt_area +
#     scale_fill_gradientn(
#       name = "History of fire",
#       limits = c(0, 1),
#       breaks = fire_breaks[-1],
#       colors = c("#4B90C1cc", "#A6C19Dcc", "#FBFA7Ccc", "#EB9148cc", "#D63228cc"),
#       labels = c("Very low", "Low", "Medium", "High", "Very high"),
#       values = (fire_breaks[-1]),
#       guide = "legend",
#       na.value = "transparent")
}