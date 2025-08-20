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

# Isochrones with unlabeled points
c("public_space", "waste", "transportation", "sanitation", "electricity", "water", "communication") %>%
  walk(\(x) {
    points <- fuzzy_read(spatial_dir, paste0(x, "_POI"))
    group <- layer_params[[paste0(x, "_points")]]$label
    p <- plots[[paste0(x, "_zones")]]
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      plots[[paste0(x, "_proximity")]] <<- p +
        geom_spatvector(data = points, aes(color = group), size = 1) +
        scale_color_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature") +
        coord_3857_bounds(static_map_bounds)
    }
  })

# Isochrones with labeled points
c("sez") %>%
  walk(\(x) {
    points <- fuzzy_read(spatial_dir, paste0(x, "_POI"))
    group <- layer_params[[paste0(x, "_points")]]$label
    p <- plots[[paste0(x, "_zones")]]
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      # Convert to sf for ggrepel
      points_sf <- points %>%
        mutate(.before = 1, text = pull(points[layer_params[[paste0(x, "_points")]]$data_variable])) %>%
        st_as_sf()

      plots[[paste0(x, "_proximity")]] <<- p +
        geom_sf(data = points_sf, aes(color = group), size = 1) +
        geom_text_repel(
          data = points_sf, aes(label = text, color = group, geometry = geometry),
          stat = "sf_coordinates",
          # I am surprised that the bounds should be in 3857 as we've not yet changed
          # coordinate systems, but it works and 4326 does not
          xlim = ext(project(static_map_bounds, "epsg:3857"))[1:2],
          ylim = ext(project(static_map_bounds, "epsg:3857"))[3:4],
          show.legend = F) +
        scale_color_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature") +
        coord_3857_bounds(static_map_bounds)
    }
  })
