# Map isochrones

# # Schools
# tryCatch_named("school_proximity", {
#   school_points <- fuzzy_read(spatial_dir, "school-points", vect)
#   if (inherits(school_points, "SpatVector")) {
#     plots$school_proximity <- plot_static_layer(school_points, "school_points", baseplot = plots$school_zones)
#   }
# })
# Health facilities
# tryCatch_named("health_proximity", {
  health_points <- fuzzy_read(spatial_dir, "health-points", vect)
#   if (inherits(health_points, "SpatVector")) {
#     plots$health_proximity <- plot_static_layer(health_points, "health_points", baseplot = plots$health_zones)
#   }
# })

# Isochrones with unlabeled points
c("health", "public_space", "waste", "transportation", "sanitation", "electricity", "water", "communication", "landfill") %>%
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
    params <- layer_params[[paste0(x, "_points")]]
    group <- str_wrap(params$label, 30)
    existence <- c(nrow(polygons) > 0, nrow(points) > 0, nrow(lines) > 0)
    p <- plots[[paste0(x, "_zones")]]
    if (any(existence)) {
      distance_buffer <- buffer(aoi, max(layer_params[[paste0(x, "_zones")]]$breaks))
      points <- points[static_map_bounds][distance_buffer] # Filter added for SEZ labels
      polygons <- polygons[static_map_bounds][distance_buffer]
      lines <- lines[static_map_bounds][distance_buffer]
      # Just use zones if nearest points are outside the mapping bounds
      if (nrow(points) == 0 & nrow(polygons) == 0 & nrow(lines) == 0) {
        plots[[paste0(x, "_proximity")]] <<- p
        return(NULL)
      }
      
      geoms <- list(
        geom_spatvector(data = polygons, aes(fill = group), color = NA, show.legend = F),
        geom_spatvector(data = points, aes(color = group), size = 1),
        geom_spatvector(data = lines, aes(color = group), size = 1)
        )[existence]
      scales <- list(
        scale_fill_manual(values = params$palette, name = "Feature"),
        scale_color_manual(values = params$palette, name = "Feature"),
        scale_color_manual(values = params$palette, name = "Feature"))[existence]

      # Points map
      plots[[paste0(x, "_points")]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
        geoms + scales +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = params$caption)
      # Points & isochrones map (ggpacket would let me reuse the code)
      if (is.null(p)) return(NULL)
      plots[[paste0(x, "_proximity")]] <<- p +
        ggnewscale::new_scale_fill() +
        geoms + scales +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = paste(params$caption, "Only features within the maximum isochrone distance are shown."))
    }
  })

# Isochrones with labeled points
c("education") %>%
  walk(\(x) {
    points <- fuzzy_read(spatial_dir, paste0(x, "_POI\\."))
    params <- layer_params[[paste0(x, "_points")]]
    group <- params$label
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
        mutate(.before = 1, text = pull(points[params$data_variable])) %>%
        st_as_sf()
        
      points_geom <- geom_sf(data = points_sf, aes(color = group), size = 1)
      scale <- scale_color_manual(values = params$palette, name = "Feature")
      text_labels <- if (length(na.omit(points_sf$text)) > 10) {
        NULL
      } else {
        geom_text_repel(
          data = points_sf, aes(label = text, color = group, geometry = geometry),
          stat = "sf_coordinates",
          # I am surprised that the bounds should be in 3857 as we've not yet changed
          # coordinate systems, but it works and 4326 does not
          xlim = ext(project(static_map_bounds, "epsg:3857"))[1:2],
          ylim = ext(project(static_map_bounds, "epsg:3857"))[3:4],
          show.legend = F)
      }
      # Points map
      plots[[paste0(x, "_points")]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
        points_geom +
        text_labels +
        scale +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = params$caption)
      # Points and isochrones map
      plots[[paste0(x, "_proximity")]] <<- p +
        points_geom +
        text_labels +
        scale +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = params$caption)
    }
  })

c("sez") %>%
  walk(\(x) {
    points <- fuzzy_read(spatial_dir, paste0(x, "_POI\\."))
    params <- layer_params[[paste0(x, "_points")]]
    group <- params$label
    p <- plots[[paste0(x, "_zones")]]
    # browser()
    if (inherits(points, "SpatVector") & !is.null(p)) {
      points <- points[static_map_bounds] # Filter added for SEZ labels
      # Just use zones if nearest points are outside the mapping bounds
      if (nrow(points) == 0) {
        plots[[paste0(x, "_proximity")]] <<- p
        return(NULL)
      }
      # Convert to sf for ggrepel
      points_sf <- points %>%
        mutate(.before = 1,
          text = pull(points[params$data_variable]),
          description_f = factor(description,
            levels = c("Agro-Industrial", "IT Center", "IT Park", "Manufacturing", "Medical Tourism Center", "Tourism")),
          operating = factor(layer == "sez-operating", levels = c(FALSE, TRUE)),
          weight = c("plain", "bold")[(operating == "TRUE") + 1],
          ) %>%
        st_as_sf()
        
      points_geom <- geom_sf(data = points_sf, aes(color = description_f, shape = operating), size = 1.5, show.legend = c(color = T, fill = F))
      scales <- list(
        color = scale_color_manual(name = "SEZ type",
            values = setNames(scales::hue_pal()(6), levels(points_sf$description_f)), drop = T),
        shape = scale_shape_manual(
          values = c("TRUE" = 19, "FALSE" = 1), name = "SEZ status", drop = F,
          labels = c("TRUE" = "Operating", "FALSE" = "Planned"),
          )
      )
      text_labels <- if (length(na.omit(points_sf$text)) > 10) {
        NULL
      } else {
        geom_text_repel(
          data = points_sf, aes(label = text, color = description, fontface = weight, geometry = geometry),
          stat = "sf_coordinates",
          # I am surprised that the bounds should be in 3857 as we've not yet changed
          # coordinate systems, but it works and 4326 does not
          xlim = ext(project(static_map_bounds, "epsg:3857"))[1:2],
          ylim = ext(project(static_map_bounds, "epsg:3857"))[3:4],
          show.legend = F)
      }
      # Points map
      plots[[paste0(x, "_points")]] <<- plot_static_layer(aoi_only = T, plot_aoi = T) +
        points_geom +
        text_labels +
        scales +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = params$caption)
      # Points and isochrones map
      plots[[paste0(x, "_proximity")]] <<- p +
        ggnewscale::new_scale_color() +
        ggnewscale::new_scale_fill() +
        points_geom +
        text_labels +
        scales +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = paste(params$caption, "Some SEZs that contribute to the isochrones may be outside the mapping bounds.")) #+
        # theme(legend.text = ggtext::element_markdown())
    }
  })

