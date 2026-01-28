# Map GHS expansion - residential and non-residential
# This script should be sourced after setup.R
# Requires: ghs_res_expansion.tif and ghs_nres_expansion.tif in spatial_dir

tryCatch({
  # Color palettes
  res_cols <- c("#d8daeb", "#b2abd2", "#8073ac", "#542788", "#2d004b")
  nres_cols <- c("#fee0b6", "#fdb863", "#e08214", "#b35806", "#7f3b08")



  # Labels
  labs <- c("Before 1986", "1986-1995", "1996-2005", "2006-2015", "After 2016")

  # Read expansion rasters
  ghs_res <- fuzzy_read(spatial_dir, "ghs_res_expansion.*.tif$")
  ghs_nres <- fuzzy_read(spatial_dir, "ghs_nres_expansion.*.tif$")

  if (!inherits(ghs_res, "SpatRaster")) {
    stop("GHS residential expansion file not found")
  }

  if (!inherits(ghs_nres, "SpatRaster")) {
    stop("GHS non-residential expansion file not found")
  }

  # Bin the rasters into categories
  ghs_res_binned <- classify(ghs_res,
                              matrix(c(-Inf, 1986, 1,
                                      1986, 1995, 2,
                                      1995, 2005, 3,
                                      2005, 2015, 4,
                                      2015, Inf, 5),
                                    ncol = 3, byrow = TRUE))

  ghs_nres_binned <- classify(ghs_nres,
                               matrix(c(-Inf, 1986, 1,
                                       1986, 1995, 2,
                                       1995, 2005, 3,
                                       2005, 2015, 4,
                                       2015, Inf, 5),
                                     ncol = 3, byrow = TRUE))

  # Set levels
  levels(ghs_res_binned) <- data.frame(id = 1:5, label = labs)
  levels(ghs_nres_binned) <- data.frame(id = 1:5, label = labs)

  # 1. Residential Expansion
  p_res_exp <- ggplot() +
    annotation_map_tile(type = "cartolight", zoom = get_zoom_level(static_map_bounds) + zoom_adjustment, progress = "none") +
    geom_spatraster(data = ghs_res_binned, as.factor = TRUE, maxcell = 5e5, na.rm = TRUE, alpha = 0.7) +
    scale_fill_manual(
      name = "Residential",
      values = setNames(res_cols, labs),
      na.value = NA,
      na.translate = FALSE
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
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm"))




  save_plot(
    plot = p_res_exp,
    filename = "ghs_residential_expansion.png",
    directory = styled_maps_dir,
    map_height = map_height,
    map_width = map_width,
    dpi = 200,
    rel_widths = map_portions
  )

  # 2. Non-Residential Expansion
  p_nres_exp <- ggplot() +
    annotation_map_tile(type = "cartolight", zoom = get_zoom_level(static_map_bounds) + zoom_adjustment, progress = "none") +
    geom_spatraster(data = ghs_nres_binned, as.factor = TRUE, maxcell = 5e5, na.rm = TRUE, alpha = 0.7) +
    scale_fill_manual(
      name = "Non-Residential",
      values = setNames(nres_cols, labs),
      na.value = NA,
      na.translate = FALSE
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
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm"))

  save_plot(
    plot = p_nres_exp,
    filename = "ghs_nonresidential_expansion.png",
    directory = styled_maps_dir,
    map_height = map_height,
    map_width = map_width,
    dpi = 200,
    rel_widths = map_portions
  )

  message("Success: ghs_residential_expansion")
  message("Success: ghs_nonresidential_expansion")

}, error = function(e) {
  message(paste("Failure: ghs_expansion -", e$message))
})
