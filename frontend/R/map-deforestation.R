tryCatch_named("deforest", {
  deforest <- fuzzy_read(spatial_dir, layer_params$deforest$fuzzy_string, rast)
  plots$forest_deforest <- plot_static_layer(deforest, "deforest", baseplot = plots$forest)
})