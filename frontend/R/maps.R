# Generating LGCRRP Maps

# setwd("lgcrrp-mille-feuille/frontend")
source("R/setup.R")
source("R/pre-mapping.R")

# Load map layer parameters
layer_params_file <- 'source/layers.yml' # Also used by fns.R
layer_params <- read_yaml(layer_params_file)

# Set visualization parameters
# Switch to using yaml file, but requires renaming all variables
# viz <- read_yaml("source/visualization-parameters.yml")
# Interactive Plots (Leaflet)
basemap_opacity <- 0.3
legend_opacity <- 0.8
layer_alpha <- 0.8 # Used by both interactive and static

# Static map
map_width <- 6.9
map_height <- 5.9
aspect_ratio <- map_width / map_height
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)
# max() is a placeholder. The formula was developed for smaller cities, but calculates 7 for Guiyang which is far too coarse

area <- if (inherits(aoi, "sf")) {
  units::drop_units(sqrt(st_area(aoi)))
} else if (inherits(aoi, "SpatVector")) {
  sqrt(expanse(aoi))
}
zoom_level <- max(10, round(14.6 + -0.00015 * area))


# Static maps

# Initiate plots list ----------------------------------------------------------
plots <- list()

# Plot AOI ---------------------------------------------------------------------
plots$aoi <- plot_static_layer(aoi_only = T)
save_plot(plot = plots$aoi, filename = "aoi.png",
          directory = styled_maps_dir)

# Most plots -------------------------------------------------------------------
unlist(lapply(layer_params, \(x) x$fuzzy_string)) %>%
  map2(names(.), \(fuzzy_string, yaml_key) {
    tryCatch({
      data <- fuzzy_read(spatial_dir, fuzzy_string) %>%
        vectorize_if_coarse()
      plot <- plot_static_layer(data = data, yaml_key = yaml_key)
      plots[[yaml_key]] <<- plot
      message(paste("Success:", yaml_key))
    },
    error = \(e) {
      warning(glue("Error on {yaml_key}: {e}"))
    })
  }) %>% unlist() -> plot_log

# Non-standard static plots

# Schools
school_points <- fuzzy_read(spatial_dir, "school-points", vect)
plots$school_proximity <- plot_static_layer(school_points, "school_points", baseplot = plots$school_zones)

# Health facilities
health_points <- fuzzy_read(spatial_dir, "health-points", vect)
plots$health_proximity <- plot_static_layer(health_points, "health_points", baseplot = plots$health_zones)

# Deforestation ----------------------------------------------------------------
deforest <- fuzzy_read(spatial_dir, "Deforest", rast)
values(deforest) <- values(deforest) + 2000
plots$deforest <- plot_static_layer(deforest, "deforest")
plots$forest_deforest <- plot_static_layer(deforest, "deforest", baseplot = plots$forest)

# Flooding ---------------------------------------------------------------------

plot_flooding <- function(flood_type) {
  file <- fuzzy_read(spatial_dir, glue("{flood_type}_2020.tif$"), paste)
  if (is.na(file)) return(NULL)
  flood_data <- terra::crop(rast(file), static_map_bounds)
  # Temporary fix for if layer is all NAs
  if (all(is.na(values(flood_data)))) values(flood_data)[1] <- 0
  plots[[flood_type]] <<- plot_static_layer(flood_data, yaml_key = flood_type)
  plots[[glue("{flood_type}_population")]] <<- plot_static_layer(flood_data, yaml_key = flood_type, baseplot = plots$population)
  plots[[glue("{flood_type}_wsf")]] <<- plot_static_layer(flood_data, yaml_key = flood_type, baseplot = plots$wsf)
  plots[[glue("{flood_type}_infrastructure")]] <<- plot_static_layer(flood_data, yaml_key = flood_type, baseplot = plots$infrastructure)
}

flooding_yaml_keys <- c("fluvial", "pluvial", "coastal", "combined_flooding")
walk(flooding_yaml_keys, plot_flooding)

# Intersections ----------------------------------------------------------------
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

# Historical Fire --------------------------------------------------------------
historical_fire_data <- fuzzy_read(spatial_dir, "globfire")
historical_fire_data_3857 <- project(historical_fire_data, "epsg:3857") %>%
  mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
fire_bbox <- aspect_buffer(st_bbox(historical_fire_data), aspect_ratio, buffer_percent = 0.05)
fire_bbox_3857 <- st_bbox(st_transform(fire_bbox, crs = "epsg:3857"))

