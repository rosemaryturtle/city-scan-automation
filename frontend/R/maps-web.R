# Generating City Scan Maps

if ("frontend" %in% list.files()) setwd("frontend")
source("R/setup.R")
source("R/pre-mapping.R")

# Set static map visualization parameters
layer_alpha <- 0.7
map_width <- 6.9
map_height <- 5.9
aspect_ratio <- map_width / map_height

# Define map extent and zoom level
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)

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
