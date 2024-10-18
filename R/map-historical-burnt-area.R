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