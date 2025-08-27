# tryCatch_named("school_proximity", {
#   school_points <- fuzzy_read(spatial_dir, "school-points", vect)
#   if (inherits(school_points, "SpatVector")) {
#     # titles <- unlist(layer_params$school_points[c("title", "title_fr")])
#     # subtitles <- unlist(layer_params$school_points[c("subtitle", "subtitle_fr")])
#     plots$school_proximity <- plot_static_layer(school_points, "school_points",
#       title = NULL, subtitle = NULL,
#       baseplot = plots$school_zones)
#   }
# })
# # Health facilities
# tryCatch_named("health_proximity", {
#   health_points <- fuzzy_read(spatial_dir, "health-points", vect)
#   if (inherits(health_points, "SpatVector")) {
#     # titles <- unlist(layer_params$health_points[c("title", "title_fr")])
#     # subtitles <- unlist(layer_params$health_points[c("subtitle", "subtitle_fr")])
#     plots$health_proximity <- plot_static_layer(health_points, "health_points",
#       title = NULL, subtitle = NULL,
#       labels = "TEST",
#       baseplot = plots$health_zones)
#   }
# })

# Isochrones with unlabeled points
c("school", "health") %>%
  walk(\(x) {
    yaml_key <- paste0(x, "_points")
    params <- layer_params[[yaml_key]]
    points <- fuzzy_read(spatial_dir, params$fuzzy_string)
    group <- params$label
    p <- plots[[paste0(x, "_zones")]]
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      # # Points map
      # plots[[yaml_key]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
      #   geom_spatvector(data = points, aes(color = group), size = 1) +
      #   scale_color_manual(values = params$palette, name = NULL) +
      #   coord_3857_bounds(static_map_bounds)
      # Points & isochrones map (ggpacket would let me reuse the code)
      plots[[paste0(x, "_proximity")]] <<- p +
        geom_spatvector(data = points, aes(color = group), size = 1) +
        scale_color_manual(values = params$palette, name = NULL) +
        coord_3857_bounds(static_map_bounds)
    }
  })


c("school", "health") %>%
  walk(\(x) {
    yaml_key <- paste0(x, "_points")
    # params <- layer_params[[yaml_key]] 
    params <- prepare_parameters(yaml_key)
    points <- fuzzy_read(spatial_dir, params$fuzzy_string)
    group <- params$label
    p <- packets[[paste0(x, "_zones")]]
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      # # Points map
      # plots[[yaml_key]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
      #   geom_spatvector(data = points, aes(color = group), size = 1) +
      #   scale_color_manual(values = params$palette, name = NULL) +
      #   coord_3857_bounds(static_map_bounds)
      # Points & isochrones map (ggpacket would let me reuse the code)
      packets[[paste0(x, "_proximity")]] <<- p +
        guides(fill = guide_legend(order = 1)) +
        geom_spatvector(data = points, aes(color = group), size = 1) +
        scale_color_manual(values = params$palette, name = NULL, guide = guide_legend(order = 2)) +
        coord_3857_bounds(static_map_bounds)
    }
  })
