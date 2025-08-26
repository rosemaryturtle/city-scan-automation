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
    features <- fuzzy_read(spatial_dir, paste0(x, "_POI_unmodified"), svc)
    if (inherits(features, "SpatVectorCollection")) { 
      geometries <- sapply(features, type_data)
      points <- if ("points" %in% geometries) features[which(geometries == "points")] else vect()
      polygons <- if ("polygons" %in% geometries) features[which(geometries == "polygons")] else vect()
      lines <- if ("lines" %in% geometries) features[which(geometries == "lines")] else vect()
      # For when polygons are too small to see, also label their centroids
      if (nrow(polygons) > 0) points <- rbind(points, centroids(polygons))
    } else {
      points <- fuzzy_read(spatial_dir, paste0(x, "_POI\\."))
      if (!inherits(points, "SpatVector")) return(NULL)
      polygons <- vect()
      lines <- vect()
    }
    group <- layer_params[[paste0(x, "_points")]]$label
    existence <- c(nrow(polygons) > 0, nrow(points) > 0, nrow(lines) > 0)
    p <- plots[[paste0(x, "_zones")]]
    if (any(existence)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      polygons <- polygons[static_map_bounds]
      lines <- lines[static_map_bounds]
      # Just use zones if nearest points are outside the mapping bounds
      if (nrow(points) == 0 & nrow(polygons) == 0 & nrow(lines) == 0) {
        plots[[paste0(x, "_proximity")]] <<- p
        return(NULL)
      }
      
      geoms <- list(
        geom_spatvector(data = polygons, aes(fill = group), color = NA, size = 1),
        geom_spatvector(data = points, aes(color = group), size = 1),
        geom_spatvector(data = lines, aes(color = group), size = 1)
        )[existence]
      scales <- list(
        scale_fill_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature"),
        scale_color_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature"),
        scale_color_manual(values = layer_params[[paste0(x, "_points")]]$palette, name = "Feature"))[existence]

      # Points map
      plots[[paste0(x, "_points")]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
        geoms + scales +
        coord_3857_bounds(static_map_bounds)
      # Points & isochrones map (ggpacket would let me reuse the code)
      if (is.null(p)) return(NULL)
      plots[[paste0(x, "_proximity")]] <<- p +
        ggnewscale::new_scale_fill() +
        geoms + scales +
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
      # Just use zones if nearest points are outside the mapping bounds
      if (nrow(points) == 0) {
        plots[[paste0(x, "_proximity")]] <<- p
        return(NULL)
      }
      # Convert to sf for ggrepel
      points_sf <- points %>%
        mutate(.before = 1, text = pull(points[layer_params[[paste0(x, "_points")]]$data_variable])) %>%
        st_as_sf()
      # Points and isochrones map
      plots[[paste0(x, "_points")]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
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
      # Points and isochrones map
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
