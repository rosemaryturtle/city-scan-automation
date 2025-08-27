# Generating City Scan maps for transparencies

if ("frontend" %in% list.files()) setwd("frontend")

# Set static map visualization parameters
layer_alpha <- 0.7
map_width <- 12.56 # Width of the map itself, excluding legend
map_height <- 9.7
aspect_ratio <- map_width / map_height
map_portions <- c(map_width, 2.6) # First number is map width, second is legend width

# Load libraries and pre-process rasters
source("R/setup.R", local = T)
source("R/pre-mapping.R", local = T)

# If you want layers.yml file, change it here
# layer_params_file <- 'source/layers-uzbek.yml' # Also used by fns.R
# layer_params <- read_yaml(layer_params_file)

# Define map extent and zoom level adjustment
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)
zoom_adjustment <- 0

# Custom themes
theme_title <- \(...) theme(plot.title = element_text(size = 20, margin = margin(6, 0, 3.5, 40)), ...)

# Static maps

# Initiate plots list ----------------------------------------------------------
plots <- list()

# Plot AOI boundary, vector basemap, and aerial basemap  -----------------------
plots$aoi <- plot_static_layer(aoi_only = T, plot_aoi = T, plot_wards = !is.null(wards),
  baseplot = ggplot(),
  zoom_adj = zoom_adjustment,
  aoi_stroke = list(color = "black", linewidth = 0.4)) +
  labs(title = toupper(paste(
          "Area of interest",
          "Domaine d'intérêt",
          sep = "   /   "))) +
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
      data <- fuzzy_read(spatial_dir, fuzzy_string) %>%
        vectorize_if_coarse()
      plot <- plot_static_layer(
        data = data, yaml_key = yaml_key, zoom_adj = zoom_adjustment,
        baseplot = ggplot(),
        plot_aoi = T, plot_wards = !is.null(wards)) +
        labs(title = toupper(paste(
          layer_params[[yaml_key]]$title,
          layer_params[[yaml_key]]$title_fr,
          sep = "   /   "))) +
        theme_title()
      plots[[yaml_key]] <<- plot
      message(paste("Success:", yaml_key))
    })
  }) %>% unlist() -> plot_log

# Non-standard static plots ----------------------------------------------------

source("R/map-schools-health-proximity.R", local = T) # Could be standard if layers.yml included baseplot # nolint: line_length_linter.
source("R/map-elevation.R", local = T) # Could be standard if we wrote city-specific breakpoints to layers.yml
if ("zoom" %in% names(plots$elevation$layers[[2]]$mapping)) {
  plots$elevation$layers[[2]] <- NULL
}
source("R/map-deforestation.R", local = T) # Could be standard if layers.yml included baseplot and source data had 2000 added
source("R/map-historical-burnt-area.R", local = T)
# plots$infrastructure <- plots$infrastructure + theme(legend.text = element_markdown())

if (!is.null(plots$school_proximity)) plots$school_proximity <- plots$school_proximity +
  labs(title = toupper(paste(
    layer_params[["school_zones"]]$title,
    layer_params[["school_zones"]]$title_fr,
    sep = "   /   ")))
if (!is.null(plots$health_proximity)) plots$health_proximity <- plots$health_proximity +
  labs(title = toupper(paste(
    layer_params[["health_zones"]]$title,
    layer_params[["health_zones"]]$title_fr,
    sep = "   /   ")))
if (!is.null(plots$roads)) plots$roads <- plots$roads +
  labs(title = toupper(paste(
    layer_params[["roads"]]$stroke$title,
    layer_params[["roads"]]$stroke$title_fr,
    sep = "   /   ")))

# Remove grey background, add titles, remove scale bar and north arrow
for (name in names(plots)) {
  if (name != "scale_bar") {
    plots[[name]]$layers <- plots[[name]]$layers %>%
      discard(\(x) inherits(x$geom, c("GeomNorthArrow", "GeomScaleBar")))
  }
  if (name == "vector") next
  if (name == "aerial") next
  title <- toupper(paste(
      layer_params[[name]]$title,
      layer_params[[name]]$title_fr,
      sep = "   /   "))
  if (length(title) > 0) {
    plots[[name]] <- plots[[name]] +
      labs(title = toupper(paste(
        layer_params[[name]]$title,
        layer_params[[name]]$title_fr,
        sep = "   /   ")))
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
  # keep_at(~ str_subset(.x, "luvial|coastal|combined")) %>%
  # keep_at(~ str_subset(.x, "aerial|vector")) %>%
  walk2(names(.), \(plot, name) {
  # if (name != "aoi") return(NULL)
  save_plot(plot, filename = glue("{name}.png"), directory = transparencies_dir,
    map_height = map_height + .3, map_width = map_width, dpi = 200, rel_widths = map_portions)
})
