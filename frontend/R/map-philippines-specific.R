# Philippines specific maps

# Buildings --------------------------------------------------------------------

plot_buildings <- function() {
  buildings <- fuzzy_read(spatial_dir, "Buildings")
  if (!inherits(buildings, "SpatVector")) return(NULL)
  plot_static_layer(aoi_only = T, plot_aoi = T) +
    geom_spatvector(data = buildings, aes(fill = "Buildings"), color = NA) +
    scale_fill_manual(values = "grey35", name = "") +
    coord_3857_bounds(static_map_bounds) +
    labs(caption = "Map data from Google Open Buildings.")
}
plots$buildings <- plot_buildings()

plot_building_morphologies <- function() {
  morphologies <- fuzzy_read(spatial_dir, "ghsl-build")
  if (!inherits(morphologies, "SpatRaster")) return(NULL)
  plot_static_layer(
    data = morphologies, yaml_key = "building_morphology_non_residential",
    baseplot = plots$building_morphology_residential)
}
plots$building_morphology <- plot_building_morphologies()


# Ports & road networks --------------------------------------------------------

plot_ports <- function() {
  roads <- fuzzy_read(spatial_dir, "primary_roads")
  ports <- list(
    "RoRo Seaport" = fuzzy_read(spatial_dir, "roro_ports"),
    "Non-RoRo Seaport" = fuzzy_read(spatial_dir, "seaports"),
    Airport = fuzzy_read(spatial_dir, "airports")) %>%
    keep(~ inherits(.x, "SpatVector"))

  ports <- names(ports) %>%
    map(\(x) {
      mutate(ports[[x]], type = x, label = toupper(str_sub(x, 1, 1)), .keep = "none")
    })
  if (!inherits(roads, "SpatVector") & length(ports) == 0) return(NULL)
  ports <- reduce(ports, rbind) %>%
    arrange(label)
  # browser()
  plot_static_layer(aoi_only = T, plot_aoi = F, zoom_adj = zoom_adjustment) +
    geom_spatvector(data = roads, aes(color = "Primary road")) +
    scale_color_manual(values = c("Primary road" = "grey20"), name = "") +
    ggnewscale::new_scale_color() +
    geom_spatvector(data = ports, aes(shape = type, color = type), fill = "blue", size = 2) +
    scale_color_manual(values =
      c("RoRo Seaport" = "blue", 
      "Non-RoRo Seaport" = "dodgerblue",
      "Airport" = "forestgreen"), name = "Port type") +
    # scale_shape_manual(values = c("RoRo Seaport" = 21, "Airport" = 2, "Non-RoRo Seaport" = 1), name = "Port type") +
    scale_shape_manual(values = c("RoRo Seaport" = 19, "Airport" = 2, "Non-RoRo Seaport" = 1), name = "Port type") +
    coord_3857_bounds(static_map_bounds)
}
plots$ports <- plot_ports()

# Overlays ---------------------------------------------------------------------
overlay_plots <- list()

# Vegetation over built-up area ------------------------------------------------
plot_vegetation_over_built <- function() {
  built <- fuzzy_read(spatial_dir, "built_over_time")
  if (!inherits(built, c("SpatRaster", "SpatVector"))) return(NULL)
  built <- classify(built, cbind(c(-Inf, 2026), c(2026, Inf), c(2025, NA)),
                    include.lowest = TRUE)
  built <- as.polygons(built)
  # plots$vegetation +
  #   ggpattern::geom_sf_pattern(data = built, color = NA, fill = NA,
  #   aes(pattern = "2025 built-up area"),
  #   pattern_spacing = 0.02, pattern_fill = NA, pattern_density = 0.5) +
  #   ggpattern::scale_pattern_manual(values = "stripe", name = "") +
  #   coord_3857_bounds(static_map_bounds)
  plots$builtup_binary <- plot_static_layer(aoi_only = T, plot_aoi = F) +
    ggpattern::geom_sf_pattern(data = built, color = NA, fill = NA, aes(pattern = "2025 built-up area"),
    pattern_spacing = 0.0125, pattern_fill = NA, pattern_density = .5, pattern_size = .25) +
    ggpattern::scale_pattern_manual(values = "stripe", name = "")   +
    coord_3857_bounds(static_map_bounds)
  veg <- fuzzy_read(spatial_dir, layer_params$vegetation$fuzzy_string)
  if (!inherits(veg, c("SpatRaster", "SpatVector"))) return(NULL)
  plot_static_layer(veg, "vegetation", baseplot = plots$builtup_binary) +
    labs(caption = "Map data from GHSL (GHS-BUILT-S R2023A) and ESA (Sentinel-2).") 
}
overlay_plots$vegetation_builtup <- plot_vegetation_over_built()


