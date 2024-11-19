school_points <- fuzzy_read(spatial_dir, "school-points", vect)
if (inherits(school_points, "SpatVector")) {
  plots$school_proximity <- plot_static_layer(school_points, "school_points", baseplot = plots$school_zones)
  message("Success: schools_proximity")
}
# Health facilities
health_points <- fuzzy_read(spatial_dir, "health-points", vect)
if (inherits(health_points, "SpatVector")) {
  plots$health_proximity <- plot_static_layer(health_points, "health_points", baseplot = plots$health_zones)
  message("Success: health_proximity")
}