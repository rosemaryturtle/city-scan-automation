tryCatch_named("deforest", {
  deforest <- fuzzy_read(spatial_dir, layer_params$deforest$fuzzy_string, rast)
  titles <- unlist(layer_params$deforest[c("title", "title_fr")])
  subtitles <- unlist(layer_params$deforest[c("subtitle", "subtitle_fr")])
  plots$forest_deforest <- plot_static_layer(deforest, "deforest", baseplot = plots$forest)
})