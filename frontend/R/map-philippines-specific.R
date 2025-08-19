# Philippines specific maps

# Buildings

buildings <- fuzzy_read(spatial_dir, "Buildings")

plots$buildings <- plot_static_layer(aoi_only = T, plot_aoi = F) +
  geom_spatvector(data = buildings, aes(fill = "Buildings"), color = NA) +
  scale_fill_manual(values = "grey35", name = "") +
  coord_3857_bounds(static_map_bounds)


# Vegetation over built-up area ------------------------------------------------
built <- fuzzy_read(spatial_dir, "built_over_time")
built <- classify(built, cbind(c(-Inf, 2026), c(2026, Inf), c(2025, NA)),
                  include.lowest = TRUE)
# built[!is.na(built)] <- 1
built <- as.polygons(built)
# plots$vegetation +
#   ggpattern::geom_sf_pattern(data = built, color = NA, fill = NA,
#   aes(pattern = "2025 built-up area"),
#   pattern_spacing = 0.02, pattern_fill = NA, pattern_density = 0.5) +
#   ggpattern::scale_pattern_manual(values = "stripe", name = "") +
#   coord_3857_bounds(static_map_bounds)
plots$builtup_binary <- plot_static_layer(aoi_only = T, plot_aoi = F) +
  ggpattern::geom_sf_pattern(data = built, color = NA, fill = NA, aes(pattern = "2025 built-up area"),
  pattern_spacing = 0.02, pattern_fill = NA, pattern_density = 0.5) +
  ggpattern::scale_pattern_manual(values = "stripe", name = "")   +
  coord_3857_bounds(static_map_bounds)
veg <- data <- fuzzy_read(spatial_dir, layer_params$vegetation$fuzzy_string)
plots$vegetation_builtup <- plot_static_layer(veg, "vegetation", baseplot = plots$builtup_binary)

# Map of building footprints ---------------------------------------------------
# Can probably be a standard map

# Overlays with flooding, extreme LST and liquefaction susceptibility ----------
# [ ] Map of population density 1970–2030 (GHSL)
# [ ] Map of built-up area change from 1970–2030 (GHSL 2023)
# [ ] Map of building footprints (Microsoft Building Footprints or Google)
# [ ] Map of schools, with isochrones (OpenStreetMap)
# [ ] Map of health facilities, with isochrones (OpenStreetMap)
# [ ] Map of public spaces, with isochrones (OpenStreetMap)
# [ ] Map of special economic zones, with isochrones
# [ ] Map of SWM infrastructure, with isochrones (OSM)
# [ ] Map of water infrastructure, with isochrones (OSM)
# [ ] Map of public transit stops, with isochrones (OSM)

# Extreme LST

librarian::shelf(smoothr, ggpattern)
data <- fuzzy_read(spatial_dir, "extreme-lst")
data_inverse <- erase(aoi, data)
data_smooth <- smooth(data, method = "ksmooth", smoothness = 3)
test_plots <- list()
names(plots) %>%
# "population" %>%
  # str_subset("school_points") %>%
  str_subset("population|builtup|school_points|waste_points|public_space_points|health_points|buildings") %>%
  str_subset("binary", negate = T) %>%
  walk(\(x) {
    test_plots[[paste0(x, "_outline_smooth")]] <<- plots[[x]] +
      ggnewscale::new_scale_color() +
      geom_sf(data = data_smooth, aes(color = "Extreme LST"), fill = NA, linewidth = .6) +
      scale_color_manual(values = "red", name = "") +
      coord_3857_bounds(static_map_bounds)
})

# Liquefaction susceptibility ---------------------------------------------

data <- fuzzy_read(spatial_dir, "liquefa")
names(data) <- "liquefaction"
plot(data)

names(plots) %>%
# "population" %>%
  # str_subset("school_points") %>%
  str_subset("population|builtup|school_points|waste_points|public_space_points|health_points|building") %>%
  str_subset("binary", negate = T) %>%
  walk(\(x) {

    test_plots[[paste0(x, "_liquefaction_fill")]] <<-
      plot_static_layer(data = data, yaml_key = "liquefaction", baseplot = plots[[x]])

    # For point data, considering plotting points on top

    # str(test_plots[[paste0(x, "_liquefaction_fill")]]$layers %>% keep(~ "aes_params" %in% names(.x) && "alpha" %in% names(.x$aes_params)))

  })

for (name in names(test_plots)) {
  print(name)
  save_plot(test_plots[[name]], filename = glue("{name}.png"), directory = styled_maps_dir,
    map_height = map_height, map_width = map_width, dpi = 200, rel_widths = map_portions)
}

