# Generating LGCRRP Maps

# setwd("lgcrrp-mille-feuille/frontend")
source("R/setup.R")
source("R/pre-mapping.R")

# Load map layer parameters
layer_params_file <- 'source/layers.yml' # Also used by fns.R
layer_params <- read_yaml(layer_params_file)

# Set static map visualization parameters
layer_alpha <- 0.8
map_width <- 6.9
map_height <- 5.9
aspect_ratio <- map_width / map_height

# Define the AOI
aoi <- st_zm(st_read(file.path(user_input_dir, "AOI")))
aoi_bounds <- st_bbox(aoi)
static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)

# Create basemaps
zoom <- round(14.6 + -0.00015 * units::drop_units(sqrt(st_area(aoi))))
tiles <- annotation_map_tile(type = "cartolight", zoom = zoom, progress = "none")

# Initiate plots list ----------------------------------------------------------
plots <- list()

# Plot AOI ---------------------------------------------------------------------
plots$aoi <- plot_layer(aoi_only = T)
save_plot(plot = plots$aoi, filename = "aoi.png",
          directory = styled_maps_dir)

# Most plots -------------------------------------------------------------------
unlist(lapply(layer_params, \(x) x$fuzzy_string)) %>%
  # keep_at("land_cover") %>%
  # .[14] %>%
  map2(names(.), \(fuzzy_string, yaml_key) {
    tryCatch({
      data <- fuzzy_read(spatial_dir, fuzzy_string)
      if (class(data)[1] == "SpatRaster") {
        # Vectorize only if resolution is coarse (7000 is based off Cumilla population)
        cell_count <- (units::drop_units(st_area(aoi)) / cellSize(data)[1,1])[[1]]
        if (cell_count < 7000) data <- rast_as_vect(data)
      }
      plot <- plot_layer(data = data, yaml_key = yaml_key)
      plots[[yaml_key]] <<- plot
      message(paste("Success:", yaml_key))
    },
    error = \(e) {
      warning(glue("Error on {yaml_key}: {e}"))
    })
  }) %>% unlist() -> log

# Elevation --------------------------------------------------------------------
# elevation_params <- prepare_parameters("elevation")
# elevation_title <- format_title(elevation_params$title, elevation_params$subtitle)
# plots$elevation <- plots$elevation + labs(color = elevation_title)

# # Road criticality -------------------------------------------------------------
# # Doing this manually because of stroke weight and color legends
# road_params <- prepare_parameters("roads")
# road_title <- format_title(road_params$title, road_params$subtitle)
# road_data <- fuzzy_read(spatial_dir, "edges-edit.gpkg")
# plots$roads <- plot_layer(data = road_data, yaml_key = "roads") +
#   scale_color_stepsn(
#     name = road_title,
#     colors = road_params$stroke$palette,
#     labels = scales::label_percent()) +
#   scale_linewidth_manual(
#     name = "Road type",
#     values = c("FALSE" = 0.24, "TRUE" = 1),
#     labels = c("Secondary", "Primary"))

# Deforestation ----------------------------------------------------------------
deforest <- fuzzy_read(spatial_dir, "Deforest", rast)
values(deforest) <- values(deforest) + 2000
plots$deforest <- plot_layer(deforest, "deforest")
plots$forest_deforest <- plot_layer(deforest, "deforest", baseplot = plots$forest)

# Flooding ---------------------------------------------------------------------

plot_flooding <- function(flood_type) {
  # browser()
  file <- fuzzy_read(spatial_dir, glue("{flood_type}_2020.tif$"), paste)
  if (is.na(file)) return(NULL)
  flood_data <- terra::crop(rast(file), static_map_bounds)
  # Temporary fix for if layer is all NAs
  if (all(is.na(values(flood_data)))) values(flood_data)[1] <- 0
  plots[[flood_type]] <<- plot_layer(flood_data, yaml_key = flood_type)
  plots[[glue("{flood_type}_population")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$population)
  plots[[glue("{flood_type}_wsf")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$wsf)
  plots[[glue("{flood_type}_infrastructure")]] <<- plot_layer(flood_data, yaml_key = flood_type, baseplot = plots$infrastructure)
}

flooding_yaml_keys <- c("fluvial", "pluvial", "coastal", "combined_flooding")
walk(flooding_yaml_keys, plot_flooding)

# Historical Fire --------------------------------------------------------------
historical_fire_data <- fuzzy_read(spatial_dir, "globfire")
historical_fire_data_3857 <- project(historical_fire_data, "epsg:3857") %>%
  mutate(x = geom(., df = T)$x, y = geom(., df = T)$y)
fire_bbox <- aspect_buffer(st_bbox(historical_fire_data), aspect_ratio, buffer_percent = 0.05)
fire_bbox_3857 <- st_bbox(st_transform(fire_bbox, crs = "epsg:3857"))

fire_breaks <- scales::rescale((0:5/5)^3)

plots$burnt_area <- ggplot() +
  geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
    # coord_sf(expand = F) +
  annotation_map_tile(type = "cartolight", zoom = zoom - 5) +
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
  theme(
    legend.justification = c("left", "bottom"),
    legend.box.margin = margin(0, 0, 0, 12, unit = "pt"),
    legend.margin = margin(4,0,4,0, unit = "pt"),
    axis.text = element_blank(),
    axis.ticks = element_blank(),
    axis.ticks.length = unit(0, "pt"),
    plot.margin = margin(0,0,0,0)) + 
    geom_sf(data = aoi, fill = NA, linetype = "dashed", linewidth = .5) + 
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
walk2(plots, names(plots), \(plot, name) {
  save_plot(plot, filename = glue("{name}.png"), directory = styled_maps_dir)
})
