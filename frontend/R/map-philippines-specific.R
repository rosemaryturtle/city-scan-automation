# Philippines specific maps

# Buildings --------------------------------------------------------------------

buildings <- fuzzy_read(spatial_dir, "Buildings")
if (inherits(buildings, "SpatVector")) {
  plots$buildings <- plot_static_layer(aoi_only = T, plot_aoi = T) +
    geom_spatvector(data = buildings, aes(fill = "Buildings"), color = NA) +
    scale_fill_manual(values = "grey35", name = "") +
    coord_3857_bounds(static_map_bounds)
}

# Ports & road networks --------------------------------------------------------

roads <- fuzzy_read(spatial_dir, "primary_roads")
ports <- list(
  RoRo = fuzzy_read(spatial_dir, "roro_ports"),
  Seaports = fuzzy_read(spatial_dir, "seaports"),
  Airports = fuzzy_read(spatial_dir, "airports")) %>%
  keep(~ inherits(.x, "SpatVector"))

ports <- names(ports) %>%
  map(\(x) {
    mutate(ports[[x]], type = x, label = toupper(str_sub(x, 1, 1)), .keep = "none")
  })
if (inherits(roads, "SpatVector") | length(ports) > 0) {
  ports <- reduce(ports, rbind)
  plots$ports <- plot_static_layer(aoi_only = T, plot_aoi = F) +
    geom_spatvector(data = roads, aes(color = "Primary road")) +
    scale_color_manual(values = c("Primary road" = "grey20"), name = "") +
    ggnewscale::new_scale_color() +
    geom_spatvector(data = ports, aes(shape = type, color = type)) +
    scale_color_manual(values = c("RoRo" = "dodgerblue", "Seaport" = "dodgerblue", "Airport" = "red"), name = "Port type") +
    scale_shape_manual(values = c("RoRo" = 16, "Airport" = 2, "Seaport" = 1), name = "Port type") +
    coord_3857_bounds(static_map_bounds)
}

# Overlays ---------------------------------------------------------------------
overlay_plots <- list()

# Vegetation over built-up area ------------------------------------------------
built <- fuzzy_read(spatial_dir, "built_over_time")
if (inherits(built, c("SpatRaster", "SpatVector"))) {
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
  overlay_plots$vegetation_builtup <- plot_static_layer(veg, "vegetation", baseplot = plots$builtup_binary)
}

# Extreme LST

librarian::shelf(smoothr, ggpattern)
lst_data <- fuzzy_read(spatial_dir, "extreme-lst")
if (inherits(lst_data, c("SpatVector", "SpatRaster"))) {
  lst_data_smooth <- smooth(lst_data, method = "ksmooth", smoothness = 3)
  names(plots) %>%
    str_subset("population|builtup|building|proximity") %>%
    str_subset("binary", negate = T) %>%
    walk(\(x) {
      overlay_plots[[paste0("extreme_lst_", x)]] <<- plots[[x]] +
        ggnewscale::new_scale_color() +
        geom_sf(data = lst_data_smooth, aes(color = "Extreme LST"), fill = NA, linewidth = .6) +
        scale_color_manual(values = "red", name = "") +
        coord_3857_bounds(static_map_bounds)
    })
}

# Liquefaction susceptibility --------------------------------------------------

liquefaction_data <- fuzzy_read(spatial_dir, "liquefa")
if (inherits(liquefaction_data, c("SpatVector", "SpatRaster"))) {
  names(liquefaction_data) <- "liquefaction"

  names(plots) %>%
    str_subset("population|builtup|building|proximity") %>%
    str_subset("binary", negate = T) %>%
    walk(\(x) {

      overlay_plots[[paste0("liquefaction_", x)]] <<-
        plot_static_layer(data = liquefaction_data, yaml_key = "liquefaction", baseplot = plots[[x]],
          alpha = .5)

      # For point data, considering plotting points on top
      # …
    })
}
