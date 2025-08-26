# Historical Fire --------------------------------------------------------------
# Non-standard because uses larger extent
tryCatch_named("burnt_area", {
  burnt_area <- fuzzy_read(spatial_dir, layer_params$burnt_area$fuzzy_string)
  if (inherits(burnt_area, c("SpatVector", "SpatRaster"), which = F)) {
    plots$burnt_area <- plot_static_layer(
      burnt_area, "burnt_area",
      static_map_bounds = static_map_bounds,
      plot_aoi = T,
      zoom_adj = zoom_adjustment)
  }
})
