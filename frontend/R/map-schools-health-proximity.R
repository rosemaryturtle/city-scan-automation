# Map isochrones

# Schools
tryCatch_named("school_proximity", {
  school_points <- fuzzy_read(spatial_dir, "school-points", vect)
  if (inherits(school_points, "SpatVector")) {
    plots$school_proximity <- plot_static_layer(school_points, "school_points", baseplot = plots$school_zones)
  }
})
# Health facilities
tryCatch_named("health_proximity", {
  health_points <- fuzzy_read(spatial_dir, "health-points", vect)
  if (inherits(health_points, "SpatVector")) {
    plots$health_proximity <- plot_static_layer(health_points, "health_points", baseplot = plots$health_zones)
  }
})

c("public_space", "waste", "transportation", "sanitation", "electricity", "sez", "water", "communication") %>%
  walk(\(x) {
    points <- fuzzy_read(spatial_dir, paste0(x, "_POI"))
    label <- layer_params[[paste0(x, "_points")]]$label
    p <- plots[[paste0(x, "_zones")]]
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      plots[[paste0(x, "_proximity")]] <<- p +
          geom_spatvector(data = points, aes(color = label), size = 1) +
          scale_color_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature") +
          coord_3857_bounds(static_map_bounds)
    }
  })