# Extreme LST

plot_extreme_lst <- function() {
lst_data <- fuzzy_read(spatial_dir, "extreme-lst")
if (!inherits(lst_data, c("SpatVector", "SpatRaster"))) return(NULL)
  lst_data_smooth <- smooth(lst_data, method = "ksmooth", smoothness = 3)
  names(plots) %>%
    str_subset("population|builtup|building|proximity|points|infrastructure") %>%
    str_subset("binary", negate = T) %>%
    walk(\(x) {
      old_caption <- ggplot_build(plots[[x]])$plot$labels$caption
      new_caption <- layer_params$lst_extreme$caption
      caption <- paste0(str_replace(old_caption, "\\.", ", "), str_replace(new_caption, "Map data from", "and"))
      overlay_plots[[paste0("extreme_lst_", x)]] <<- plots[[x]] +
        ggnewscale::new_scale_color() +
        geom_sf(data = lst_data_smooth, aes(color = "Extreme LST"), fill = NA, linewidth = .6) +
        scale_color_manual(values = "red", name = "") +
        coord_3857_bounds(static_map_bounds) +
        labs(caption = caption)
    })
}
plot_extreme_lst()

# Liquefaction susceptibility --------------------------------------------------

liquefaction_data <- fuzzy_read(spatial_dir, "liquefa")
if (inherits(liquefaction_data, c("SpatVector", "SpatRaster"))) {
  names(liquefaction_data) <- "liquefaction"

  names(plots) %>%
    str_subset("population|builtup|building|proximity|points|infrastructure") %>%
    str_subset("binary", negate = T) %>%
    # .[27] %>%
    walk(\(x) {
      # browser()
      old_caption <- ggplot_build(plots[[x]])$plot$labels$caption
      new_caption <- layer_params$liquefaction$caption
      caption <- paste0(str_replace(old_caption, "\\.", "; "), str_replace(new_caption, "Map data from", "and from"))
      overlay_plots[[paste0("liquefaction_", x)]] <<-
        plot_static_layer(data = liquefaction_data, yaml_key = "liquefaction", baseplot = plots[[x]],
          alpha = .5, no_new_theme = F) +
          labs(caption = caption)

      # For point data, considering plotting points on top
      # …
    })
}

# Flooding overlays ------------------------------------------------------------
flood_data <- fuzzy_read(spatial_dir, "combined_flooding_2020.tif$")
if (inherits(flood_data, c("SpatRaster", "SpatVector"))) {
  flood_data <- terra::crop(flood_data, static_map_bounds)
  # Temporary fix for if layer is all NAs
  if (all(is.na(values(flood_data)))) values(flood_data)[1] <- 0
  flood_type <- "combined_flooding"
  plots[[flood_type]] <- plot_static_layer(
    flood_data, yaml_key = flood_type,
    plot_aoi = T, plot_wards = !is.null(wards))
  names(plots) %>%
    str_subset("population|builtup|building|proximity|points|infrastructure") %>%
    str_subset("binary", negate = T) %>%
    # .[27] %>%
    walk(\(x) {
      old_caption <- ggplot_build(plots[[x]])$plot$labels$caption
      new_caption <- layer_params$combined_flooding$caption
      caption <- paste0(str_replace(old_caption, "\\.", ", "), str_replace(new_caption, "Map data from", "and"))
      overlay_plots[[paste(flood_type, x, sep = "_")]] <<-
        plot_static_layer(data = flood_data, yaml_key = flood_type, baseplot = plots[[x]], no_new_theme = F) +
        labs(caption = caption)
    })
}
