school_points <- fuzzy_read(spatial_dir, "school-points", vect)
plots$school_proximity <- plot_static_layer(school_points, "school_points", baseplot = plots$school_zones)

# Health facilities
health_points <- fuzzy_read(spatial_dir, "health-points", vect)
plots$health_proximity <- plot_static_layer(health_points, "health_points", baseplot = plots$health_zones)