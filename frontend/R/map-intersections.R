intersection_nodes <- fuzzy_read(spatial_dir, layer_params$intersections$fuzzy_string, layer = "nodes")
if (inherits(intersection_nodes, "SpatVector")) {
  intersection_nodes <- intersection_nodes %>%
    project("epsg:3857") %>%
    mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
  intersection_params <- prepare_parameters("intersections")
  p <- ggplot() +
    geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
    annotation_map_tile(type = "cartolight", zoom = zoom_level) +
    stat_density_2d(
      data = intersection_nodes,
      geom = "raster",
      aes(x = x, y = y, fill = after_stat(ndensity)),
      contour = FALSE, n = 200) +
    scale_fill_gradient(
      # limits = c(0.1, 1),
      low = intersection_params$palette[1], high = intersection_params$palette[2],
      name = format_title(intersection_params$title, intersection_params$subtitle),
      na.value = "transparent") +
    annotation_north_arrow(style = north_arrow_minimal, location = "br", height = unit(1, "cm")) +
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm")) +        
    theme_custom() +
    theme_legend(data = intersection_nodes, params = intersection_params) +
  geom_spatvector(data = aoi, fill = NA, linetype = "solid", linewidth = .4)
  if (!is.null(wards)) p <- p + geom_spatvector(data = wards, color = "grey30", fill = NA, linetype = "solid", linewidth = .25)
  plots$intersections <- p + coord_3857_bounds(static_map_bounds)
  message("Success: intersections")
}