fire_breaks <- scales::rescale((0:5/5)^3)

plots$burnt_area <- ggplot() +
  geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
  annotation_map_tile(type = "cartolight", zoom = zoom_level - 5) +
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

# Save plots -------------------------------------------------------------------
plots %>% walk2(names(.), \(plot, name) {
  save_plot(plot, filename = glue("{name}.png"), directory = styled_maps_dir)
})

# HTML version of plots --------------------------------------------------------
add_leaflet_plot <- function(yaml_key, fuzzy_string = NULL) {
    if (is.null(fuzzy_string)) fuzzy_string <- layer_params[[yaml_key]]$fuzzy_string
    tryCatch({
      data <- fuzzy_read(spatial_dir, fuzzy_string) %>%
        aggregate_if_too_fine(threshold = 1e3, fun = \(x) Mode(x, na.rm = T)) %>%
        vectorize_if_coarse(threshold = 1e6)
      plot_function <- create_layer_function(data = data, yaml_key = yaml_key)
      plots_html[[yaml_key]] <<- plot_function
      message(paste("Success:", yaml_key))
    },
    error = \(e) {
      message(paste("Failure:", yaml_key))
      warning(glue("Error on {yaml_key}: {e}"))
    })
  }

# Make most leaflet plots
possible_layers <- names(keep(layer_params, \(x) !is.null(x$fuzzy_string)))
plots_html <- list()
possible_layers %>%
  str_subset("luvial|flood|road", negate = T) %>%
  lapply(add_leaflet_plot) %>%
  unlist() -> plot_log

# Non standard

possible_layers %>%
  str_subset("luvial|coastal|flood|deforest") %>%
  lapply(\(yaml_key) {
    fuzzy_string <- layer_params[[yaml_key]]$fuzzy_string
    tryCatch({
      data <- fuzzy_read(spatial_dir, fuzzy_string) %>%
        aggregate_if_too_fine(fun = \(x) if (all(is.na(x))) NA else max(x, na.rm = T)) %>%
        vectorize_if_coarse(threshold = 1e7)
      plot_function <- create_layer_function(data = data, yaml_key = yaml_key)
      plots_html[[yaml_key]] <<- plot_function
      message(paste("Success:", yaml_key))
    },
    error = \(e) {
      message(paste("Failure:", yaml_key))
      warning(glue("Error on {yaml_key}: {e}"))
    })
  }) -> plots_log

deforest <- fuzzy_read(spatial_dir, layer_params$deforest$fuzzy_string)
values(deforest) <- values(deforest) + 2000
deforest_vect <- deforest %>%
  aggregate_if_too_fine(threshold = 1e4, fun = \(x) if (all(is.na(x))) NA else max(x, na.rm = T)) %>%
  vectorize_if_coarse(threshold = 1e6)
plots_html$deforest <- create_layer_function(data = deforest_vect, yaml_key = "deforest")

roads <- fuzzy_read(spatial_dir, layer_params$roads$fuzzy_string) %>%
  filter(edge_centr > break_pretty2(edge_centr, 10)[9])
roads_params <- prepare_parameters("roads")
roads_color_scale <- create_color_scale(
  domain = c(range(roads[roads_params$stroke$variable])),
  palette = roads_params$stroke$palette,
  bins = roads_params$bins,
  breaks = roads_params$breaks
    )
plots_html$roads <- \(maps, show = T) {
  addPolylines(
    maps,
    data = roads,
    fillColor = "tranparent",
    stroke = T,
    weight = 1,
    color = ~roads_color_scale(get_layer_values(roads[roads_params$stroke$variable])),
    label = paste0(round(get_layer_values(roads[roads_params$stroke$variable]), 1), "%"),
    group = roads_params$group_id
    ) %>%
  addLegend(
    position = "bottomright",
    values = break_pretty2(get_layer_values(roads[roads_params$stroke$variable])),
    pal = roads_color_scale,
    title = paste(roads_params$stroke$title, "<br>", roads_params$stroke$subtitle),
    opacity = legend_opacity,
    group = roads_params$group_id
  )
}

message(paste("Following plots not made:", paste_and(which_not(possible_layers, names(plots_html)))))

# Add group ids (for leaflet layer control) for all successfully created layers
group_ids <- map(layer_params, \(x) x$group_id) %>% keep_at(names(plots_html)) %>% unlist() %>% unname()
