RedOr <- c("#f2d7b5", "#ebb391", "#e28e73", "#d76a61", "#ca5a7e","#8c2e71", "#5d1f3b")

zones <- c('commercial', 'industrial', 'residential')

for (zone in zones){
  tryCatch({
    freq <- fuzzy_read(spatial_dir, paste0("_freq_", zone ,".*.tif$"))
    if (!inherits(freq, "SpatRaster")) {
      message(paste("Skipping", zone, "- freq file not found"))
      next
    }
    freq[freq == 0] <- NA

    kde <- fuzzy_read(spatial_dir, paste0("_kde_", zone ,".*.tif$"))
    if (!inherits(kde, "SpatRaster")) {
      message(paste("Skipping", zone, "- kde file not found"))
      next
    }
    kde <- setMinMax(kde)
    minmax(kde)

    osm_points <- st_read(file.path(spatial_dir,
                                      paste0(city, '_osm_', zone, '.gpkg' )),
                          quiet = TRUE)

    p <- ggplot() +
      annotation_map_tile(type = "cartolight", zoom = 12, progress = "none") +

      geom_spatraster(data = freq, na.rm = TRUE, alpha = 0.85) +
      geom_spatraster_contour(data = kde, color = "white", linewidth = 0.5, bins = 10, alpha = 0.8) +
      geom_sf(data = osm_points, size = 0.1, color = "grey", alpha = 0.4) +

      scale_fill_gradientn(
        name = paste0(
          str_to_title(zone),
          " Distribution<br><br>",
          "<i><span style='font-size:11pt;'>",
          "Based on OSM POIs at 1km<sup>2</sup></span><br>",
          "with kernel density estimation <br> contours</i><br>"
        ),
        colours = RedOr,
        breaks = c(0.2, 0.4, 0.6, 0.8),
        na.value = NA,
        guide = guide_colorbar(
          title.hjust = 0,
          title.theme = element_markdown()
        )
      ) +
      {if (!is.null(wards))
        geom_spatvector(data = wards, fill = NA, color = "gray30", linewidth = 0.25)
      else
        geom_spatvector(data = aoi, fill = NA, color = "black", linewidth = 0.4)
      } +

      {if (!is.null(wards))
        geom_spatvector(data = wards %>%
                          aggregate( by = "COD_CAV", dissolve = TRUE) %>%
                          fillHoles(),
                        color = "gray30", fill = NA, linetype = "solid", linewidth = .525)
      } +
      {if (!is.null(wards))

        geom_spatvector(data = wards %>%
                          aggregate( by = "COD_DEPT", dissolve = TRUE) %>%
                          fillHoles(),
                        color = "gray30", fill = NA, linetype = "solid", linewidth = .75)

      }+
      theme_custom() +
      coord_3857_bounds(static_map_bounds) +
      annotation_north_arrow(style = north_arrow_minimal, location = "br", height = unit(1, "cm")) +
      annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33),
                       height = unit(0.25, "cm"))

    save_plot(
      plot = p,
      filename = paste0(zone, "_acitivity_freq.png"),
      directory = styled_maps_dir,
      map_height = map_height,
      map_width = map_width,
      dpi = 200,
      rel_widths = map_portions
    )

    message(paste("Success:", zone, "economic activity freq"))
  }, error = function(e) {
    message(paste("Failure:", zone, "economic_activity_freq -", e$message))
  })
}









