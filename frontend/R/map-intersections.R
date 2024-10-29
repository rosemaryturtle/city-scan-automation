intersection_nodes <- fuzzy_read(spatial_dir, "nodes.shp$") %>%
  project("epsg:3857") %>%
  mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
intersection_params <- prepare_parameters("intersections")
plots$intersections <- ggplot() +
  geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
  annotation_map_tile(type = "cartolight", zoom = zoom_level) +
  stat_density_2d(
    data = intersection_nodes,
    geom = "raster",
    aes(x = x, y = y, fill = after_stat(ndensity)),
    contour = FALSE, n = 200) +
    geom_sf(data = aoi, fill = NA, linetype = "dashed", linewidth = .5) + 
    coord_3857_bounds() +
    theme_custom() +
  scale_fill_gradient(
    # limits = c(0.1, 1),
    low = intersection_params$palette[1], high = intersection_params$palette[2],
    name = format_title(intersection_params$title, intersection_params$subtitle),
    na.value = "transparent")