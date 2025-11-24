# Generating City Scan maps for transparencies

if ("frontend" %in% list.files()) setwd("frontend")

# This file is currently set to use layers-with-french.yml instead of layers.yml.
# Change in R/setup.R

# Set static map visualization parameters --------------------------------------

# Frequently used parameters:
# For a single legend per map, use
#   map_width <- 12.56; map_height <- 9.7; map_portions <- c(map_width, 2.6)
# For two columns of legends (and captions), use
#   map_width <- 11.2; map_height <- 9.7; map_portions <- c(map_width, 4.06)

layer_alpha <- 0.7
map_width <- 11.2 # 15.16 is total width (map_width + legend width)
map_height <- 9.7
aspect_ratio <- map_width / map_height
map_portions <- c(map_width, 4.06) # First number is map width, second is legend width

# Load libraries and pre-process rasters
source("R/setup.R", local = T)
source("R/pre-mapping.R", local = T)

# If you want to change the layers.yml file, change it here
# layer_params_file <- 'source/layers-uzbek.yml' # Also used by fns.R
# layer_params <- read_yaml(layer_params_file)

# Define map extent and zoom level adjustment
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)
zoom_adjustment <- 1

# Custom themes
theme_title <- \(...) theme(plot.title = element_text(size = 20, margin = margin(6, 0, 3.5, 40)), ...)

# Static maps

# Initiate plots list ----------------------------------------------------------
plots <- list()
packets <- list()

# Plot AOI boundary, vector basemap, and aerial basemap  -----------------------
plots$aoi <- plot_static_layer(aoi_only = T, plot_aoi = T, plot_wards = !is.null(wards),
  baseplot = ggplot(),
  zoom_adj = zoom_adjustment,
  aoi_stroke = list(color = "black", linewidth = 0.4)) +
  labs(title = paste(c(
          "Area of interest",
          "Zone d'intérêt"),
          collapse = "   /   ")) +
  theme_title()

plots$vector <- plot_static_layer(aoi_only = T, plot_aoi = F, plot_wards = !is.null(wards),
  zoom_adj = zoom_adjustment,
  # , aoi_stroke = list(color = "black", linewidth = 0.4)
  ) +
  labs(title = "   ") +
  theme_title()

# Plot aerial imagery ----------------------------------------------------------
plots$aerial <- plot_static_layer(aoi_only = T, plot_aoi = F, plot_wards = !is.null(wards),
    zoom_adj = zoom_adjustment,
    #  aoi_stroke = list(color = "yellow", linewidth = 0.4),
    baseplot = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}.jpg") +
  labs(title = "   ") +
  theme_title()

# Plot blank map for scale bar only --------------------------------------------
plots$scale_bar <- plot_static_layer(aoi_only = T, plot_aoi = F, plot_wards = F,
  baseplot = ggplot()) +
  theme_title() +
  annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm"))

# Standard plots ---------------------------------------------------------------
unlist(lapply(layer_params, \(x) x$fuzzy_string)) %>%
  discard_at(c("burnt_area", "elevation")) %>%
  map2(names(.), \(fuzzy_string, yaml_key) {
    tryCatch_named(yaml_key, {
      file_path <- fuzzy_read(spatial_dir, fuzzy_string, FUN = paste)
      if (is.na(file_path)) stop(glue("File {file_path} does not exist"))
      data <- fuzzy_read(spatial_dir, fuzzy_string)
      if (inherits(data, "SpatRaster")) data <- vectorize_if_coarse(data)
      titles <- unlist(layer_params[[yaml_key]][c("title", "title_fr")])
      subtitles <- unlist(layer_params[[yaml_key]][c("subtitle", "subtitle_fr")])
      packet <- plot_static_layer(
        title = paste(titles, collapse = "<br>"),
        subtitle = paste(subtitles, collapse = "<br>"),
        data = data, yaml_key = yaml_key, zoom_adj = zoom_adjustment,
        packet = T, plot_aoi = T, plot_wards = !is.null(wards)) +
        labs(title = paste(titles, collapse = "   /   ")) +
        theme_title()
      packets[[yaml_key]] <<- packet
      plots[[yaml_key]] <<- ggplot() + packet
      message(paste("Success:", yaml_key))
    })
  }) %>% unlist() -> plot_log

# Non-standard static plots ----------------------------------------------------

source("R/map-isochrones.R", local = T) # Could be standard if layers.yml included baseplot # nolint: line_length_linter.
source("R/map-elevation.R", local = T) # Could be standard if we wrote city-specific breakpoints to layers.yml
if ("zoom" %in% names(plots$elevation$layers[[2]]$mapping)) {
  plots$elevation$layers[[2]] <- NULL
}
source("R/map-deforestation.R", local = T) # Could be standard if layers.yml included baseplot and source data had 2000 added
source("R/map-historical-burnt-area.R", local = T)
# plots$infrastructure <- plots$infrastructure + theme(legend.text = element_markdown())

if (!is.null(plots$school_proximity)) plots$school_proximity <- plots$school_proximity +
  labs(title = paste(c(
    layer_params[["school_zones"]]$title,
    layer_params[["school_zones"]]$title_fr),
    collapse = "   /   "))