# Combined infrastructure map
plot_combined <- function() {
infra_types <- c("public_space", "waste", "transportation", "sanitation", "electricity", "water",
  "communication", "landfill", "sez", "education")
combined_features <- infra_types %>%
  map(\(x) {
    features <- fuzzy_read(spatial_dir, paste0(x, "_POI_unmodified"), svc)
    params <- layer_params[[paste0(x, "_points")]]
    group <- params$label
    if (is.na(features)) return(NULL)
    if (inherits(features, "SpatVectorCollection")) { 
      geometries <- sapply(features, type_data)
      points <- if ("points" %in% geometries) features[which(geometries == "points")] %>% mutate(layer = x, group = group, .keep = "none") else vect()
      polygons <- if ("polygons" %in% geometries) features[which(geometries == "polygons")] %>% mutate(layer = x, group = group, .keep = "none") else vect()
      lines <- if ("lines" %in% geometries) features[which(geometries == "lines")] %>% mutate(layer = x, group = group, .keep = "none") else vect()
      # For when polygons are too small to see, also label their centroids
      if (nrow(polygons) > 0) points <- rbind(points, centroids(polygons))
    } else {
      points <- fuzzy_read(spatial_dir, paste0(x, "_POI\\.")) %>%
        mutate(layer = x, group = group, .keep = "none")
      if (!inherits(points, "SpatVector")) return(NULL)
      polygons <- vect()
      lines <- vect()
    }
    existence <- c(nrow(polygons) > 0, nrow(points) > 0, nrow(lines) > 0)
    return(list(polygons = polygons, points = points, lines = lines)[existence])
  }) %>%
  setNames(infra_types)

if (all(sapply(combined_features, is.null))) return(NULL)

colors <- layer_params %>%
  keep_at(c(paste0(infra_types, "_points"), "health_points")) %>%
  map("palette") %>% unlist()
labels <- layer_params %>%
  keep_at(c(paste0(infra_types, "_points"), "health_points")) %>%
  map("labels") %>% unlist()
long_labels <- layer_params %>%
  keep_at(c(paste0(infra_types, "_points"), "health_points")) %>% names() %>%
  str_extract("^[^_]+") %>% stringr::str_to_title() %>%
  paste0(": ", labels) %>%
  str_wrap(30)
palette <- setNames(colors, labels)

combined_points <- combined_features %>%
  map("points") %>%
  discard(\(x) is.null(x)) %>%
  bind_spat_rows()
if (inherits(health_points, "SpatVector")) {
combined_points <- bind_spat_rows(
  combined_points,
  project(mutate(health_points, layer = "health", group = layer_params$health_points$labels, .keep = "none"), crs(combined_points)))
}
combined_points <- combined_points %>%
  mutate(group = factor(group, levels = names(palette))) %>%
  .[static_map_bounds]
combined_polygons <- combined_features %>%
  map("polygons") %>%
  discard(\(x) is.null(x)) %>%
  (\(out) if (length(out) == 0) mutate(vect(), group = character(0)) else bind_spat_rows(out))() %>%
  mutate(group = factor(group, levels = names(palette))) %>%
  .[static_map_bounds]
combined_lines <- combined_features %>%
  map("lines") %>%
  discard(\(x) is.null(x)) %>%
  (\(out) if (length(out) == 0) mutate(vect(), group = character(0)) else bind_spat_rows(out))() %>%
  # bind_spat_rows() %>%
  mutate(group = factor(group, levels = names(palette))) %>%
  .[static_map_bounds]

plot_static_layer(aoi_only = T, plot_aoi = T) +
  geom_spatvector(data = combined_polygons, aes(fill = group), color = NA, size = 1, show.legend = F) +
  geom_spatvector(data = combined_points, aes(color = group), size = 1, show.legend = T) +
  # geom_spatvector(data = combined_lines, aes(color = group), size = 1, name = "Infrastructure Type")
  scale_fill_manual(values = palette, labels = long_labels, name = "Infrastructure type", drop = F) + 
  scale_color_manual(values = palette, labels = long_labels, name = "Infrastructure type", drop = F) +
  coord_3857_bounds(static_map_bounds) +
  labs(caption = "Map data from OpenStreetMap.")
}

plots$combined_infrastructure <- plot_combined()
