# Historical Fire --------------------------------------------------------------
# Non-standard because usees larger extent
burnt_area <- fuzzy_read(spatial_dir, layer_params$burnt_area$fuzzy_string)
if (inherits(burnt_area, c("SpatVector", "SpatRaster"), which = F)) {
  burnt_extent <- aspect_buffer(
    vect(ext(burnt_area), crs = crs(burnt_area)),
    aspect_ratio, buffer_percent = 0.05)
  plots$burnt_area <- plot_static_layer(
    burnt_area, "burnt_area",
    static_map_bounds = burnt_extent)
  message("Success: Historical burnt area")
}