if (!is.null(plots$health_proximity)) plots$health_proximity <- plots$health_proximity +
  labs(title = paste(c(
    layer_params[["health_zones"]]$title,
    layer_params[["health_zones"]]$title_fr),
    collapse = "   /   "))
if (!is.null(plots$roads)) plots$roads <- plots$roads +
  labs(title = paste(c(
    layer_params[["roads"]]$stroke$title,
    layer_params[["roads"]]$stroke$title_fr),
    collapse = "   /   "))

# Remove grey background, add titles, remove scale bar and north arrow
for (name in names(plots)) {
  if (name != "scale_bar") {
    plots[[name]]$layers <- plots[[name]]$layers %>%
      discard(\(x) inherits(x$geom, c("GeomNorthArrow", "GeomScaleBar")))
  }
  if (name == "vector") next
  if (name == "aerial") next
  title <- paste(c(
      layer_params[[name]]$title,
      layer_params[[name]]$title_fr),
      collapse = "   /   ")
  if (length(title) > 0) {
    plots[[name]] <- plots[[name]] +
      labs(title = title)
  }
  plots[[name]] <- plots[[name]] +
    theme(
      panel.background = element_rect(fill = "white"),
      legend.box.margin = margin(0, 0, 60, 12, unit = "pt")
      ) +
    theme_title()
}

# Save plots -------------------------------------------------------------------
transparencies_dir <- file.path(output_dir, "transparent-maps")
if (!dir.exists(transparencies_dir)) dir.create(transparencies_dir)
plots %>%
  walk2(names(.), \(plot, name) {
  # if (name != "aoi") return(NULL)
  save_plot(plot, filename = glue("{name}.png"), directory = transparencies_dir,
    map_height = map_height + .3, map_width = map_width, dpi = 200, rel_widths = map_portions)
  })

# Save columns of legends by themselves ----------------------------------------

# First, create fake flood plot that combines fluvial, pluvial, and coastal flood legend titles
# This would be quicker if we didn't use actual flood data, but works fine
flood_types <- c("fluvial", "pluvial", "coastal")
found_flood_type <- flood_types[which(flood_types %in% names(plots))[1]]
packets$sample_flood <- if (is.na(found_flood_type)) { NULL } else {
  plot_static_layer(
    fuzzy_read(spatial_dir, layer_params[[found_flood_type]]$fuzzy_string),
    found_flood_type, packet = T,
    title = "Flood probability
Probabilité d'inondation",
    subtitle = "Probability of a flood event of 15 centimeters or more within a 3-arc-second area in a given year
Probabilité d'un événement d'inondation de 15 centimètres ou plus dans une zone de 3 secondes d'arc au cours d’une année donnée")
}

# First column
print("Starting first legend column")
(
  ggplot() +
    packets$forest + guides(fill = guide_legend(order = 1, theme = theme(legend.title = element_blank(), legend.text = element_text(hjust = 0))), color = guide_legend(order = 1, theme = theme(legend.text = element_text(hjust = 0)))) +
    packets$deforest + guides(fill = guide_colorsteps(order = 2)) + guides(color = guide_colorsteps(order = 2)) +
    packets$vegetation + guides(fill = guide_legend(order = 3)) + guides(color = guide_legend(order = 3)) +
    packets$sample_flood + guides(fill = guide_legend(order = 4)) + guides(color = guide_legend(order = 4)) +
    packets$landslide + guides(fill = guide_legend(order = 5)) + guides(color = guide_legend(order = 5)) +
    theme(
      panel.background = element_rect(fill = "white"),
      legend.box.margin = margin(0, 0, 0, 0, unit = "pt"),
      legend.box.spacing = unit(0, "pt"),
      legend.justification = c("left", "top"))
  ) %>%
  get_plot_component("guide-box-right") %>%
  ggsave(
    filename = file.path(transparencies_dir, glue("legend-col1.png")),
    height = map_height + 1, width = 2.3, dpi = 300)

# Second column
print("Starting second legend column")
( 
  ggplot() + 
    packets$population + guides(fill = guide_colorsteps(order = 3)) + guides(color = guide_colorsteps(order = 3)) +
    packets$economic_activity + guides(fill = guide_colorsteps(order = 4)) + guides(color = guide_colorsteps(order = 2)) +
    packets$school_points +
      guides(color = guide_legend(order = 5, theme = theme(legend.text = element_text(hjust = 0)))) +
    packets$health_points + guides(color = guide_legend(order = 6, theme = theme(legend.text = element_text(hjust = 0)))) +
    packets$ghsl + guides(fill = guide_legend(order = 7, theme = theme(legend.text = element_text(hjust = 0))), color = guide_legend(order = 7, theme = theme(legend.text = element_text(hjust = 0)))) +
    theme(
      panel.background = element_rect(fill = "white"),
      legend.box.margin = margin(0, 0, 0, 0, unit = "pt"),
      legend.box.spacing = unit(0, "pt"),
      legend.justification = c("left", "top"))
  ) %>%
  get_plot_component("guide-box-right") %>%
  ggsave(
    filename = file.path(transparencies_dir, glue("legend-col2.png")),
    height = map_height + 1, width = 2.3, dpi = 300)
