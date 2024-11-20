deforest <- fuzzy_read(spatial_dir, layer_params$deforest$fuzzy_string, rast)
if (inherits(deforest, c("SpatVector", "SpatRaster"))) {
  values(deforest) <- values(deforest) + 2000 # Move to pre-mapping
  plots$deforest <- plot_static_layer(
    data = deforest, yaml_key = "deforest",
    plot_aoi = T, plot_wards = !is.null(wards))
  plots$forest_deforest <- plot_static_layer(deforest, "deforest", baseplot = plots$forest)
  message("Success: forest_deforestation")
}