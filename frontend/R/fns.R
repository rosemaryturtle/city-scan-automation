# Map Functions ----------------------------------------------------------------
fuzzy_read <- function(dir, fuzzy_string, FUN = NULL, path = T, convert_to_vect = F, ...) {
  file <- list.files(dir) %>% str_subset(fuzzy_string) #%>%
  if (length(file) > 1) warning(paste("Too many", fuzzy_string, "files in", dir))
  if (length(file) < 1) {
    file <- list.files(dir, recursive = T) %>% str_subset(fuzzy_string)
    if (length(file) > 1) warning(paste("Too many", fuzzy_string, "files in", dir))
    if (length(file) < 1) warning(paste("No", fuzzy_string, "file in", dir))
  }
  if (length(file) == 1) {
    if (is.null(FUN)) {
      FUN <- if (tolower(str_sub(file, -4, -1)) == ".tif") rast else vect
    }
    if (!path) {
      content <- suppressMessages(FUN(dir, file, ...))
    } else {
      file_path <- file.path(dir, file)
      content <- suppressMessages(FUN(file_path, ...))
    }
    if (convert_to_vect && class(content)[1] %in% c("SpatRaster", "RasterLayer")) {
      content <- rast_as_vect(content)
    }
    return(content)
  } else {
    return(NA)
  }
}

rast_as_vect <- function(x, digits = 8, ...) {
  if (class(x) == "SpatVector") return(x)
  if (is.character(x)) x <- rast(x, ...)
  out <- as.polygons(x, digits = digits)
  return(out)
}

exists_and_true <- \(x) !is.null(x) && is.logical(x) && x

# Functions for making the maps
plot_basemap <- function(basemap_style = "vector") {
  aoi_bounds <- st_bbox(aoi)
  basemap <-
    leaflet(
      data = aoi,
      # Need to probably do this with javascript
      height = "calc(100vh - 2rem)",
      width = "100%",
      options = leafletOptions(zoomControl = F, zoomSnap = 0.1)) %>% 
    fitBounds(
      lng1 = unname(aoi_bounds$xmin - (aoi_bounds$xmax - aoi_bounds$xmin)/20),
      lat1 = unname(aoi_bounds$ymin - (aoi_bounds$ymax - aoi_bounds$ymin)/20),
      lng2 = unname(aoi_bounds$xmax + (aoi_bounds$xmax - aoi_bounds$xmin)/20),
      lat2 = unname(aoi_bounds$ymax + (aoi_bounds$ymax - aoi_bounds$ymin)/20))
  if (basemap_style == "satellite") { 
    basemap <- basemap %>% addProviderTiles(., providers$Esri.WorldImagery,
                      options = providerTileOptions(opacity = basemap_opacity))
  } else if (basemap_style == "vector") {
    # addProviderTiles(., providers$Wikimedia,
    basemap <- basemap %>%
      addProviderTiles(providers$CartoDB.Positron)
      # addProviderTiles(., providers$Stadia.AlidadeSmooth,
      #  options = providerTileOptions(opacity = basemap_opacity))
  }
  return(basemap)
}

prepare_parameters <- function(yaml_key, ...) {
  # Override the layers.yaml parameters with arguments provided to ...
  # Parameters include bins, breaks, center, color_scale, domain, labFormat, and palette
  layer_params <- read_yaml(layer_params_file)
  if (yaml_key %ni% names(layer_params)) stop(paste(yaml_key, "is not a key in", layer_params_file))
  yaml_params <- layer_params[[yaml_key]]
  new_params <- list(...)
  kept_params <- yaml_params[!names(yaml_params) %in% names(new_params)]
  params <- c(new_params, kept_params)

  params$breaks <- unlist(params$breaks) # Necessary for some color scales
  if (is.null(params$bins)) {
    params$bins <- if(is.null(params$breaks)) 0 else length(params$breaks)
  }
  if (is.null(params$stroke)) params$stroke <- NA
  if (exists_and_true(params$factor) & is.null(params$breaks)) {
    params$breaks <- params$labels
  }

  # Apply layer transparency to palette
  params$palette <- sapply(params$palette, \(p) {
    # If palette has no alpha, add
    layer_alpha <- params$alpha %||% layer_alpha
    if (p == "transparent") return("#FFFFFF00")
    if (nchar(p) == 7 | substr(p, 1, 1) != "#") return(scales::alpha(p, layer_alpha))
    # If palette already has alpha, multiply
    if (nchar(p) == 9) {
      alpha_hex <- as.hexmode(substr(p, 8, 9))
      new_alpha_hex <- as.character(alpha_hex * layer_alpha)
      # At one point I used the following; what was I trying to solve for? This
      # could make colors with alpha < 1 more opaque than colors with alpha = 1
      # new_alpha_hex <- as.character(as.hexmode("ff") - (as.hexmode("ff") - alpha_hex) * layer_alpha)
      if (nchar(new_alpha_hex) == 1) new_alpha_hex <- paste0(0, new_alpha_hex)
      new_p <- paste0(substr(p, 1, 7), new_alpha_hex)
      return(new_p)
    }
    warning(paste("Palette value", p, "is not of length 6 or 8"))
  }, USE.NAMES = F)

  return(params)
}

create_layer_function <- function(data, yaml_key = NULL, params = NULL, color_scale = NULL, message = F, fuzzy_string = NULL, ...) {  
  if (message) message("Check if data is in EPSG:3857; if not, raster is being re-projected")
  if (is.null(params)) {
    params <- prepare_parameters(yaml_key, ...)
  }
  if (!is.null(params$data_variable)) data <- data[params$data_variable]
  
  if (nrow(data) == 0) stop("Data object has no rows (0 geometries or 0 cells)")
  if (inherits(data, "SpatVector") && all(is.na(values(data)))) stop("Data object has no rows (0 geometries or 0 cells)")
  
  if (exists_and_true(params$factor)) {
    layer_values <- ordered(
      get_layer_values(data),
      levels = params$breaks,
      labels = params$labels)
    data <- 
      set_layer_values(
        data = data,
        values = layer_values)
  } else {
    layer_values <- get_layer_values(data)
    if(params$bins > 0 && is.null(params$breaks)) {
      params$breaks <- break_pretty2(
                  data = layer_values, n = params$bins + 1, FUN = signif,
                  method = params$breaks_method %>% {if(is.null(.)) "quantile" else .})
    }
    if (!is.null(params$breaks)) {
      # sig_digits <- max(nchar(str_replace_all(as.character(abs(breaks)), c("^[0\\.]*|\\." = ""))))
      # round_digits <- max(nchar(str_extract(params$breaks %>% {. - floor(params$breaks)}, "(?<=\\.).*")), na.rm = T)
      round_digits <- max(nchar(str_replace(params$breaks %>% {. - floor(params$breaks)}, "^.*\\.", "")), na.rm = T)
      layer_values <- round(layer_values, round_digits)
    } else {
      layer_values <- round(layer_values, 2)
    }
    data <- set_layer_values(data, values = layer_values)
  }
  labels <- label_maker(x = layer_values,
                        levels = params$breaks,
                        labels = params$labels,
                        suffix = params$suffix)

  if (is.null(color_scale) & length(params$palette) > 0) {
    domain <- set_domain(layer_values, domain = params$domain, center = params$center, factor = params$factor)
    color_scale <- create_color_scale(
      domain = domain,
      palette = params$palette,
      center = params$center,
      # bins = if (is.null(params$breaks)) params$bins else params$breaks
      bins = params$bins,
      breaks = params$breaks,
      factor = params$factor,
      levels = levels(layer_values))
  }

  # if (length(params$stroke$palette) > 0) {
  #   stroke_color_scale <- create_color_scale(
  #     domain = range(data)[,params$stroke$variable],
  #     palette = params$stroke$palette,
  #     bins = params$bins,
  #     breaks = params$breaks
  #   )
  # }

v <- data %>%
  as.polygons(digits = 4)
v_styled <- v %>%
  rename(value = 1) %>%
  mutate(
    fillColor = color_scale(value),
    label = label_maker(
      x = value,
      levels = params$breaks,
      labels = params$labels,
      suffix = params$suffix))
fgb_path <- file.path(fgb_dir, paste0(yaml_key, ".fgb"))
writeVector(v_styled, fgb_path, overwrite = T, filetype = "FlatGeobuf")


# Where did this come from? Appeared 2025-06-02??
  # # If the data is a raster, we need to set the domain to the range of the values
  # # in the raster. If it is a vector, we can use the values in the first column.
  # if (class(data)[1] %in% c("SpatRaster", "RasterLayer")) {
  #   domain <- if (is.null(params$domain)) range(layer_values, na.rm = T) else params$domain
  # } else {
  #   domain <- if (is.null(params$domain)) range(layer_values, na.rm = T) else params$domain
  # }
  # legend_opacity <- params$legend_opacity %||% 0.8

# I have moved the formerly-present note on lessons from the CRC Workshop code to my `Week of 2023-11-26` note in Obsidian.

### !!! I need to pull labels out because not always numeric so can't be signif

  layer_function <- function(maps, show = T) {
    if (class(data)[1] %in% c("SpatRaster", "RasterLayer")) {
    # RASTER
      # maps <- maps %>% 
      #   addRasterImage(data, opacity = 1,
      #     colors = color_scale,
      #     # For now the group needs to match the section id in the text-column
      #     # group = params$title %>% str_replace_all("\\s", "-") %>% tolower(),
      #     group = params$group_id)
      maps <- maps %>% 
        addFgb(
          file = fgb_path,
          color = NULL,
          fill = T,
          label = "label",
          fillOpacity = 0.9,
          group = params$group_id)
    } else if (class(data)[1] %in% c("SpatVector", "sf")) {
      # VECTOR
      if ( # Add circle markers if geometry type is "points"
        (class(data)[1] == "SpatVector" && geomtype(data) == "points") |
        (class(data)[1] == "sf" && "POINTS" %in% st_geometry_type(data))) {
        maps <- maps %>%
          addCircles(
            data = data,
            color = params$palette,
            weight = params$weight,
            # opacity = 0.9,
            group = params$group_id,
            # label = ~ signif(pull(data[[1]]), 6)) # Needs to at least be 4 
            label = labels)
      } else { # Otherwise, draw the geometries
        maps <- maps %>%
          addPolygons(
            data = data,
            fill = if(is.null(params$fill) || params$fill) T else F,
            fillColor = ~color_scale(layer_values),
            fillOpacity = 0.9,
            stroke = if(!is.null(params$stroke) && !is.na(params$stroke) && params$stroke != F) T else F,
            color = if(!is.null(params$stroke) && !is.na(params$stroke) && params$stroke == T) ~color_scale(layer_values) else params$stroke,
            weight = params$weight,
            opacity = 0.9,
            group = params$group_id,
            # label = ~ signif(pull(data[[1]]), 6)) # Needs to at least be 4 
            label = labels)
    }} else {
      stop("Data is not spatRaster, RasterLayer, spatVector or sf")
    }
    # See here for formatting the legend: https://stackoverflow.com/a/35803245/5009249
    legend_args <- list(
      map = maps,
      # data = data,
      position = 'bottomright',
      values = domain,
      # values = if (is.null(params$breaks)) domain else params$breaks,
      # pal = if (is.null(params$labels) | is.null(params$breaks)) color_scale else NULL,
      pal = if (diff(lengths(list(params$labels, params$breaks))) == 1) NULL else color_scale,
      # colors = if (is.null(params$labels) | is.null(params$breaks)) NULL else if (diff(lengths(list(params$labels, params$breaks))) == 1) color_scale(head(params$breaks, -1)) else color_scale(params$breaks),
      colors = if (diff(lengths(list(params$labels, params$breaks))) == 1) color_scale(head(params$breaks, -1)) else NULL,
      opacity = legend_opacity,
      # bins = params$bins,
      # bins = 3,  # legend color ramp does not render if there are too many bins
      labels = params$labels,
      title = format_title(params$title, params$subtitle),
      # labFormat = params$labFormat,
      # labFormat = labelFormat(transform = function(x) label_maker(x = x, levels = params$breaks, labels = params$labels)),
      # labFormat = function(type, breaks, labels) {
      # }
      # group = params$title %>% str_replace_all("\\s", "-") %>% tolower())
      group = params$group_id)
    legend_args <- Filter(Negate(is.null), legend_args)
    # Using do.call so I can conditionally include args (i.e., pal and colors)
    maps <- do.call(addLegend, legend_args)
    # if (!show) maps <- hideGroup(maps, group = layer_id)
    return(maps)
  }

  return(layer_function)
}

plot_static_layer <- function(
    data, yaml_key, baseplot = NULL, static_map_bounds, zoom_adj = 0,
    expansion, aoi_stroke = list(color = "grey30", linewidth = 0.4),
    plot_aoi = T, aoi_only = F, plot_wards = F, plot_roads = F, ...) {
  if (aoi_only) {
    layer <- NULL
  } else { 
    # Create geom and scales
    params <- prepare_parameters(yaml_key = yaml_key, ...)
    if (!is.null(params$data_variable)) data <- data[params$data_variable]
    if (exists_and_true(params$factor)) {
      data <- 
        set_layer_values(
          data = data,
          values = ordered(get_layer_values(data),
                          levels = params$breaks,
                          labels = params$labels))
      params$palette <- setNames(params$palette, params$labels)
    }
    if(params$bins > 0 && is.null(params$breaks)) {
      params$breaks <- break_pretty2(
        data = get_layer_values(data), n = params$bins + 1, FUN = signif,
        method = params$breaks_method %>% {if(is.null(.)) "quantile" else .})
    }
    geom <- create_geom(data, params)
    data_type <- type_data(data)
    scales <- list(
      fill_scale(data_type, params),
      color_scale(data_type, params),
      linewidth_scale(data_type, params)) %>%
      .[lengths(.) > 1]
    theme <- theme_legend(data, params)
    layer <- list(geom = geom, scale = scales, theme = theme)
  }

  # I should make all these functions into a package and then define city_dir,
  # map_width, static_map_bounds, etc., as package level variables that get set
  # with set_.*() variables

  if ("static_map_bounds" %in% ls() && missing(static_map_bounds)) remove(static_map_bounds, inherits = F)
  if (!exists("static_map_bounds")) {
    warning(paste("static_map_bounds does not exist. Define one globally or as an",
      "argument to plot_static_layer. A plot extent will be defined using `aoi`."))
    if (exists("aoi")) {
      static_map_bounds <- aspect_buffer(aoi, aspect_ratio, buffer_percent = 0.05)
  } else stop("No object `aoi` exists.")
  }

  if (!missing(expansion)) {
    aspect_ratio <- as.vector(ext(project(static_map_bounds, "epsg:3857"))) %>%
      { diff(.[1:2])/diff(.[3:4]) }
    static_map_bounds <- aspect_buffer(static_map_bounds, aspect_ratio, buffer_percent = expansion - 1)
  }

  # Plot geom and scales on baseplot
  baseplot <- if (is.null(baseplot) || identical(baseplot, "vector")) {
    ggplot() +
      geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
      annotation_map_tile(type = "cartolight", zoom = get_zoom_level(static_map_bounds) + zoom_adj, progress = "none")
  } else if (is.character(baseplot)) {
    ggplot() +
      geom_spatvector(data = static_map_bounds, fill = NA, color = NA) +
      annotation_map_tile(type = baseplot, zoom = get_zoom_level(static_map_bounds) + zoom_adj, progress = "none")
  } else { baseplot + ggnewscale::new_scale_fill() }
  p <- baseplot +
    layer + 
    annotation_north_arrow(style = north_arrow_minimal, location = "br", height = unit(1, "cm")) +
    annotation_scale(style = "ticks", aes(unit_category = "metric", width_hint = 0.33), height = unit(0.25, "cm")) +        
    theme_custom()
  if (plot_roads) p <- p +
    geom_spatvector(data = roads, aes(linewidth = road_type), color = "white") +
    scale_linewidth_manual(values = c("Secondary" = 0.25, "Primary" = 1), guide = "none")
  if (plot_aoi) p <- p + geom_spatvector(data = aoi, color = aoi_stroke$color, fill = NA, linetype = "solid", linewidth = aoi_stroke$linewidth)
  if (plot_wards) {
    p <- p + geom_spatvector(data = wards, color = aoi_stroke$color, fill = NA, linetype = "solid", linewidth = .25)
    if (exists("ward_labels")) p <- p +
      geom_spatvector_text(data = ward_labels, aes(label = WARD_NO), size = 2, fontface = "bold")
  }
  p <- p + coord_3857_bounds(static_map_bounds)
  return(p)
}

type_data <- function(data) {
  data_class <- class(data)[1]
  if (data_class %ni% c("SpatVector", "SpatRaster")) {
    stop(glue("On {yaml_key} data is neither SpatVector or SpatRaster, but {data_class}"))
  }
  data_type <- if (data_class == "SpatRaster") "raster" else geomtype(data)
  if (data_type %ni% c("raster", "points", "lines", "polygons")) {
    stop(glue("On {yaml_key} data is not of type 'raster', 'points', 'lines', or 'polygons'"))
  }
  return(data_type)
}

create_geom <- function(data, params) {
  data_type <- type_data(data)
  layer_values <- get_layer_values(data)
  if (data_type == "points") {
    geom_spatvector(data = data, aes(color = layer_values), size = params$size %||% 1)
  } else if (data_type == "polygons") {
    geom_spatvector(data = data, aes(fill = layer_values), color = params$stroke)
  } else if (data_type == "lines") {
    stroke_variable <- if (length(params$stroke) > 1) params$stroke$variable else NULL
    weight_variable <- if (length(params$weight) > 1) params$weight$variable else NULL
    # I could use aes_list in a safer way
    # aes_list2 <- c(
    #   aes(color = .data[[stroke_variable]]))
    #   aes(linewidth = (.data[[weight_variable]])))
    aes_list <- aes(color = .data[[stroke_variable]], linewidth = (.data[[weight_variable]]))
    if (is.null(weight_variable)) aes_list <- aes_list[-2]
    if (is.null(stroke_variable)) aes_list <- aes_list[-1]
    geom_spatvector(data = data, aes_list)
  } else if (data_type == "raster") {
    geom_spatraster(data = data, maxcell = 5e6) #, show.legend = T)
  }
}

fill_scale <- function(data_type, params) {
  # data_type <- if (data_type %ni% c("raster", "points", "lines", "polygons")) type_data(data_type))
  if (length(params$palette) == 0 | data_type %in% c("points", "line")) {
    NULL 
  } else if (exists_and_true(params$factor)) {
    # Switched to na.translate = F because na.value = "transparent" includes
    # NA in legend for forest. Haven't tried with non-raster.
    scale_fill_manual(
      values = params$palette,
      name = format_title(params$title, params$subtitle),
      na.translate = F,
      na.value = "transparent")
  } else if (params$bins == 0) {
    scale_fill_gradientn(
      colors = params$palette,
      limits = if (is.null(params$domain)) NULL else params$domain,
      rescaler = if (!is.null(params$center)) ~ scales::rescale_mid(.x, mid = params$center) else scales::rescale,
      na.value = "transparent",
      name = format_title(params$title, params$subtitle))
  } else if (params$bins > 0) {
    scale_fill_stepsn(
      colors = params$palette,
      # Length of labels is one less than breaks when we want a discrete legend
      breaks = if (is.null(params$breaks)) waiver() else if (diff(lengths(list(params$labels, params$breaks))) == 1) params$breaks[-1] else params$breaks,
      # breaks_midpoints() is important for getting the legend colors to match the specified colors
      values = if (is.null(params$breaks)) NULL else breaks_midpoints(params$breaks, rescaler = if (!is.null(params$center)) scales::rescale_mid else scales::rescale, mid = params$center),
      labels = if (is.null(params$labels)) waiver() else params$labels,
      limits = if (is.null(params$breaks)) NULL else range(params$breaks),
      rescaler = if (!is.null(params$center)) scales::rescale_mid else scales::rescale,
      na.value = "transparent",
      oob = scales::oob_squish,
      name = format_title(params$title, params$subtitle),
      guide = if (diff(lengths(list(params$labels, params$breaks))) == 1) "legend" else "colorsteps")
  }
}

color_scale <- function(data_type, params) {
  if (data_type == "points") {
    scale_color_manual(values = params$palette, name = format_title(params$title, params$subtitle))
  } else if (length(params$stroke) < 2 || is.null(params$stroke$palette)) {
    NULL
  } else {
    scale_color_stepsn(
      colors = params$stroke$palette,
            # Length of labels is one less than breaks when we want a discrete legend
            breaks = if (is.null(params$stroke$breaks)) waiver() else if (diff(lengths(list(params$stroke$labels, params$stroke$breaks))) == 1) params$stroke$breaks[-1] else params$stroke$breaks,
            # breaks_midpoints() is important for getting the legend colors to match the specified colors
            values = if (is.null(params$stroke$breaks)) NULL else breaks_midpoints(params$stroke$breaks, rescaler = if (!is.null(params$stroke$center)) scales::rescale_mid else scales::rescale, mid = params$stroke$center),
            labels = if (is.null(params$stroke$labels)) waiver() else params$stroke$labels,
            limits = if (is.null(params$stroke$breaks)) NULL else range(params$stroke$breaks),
            rescaler = if (!is.null(params$stroke$center)) scales::rescale_mid else scales::rescale,
            na.value = "transparent",
            oob = scales::oob_squish,
      name = format_title(params$stroke$title, params$stroke$subtitle))
  }
}

linewidth_scale <- function(data_type, params) {
  if (length(params$weight) < 2 || is.null(params$weight$range)) {
    NULL
  } else if (params$weight$factor) {
    scale_linewidth_manual(
      name = format_title(params$weight$title, params$weight$subtitle),
      values = unlist(setNames(params$weight$palette, params$weight$labels)))
  } else {
    scale_linewidth(
      range = c(params$weight$range[[1]], params$weight$range[[2]]),
      name = format_title(params$weight$title, params$weight$subtitle))
  }
}

theme_legend <- function(data, params) {
  layer_values <- get_layer_values(data)
  is_legend_text <- function() {
    !is.null(params$labels) && is.character(params$labels) | is.character(layer_values)
  }
  legend_text_alignment <- if (is_legend_text()) 0 else 1

  legend_theme <- theme(
    legend.title = ggtext::element_markdown(),
    legend.text = element_text(hjust = legend_text_alignment))
  return(legend_theme)
}

theme_custom <- function(...) {
  theme(
  # legend.key = element_rect(fill = "#FAFAF8"),
  legend.justification = c("left", "bottom"),
  legend.box.margin = margin(0, 0, 0, 12, unit = "pt"),
  legend.margin = margin(4,0,4,0, unit = "pt"),
  axis.title = element_blank(),
  axis.text = element_blank(),
  axis.ticks = element_blank(),
  axis.ticks.length = unit(0, "pt"),
  plot.margin = margin(0,0,0,0),
  ...)
}

coord_3857_bounds <- function(extent, expansion = 1, ...) {
  if (!inherits(extent, "SpatExtent")) {
    if (inherits(extent, "SpatVector")) extent <- ext(project(extent, "epsg:3857"))
    if (inherits(extent, "sfc")) extent <- ext(vect(st_transform(extent, crs = "epsg:3857")))
    extent <- ext(extent)
  }
  coord_sf(
    crs = "epsg:3857",
    expand = F,
    xlim = extent[1:2] %>% { (. - mean(.)) * expansion + mean(.)},
    ylim = extent[3:4] %>% { (. - mean(.)) * expansion + mean(.)},
    ...)
}

get_zoom_level <- \(bounds, cap = 6) {
  # cap & max() is a placeholder. The formula was developed for smaller cities, but calculates 7 for Guiyang which is far too coarse
  zoom <- round(14.6 + -0.00015 * sqrt(expanse(project(bounds, "epsg:4326"))/3))
  if (is.na(cap)) return(zoom)
  max(zoom, cap)
}

save_plot <- function(
    plot = NULL, filename, directory,
    map_height = map_height, map_width = map_width, dpi = 300,
    rel_widths = c(3, 1)) {
  # Saves plots with set legend widths
  plot_layout <- plot_grid(
    plot + theme(legend.position = "none"),
    # Before ggplot2 3.5 was get_legend(plot); still works but with warning;
    # there are now multiple guide-boxes
    get_plot_component(plot, "guide-box-right"),
    rel_widths = rel_widths,
    nrow = 1) +
    theme(plot.background = element_rect(fill = "white", colour = NA))
  cowplot::save_plot(
    plot = plot_layout,
    filename = file.path(directory, filename),
    dpi = dpi,
    base_height = map_height, base_width = sum(rel_widths)/rel_widths[1] * map_width)
}

get_layer_values <- function(data) {
  if (class(data)[1] %in% c("SpatRaster")) {
      values <- values(data)
      # if (!is.null(levels(data))) values <- factor(values, levels = levels(data)[[1]]$value, labels = levels(data)[[1]]$label)
    } else if (class(data)[1] %in% c("SpatVector")) {
      values <- pull(values(data))
    } else if (class(data)[1] == "sf") {
      values <- data$values
    } else stop("Data is not of class SpatRaster, SpatVector or sf")
  return(values)
}

set_layer_values <- function(data, values) {
  if (class(data)[1] %in% c("SpatRaster")) {
      values(data) <- values
    } else if (class(data)[1] %in% c("SpatVector")) {
      values(data)[[1]] <- values
    } else if (class(data)[1] == "sf") {
      data$values <- values
    } else stop("Data is not of class SpatRaster, SpatVector or sf")
  return(data)
}

set_domain <- function(values, domain = NULL, center = NULL, factor = NULL) {
  if (!is.null(factor) && factor) {
    # Necessary for keeping levels in order
    domain <- ordered(levels(values), levels = levels(values))
  }
  if (is.null(domain)) {
    # This is a very basic way to set domain. Look at toolbox for more robust layer-specific methods
    min <- min(values, na.rm = T)
    max <- max(values, na.rm = T)
    domain <- c(min, max)
  }
  if (!is.null(center) && center == 0) {
    extreme <- max(abs(domain))
    domain <- c(-extreme, extreme)
  }
  return(domain)
}

create_color_scale <- function(domain, palette, center = NULL, bins = 5, reverse = F, breaks = NULL, factor = NULL, levels = NULL) {
  # List of shared arguments
  args <- list(
    palette = palette,
    domain = domain,
    na.color = 'transparent',
    alpha = T)
  # if (!is.null(breaks)) bins <- length(breaks)
  if (!is.null(factor) && factor) {
      color_scale <- rlang::inject(colorFactor(
        !!!args,
        levels = levels,
        ordered = TRUE))
  } else if (bins == 0) {
    color_scale <- rlang::inject(colorNumeric(
      # Why did I find it necessary to use colorRamp previously? For setting "linear"?
      # palette = colorRamp(palette, interpolate = "linear"),
      !!!args,
      reverse = reverse)) 
  } else {
    color_scale <- rlang::inject(colorBin(
      !!!args,
      bins = if (!is.null(breaks)) breaks else bins,
      # Might want to turn pretty back on
      pretty = FALSE,
      reverse = reverse))       
  }
  return(color_scale)
}

label_maker <- function(x, levels = NULL, labels = NULL, suffix = NULL) {
  # if (!is.null(labels)) {
  #   index <- sapply(x, \(.x) which(levels == .x)) # Using R's new lambda functions!
  #   x <- labels[index]
  # }
  if (is.numeric(x)) {
    x <- signif(x, 6)
  }
  if (!is.null(suffix)) {
    x <- paste0(x, suffix)
  }
  return(x)
  }

add_aoi <- function(map, data = aoi, color = 'black', weight = 2, fill = F, dashArray = '12', ...) {
  addPolygons(map, data = data, color = color, weight = weight, fill = fill, dashArray = dashArray, ...)
}

# Making the static map, given the dynamic map
mapshot_styled <- function(map_dynamic, file_suffix, return) {
  mapview::mapshot(map_dynamic,
          remove_controls = c('zoomControl'),
          file = paste0(styled_maps_dir, city_string, '-', file_suffix, '.png'),
          vheight = vheight, vwidth = vwidth, useragent = useragent)
  # return(map_static)
}

breaks_midpoints <- \(breaks, rescaler = scales::rescale, ...) {
  scaled_breaks <- rescaler(breaks, ...)
  midpoints <- head(scaled_breaks, -1) + diff(scaled_breaks)/2
  midpoints[length(midpoints)] <- midpoints[length(midpoints)] + .Machine$double.eps
  return(midpoints)
}

# Text Functions ---------------------------------------------------------------
read_md <- function(file) {
  md <- readLines(file)
  instruction_lines <- 1:grep("CITY CONTENT BEGINS HERE", md)
  mddf <- tibble(text = md[-instruction_lines]) %>%
    mutate(
      section = case_when(str_detect(text, "^//// ") ~ str_extract(text, "^/+ (.*)$", group = T), T ~ NA_character_),
      slide = case_when(str_detect(text, "^// ") ~ str_extract(text, "^/+ (.*)$", group = T), T ~ NA_character_),
      .before = 1) %>%
    tidyr::fill(section) %>% 
    { lapply(na.omit(unique(.$section)), \(sect, df) {
        df <- filter(df, section == sect) %>%
          tidyr::fill(slide, .direction = "down") %>%
          filter(!(slide != lead(slide) & text == "")) %>%
          filter(!str_detect(text, "^/") & !str_detect(text, "^----"))
        while (df$text[1] == "" & nrow(df) > 1) df <- df[-1,]
        while (tail(df$text, 1) == "" & nrow(df) > 1) df <- head(df, -1)
        return(df)
    }, df = .) } %>%
    bind_rows() #%>%
    # Do I want to remove header lines? For now, no
    # filter(!str_detect(text, "^#"))

  # Remove empty lines
  no_slide <- filter(mddf, is.na(slide))
  if (nrow(no_slide) > 0) {
    warning(paste0(
      "There are", nrow(no_slide), "lines with no slide name:\n\n",
      paste(knitr::kable(mutate(no_slide, .keep = "none", section, text = substr(text, 1, 25))), collapse = "\n")))
    mddf <- filter(mddf, !is.na(slide))
  }
  text_list <- sapply(unique(mddf$section), function(sect) {
    section_df <- filter(mddf, section == sect)
    section_list <- sapply(c(unique(section_df$slide)), function(s) {
      if (s == "empty") return (NULL)
      slide_text <- filter(section_df, slide == s)$text
      # if (str_detect(slide_text[1], "^\\s*$")) {
      #   slide_text <- slide_text[-1]
      # }
      # return(list(takeaways = slide_text))
      return(list(takeaways = slide_text))
    }, simplify = F)
    return(section_list)
  }, simplify = F)
  return(text_list)
}

double_space <- function(x) {
  str_replace(x, "\\n", "\n\n")
}

# merge_text_lists <- function(...) {
#   lists <- c(...)
#   keys <- unique(names(lists))
#   merged <- sapply(keys, function(k) {
#     index <- names(lists) == k
#     new_list <- c(unlist(lists[index], F, T))
#     names(new_list) <- str_extract(names(new_list), "([^\\.]+)$", group = T)
#     unique(names(new_list)) %>%
#       sapply(function (j) {
#         index2 <- names(new_list) == j
#         new_list2 <- c(unlist(new_list[index2], F, T))
#         names(new_list2) <- str_extract(names(new_list2), "([^\\.]+)$", group = T)
#         return(new_list2)
#       }, simplify = F)
#     return(new_list)
#   }, simplify = F)
#   return(merged)
# }

merge_lists <- \(x, y) {
  if (is.null(names(x)) | is.null(names(y))) return(unique(c(x, y)))
  nameless <- c(x[names(x) == ""], y[names(y) == ""])
  nameless <- nameless[!(nameless %in% c(names(x), names(y)))]
  unique_nodes_x <- x[setdiff(names(x), names(y))]
  unique_nodes_y <- y[setdiff(names(y), names(x))]
  common_keys <- intersect(names(x), names(y)) %>% .[. != ""]
  common_nodes <- if (length(common_keys) == 0) NULL else {
    sapply(common_keys, \(k) merge_lists(x[[k]], y[[k]]), simplify = F)
  }
  merged <- unlist(list(common_nodes, unique_nodes_x, unique_nodes_y, nameless), recursive = F)
  return(merged)
}

print_md <- function(x, div_class = NULL) {
  if (!is.null(div_class)) cat(":::", div_class, "\n")
  cat(x, sep = "\n")
  if (!is.null(div_class)) cat(":::\n")
}

print_slide_text <- function(slide) {
  if (!is.null(slide$takeaways)) {
    print_md(slide$takeaways, div_class = "takeaways")
    cat("\n")
  }
  if (!is.null(slide$method)) {
    print_md(slide$method, div_class = "method")
    cat("\n")
  }
  print_md(slide$footnote %||% "", div_class = "footnote")
}

fill_slide_content <- function(layer, extra_layers = NULL, title = NULL, slide_text = NULL) {
  if (!is.null(plots_html[[layer]])) {
    mapping_layers <- paste(
      map(c(extra_layers, layer), \(lay) layer_params[[lay]]$group_id),
      collapse = ";")
    if (is.null(slide_text)) slide_text <- slide_texts[[layer]]
    if (is.null(title)) title <- slide_text$title
    if (is.null(title)) title <- layer
    cat(glue("### {title}"))
    cat("\n")
    cat(glue('<div class="map-list" data-layers="{mapping_layers}"></div>'))
    cat("\n")
    # tryCatch(
    #   include_html_chart(fuzzy_read(file.path(output_dir, "plots/html"), slide_text$plot, paste)),
    #   error = \(e) return(""))
    plot_file <- fuzzy_read(charts_dir, slide_text$plot %||% "NO PLOT TO SEARCH FOR", paste)
    if (!is.na(plot_file)) cat(glue('<img style="max-width:95%" src="{plot_file}">\n\n\n'))
    print_slide_text(slide_text)
  }
}

fill_slide_content_pdf <- function(layer, map_name = NULL, title = NULL, slide_text = NULL) {
  if (is.null(map_name)) map_name <- layer
  map_file <- file.path(styled_maps_dir, paste0(map_name, ".png"))
  if (file.exists(map_file)) {
    if (is.null(slide_text)) slide_text <- slide_texts[[layer]]
    if (is.null(title)) title <- slide_text$title
    if (is.null(title)) title <- layer
    cat(glue("### {title}"))
    cat("\n")
    # cat(glue('<div class="map-list" data-static-map="{layer}"></div>'))
    cat(glue('<p class="map"><img src="{map_file}"></p>'))
    cat("\n")
    # tryCatch(
    #   include_html_chart(fuzzy_read(file.path(output_dir, "plots/html"), slide_text$plot, paste)),
    #   error = \(e) return(""))
    # print_slide_text(slide_text)

    cat('<div class="takeaways-method">\n')
    plot_file <- fuzzy_read(charts_dir, slide_text$plot %||% "NO PLOT TO SEARCH FOR", paste)
    if (!is.na(plot_file)) cat(glue('<p class="side-chart"><img src="{plot_file}"></p>'))
    cat("\n")
    if (!is.null(slide_text$takeaways)) {
    print_md(slide_text$takeaways, div_class = "takeaways")
    cat("\n")
  }
  if (!is.null(slide_text$method)) {
    print_md(slide_text$method, div_class = "method")
    cat("\n")
  }
    cat('</div>\n')
    print_md(slide_text$footnote %||% "", div_class = "footnote")
  # if (!is.null(slide$footnote)) print_md(slide$footnote %||% "", div_class = "footnote")
  }
}

aspect_buffer <- function(x, aspect_ratio, buffer_percent = 0, to_crs = "epsg:3857", keep_crs = T) {
  if (!inherits(x, "SpatVector")) {
    if (inherits(x, "sfc")) x <- vect(x) else stop("Input must be a terra SpatVector object")
  }
  
  from_crs <- crs(x)
  x <- project(x, y = to_crs)
  bounds_proj <- ext(x)
  center_coords <- crds(centroids(vect(bounds_proj)))
  corners <- vect(matrix(
    c(bounds_proj$xmin, bounds_proj$ymin,  # bottom left
      bounds_proj$xmax, bounds_proj$ymin,  # bottom right
      bounds_proj$xmin, bounds_proj$ymax,  # top left
      bounds_proj$xmax, bounds_proj$ymax), # top right
    ncol = 2, byrow = TRUE), crs = to_crs)

  distance_matrix <- as.matrix(distance(corners))
  x_distance <- max(distance_matrix[1,2], distance_matrix[3,4])
  y_distance <- max(distance_matrix[1,3], distance_matrix[2,4])

  if (x_distance/y_distance < aspect_ratio) x_distance <- y_distance * aspect_ratio
  if (x_distance/y_distance > aspect_ratio) y_distance <- x_distance/aspect_ratio

  new_bounds <- terra::ext(
    x = center_coords[1] + c(-1, 1) * x_distance/2 * (1 + buffer_percent),
    y = center_coords[2] + c(-1, 1) * y_distance/2 * (1 + buffer_percent))
  new_bounds <- vect(new_bounds, crs = to_crs)
  if (!keep_crs) return(new_bounds)
  project(new_bounds, y = from_crs)
}

# Alternatively could be two separate functions: pretty_interval() and pretty_quantile()
break_pretty2 <- function(data, n = 6, method = "quantile", FUN = signif, 
                          digits = NULL, threshold = 1/(n-1)/4) {
  divisions <- seq(from = 0, to = 1, length.out = n)

  if (method == "quantile") breaks <- unname(stats::quantile(data, divisions, na.rm = T))
  if (method == "interval") breaks <- divisions *
    (max(data, na.rm = T) - min(data, na.rm = T)) +
    min(data, na.rm = T)

  if (is.null(digits)) {
    digits <- if (all.equal(FUN, signif)) 1 else if (all.equal(FUN, round)) 0
  }

  distribution <- ecdf(data)
  discrepancies <- 100
  while (any(abs(discrepancies) > threshold) & digits < 6) {
    if (all.equal(FUN, signif) == TRUE) {
      pretty_breaks <- FUN(breaks, digits = digits)
      if(all(is.na(str_extract(tail(pretty_breaks, -1), "\\.[^0]*$")))) pretty_breaks[1] <- floor(pretty_breaks[1])
    }
    if (all.equal(FUN, round) == TRUE) {
      pretty_breaks <- c(
        floor(breaks[1] * 10^digits) / 10^digits,
        FUN(tail(head(breaks, -1), -1), digits = digits),
        ceiling(tail(breaks, 1) * 10^digits) / 10^digits)
    }
    if (method == "quantile") discrepancies <- distribution(pretty_breaks) - divisions
    # if (method == "interval) discrepancies <- distribution(pretty_breaks) - distribution(breaks)
    if (method == "interval") {
      discrepancies <- (pretty_breaks - breaks)/ifelse(breaks != 0, breaks, pretty_breaks)
      discrepancies[breaks == 0 & pretty_breaks == 0] <- 0
    }
    digits <- digits + 1
  }
  return(pretty_breaks)
}

include_html_chart <- \(file) cat(str_replace_all(readLines(file), "\\s+", " "), sep="\n")

break_lines <- function(x, width = 20, newline = "<br>") {
  str_replace_all(x, paste0("(.{", width, "}[^\\s]*)\\s"), paste0("\\1", newline))
}

format_title <- function(title, subtitle, width = 20) {
  title_broken <- paste0(break_lines(title, width = width, newline = "<br>"), "<br>")
  if (is.null(subtitle)) return(title_broken)
  subtitle_broken <- break_lines(subtitle, width = width, newline = "<br>")
  formatted_title <- paste0(title_broken, "<br><em>", subtitle_broken, "</em><br>")
  return(formatted_title)
}

count_aoi_cells <- function(data, aoi) {
  aoi_area <- if ("sf" %in% class(aoi)) {
    units::drop_units(sum(st_area(aoi)))
  } else if ("SpatVector" %in% class(aoi)) {
    sum(expanse(aoi)) # sum to account for multiple geometries
  }
  cell_count <- (aoi_area / cellSize(data)[1,1])[[1]]
  return(cell_count)
}

vectorize_if_coarse <- function(data, threshold = 7000) {
  if (class(data)[1] %in% c("sf", "SpatVector")) return(data)
  cell_count <- count_aoi_cells(data, aoi)
  if (cell_count < threshold) data <- rast_as_vect(data)
  return(data)
}

aggregate_if_too_fine <- function(data, threshold = 1e5, fun = "modal") {
  if (class(data)[1] %in% c("sf", "SpatVector")) return(data)
  cell_count <- count_aoi_cells(data, aoi)
  if (cell_count > threshold) {
    factor <- round(sqrt(cell_count / threshold))
    if (factor > 1) data <- terra::aggregate(data, fact = factor, fun = fun)
  }
  return(data)
}

center_max_circle <- \(x, simplify = T, tolerance = 0.0001) {
  if (simplify) s <- simplifyGeom(x, tolerance = tolerance) else s <- x
  p <- as.points(s)
  v <- voronoi(p)
  vp <- as.points(v)
  vp <- vp[is.related(vp, s, "within")]
  # Using vp[which.max(nearest(vp, p)$distance)] is 60x slower
  vppd <- distance(vp, p)

  center <- vp[which.max(apply(vppd, 1, min))]
  radius <- vppd[which.max(apply(vppd, 1, min))]
  return(list(center = center, radius = radius))
}

site_labels <- function(x, simplify = T, tolerance = 0.0001) {
  sites <- list()
  for (i in 1:nrow(x)) {
    sites[i] <- center_max_circle(x[i], simplify = simplify, tolerance = tolerance)["center"]
  }
  label_sites <- Reduce(rbind, unlist(sites))
  return(label_sites)
}

`%ni%` <- Negate(`%in%`)

which_not <- function(v1, v2, swap = F, both = F) {
  if (both) {
    list(
      "In V1, not in V2" = v1[v1 %ni% v2],
      "In V2, not in V1" = v2[v2 %ni% v1]
    )
  } else
  if (swap) {
    v2[v2 %ni% v1]
  } else {
    v1[v1 %ni% v2]
  }
}

paste_and <- function(v) {
    if (length(v) == 1) {
    string <- paste(v)
  } else {
    # l[1:(length(l)-1)] %>% paste(collapse = ", ")
    paste(head(v, -1), collapse = ", ") %>%
    paste("and", tail(v, 1))
  }
}

duplicated2way <- duplicated_all <- function(x) {
  duplicated(x) | duplicated(x, fromLast = T)
}

tolatin <- function(x) stringi::stri_trans_general(x, id = "Latin-ASCII")

ggdonut <- function(data, category_column, quantities_column, colors, title) {
  data <- as.data.frame(data) # tibble does weird things with data frame, not fixing now
  data <- data[!is.na(data[,quantities_column]),]
  data <- data[data[,quantities_column] > 0,]
  # data <- data[rev(order(data[,quantities_column])),]
  data$decimal <- data[,quantities_column]/sum(data[,quantities_column], na.rm = T)
  data$max <- cumsum(data$decimal) 
  data$min <- lag(data$max)
  data$min[1] <- 0
  data$label <- paste(scales::label_percent(0.1)(data$decimal))
  data$label[data$decimal < .02] <- "" 
  data$label_position <- (data$max + data$min) / 2
  data[,category_column] <- factor(data[,category_column], levels = data[,category_column])
  breaks <- data[data[,"decimal"] > 0.2,] %>%
    { setNames(.$label_position, .[,category_column]) }

  donut_plot <- ggplot(data) +
    geom_rect(
      aes(xmin = .data[["min"]], xmax = .data[["max"]], fill = .data[[category_column]],
      ymin = 0, ymax = 1),
      color = "white") +
    geom_text(y = 0.5, aes(x = label_position, label = label)) +
    # theme_void() +
    # scale_x_continuous(guide = "none", name = NULL) +
    scale_y_continuous(guide = "none", name = NULL) +
    scale_fill_manual(values = colors) +
    scale_x_continuous(breaks = breaks, name = NULL) +
    coord_radial(expand = F, inner.radius = 0.3) +
    guides(theta = guide_axis_theta(angle = 0)) +
    labs(title = paste(city, title)) +
    theme(axis.ticks = element_blank())
  return(donut_plot)
}

Mode <- \(x, na.rm = F) {
  if (na.rm) x <- na.omit(x)
  unique_values <- unique(x)
  unique_values[which.max(tabulate(match(x, unique_values)))]
}

prepare_html <- \(in_file, out_file, css_file) {
  library(rvest)
  library(xml2)
  pdf <- read_html(in_file)
  stylesheet_nodes <- html_elements(pdf, "link[rel=stylesheet]")
  xml_attr(stylesheet_nodes[1], "href") <- css_file
  xml2::xml_remove(stylesheet_nodes[-1])
  setup_node <- html_elements(pdf, ".setup")
  xml2::xml_remove(setup_node)
  # Do I want to remove all div.cell? NO
  # xml2::xml_remove(html_nodes(pdf, ".cell"))
  ojs_script_node <- html_element(pdf, "script[src='index_files/libs/quarto-ojs/quarto-ojs-runtime.js']")
  xml2::xml_remove(ojs_script_node)
  module_nodes <- html_elements(pdf, "script[type=module]")
  xml2::xml_remove(module_nodes)
  ojs_module_node <- html_element(pdf, "script[type=ojs-module-contents]")
  xml2::xml_remove(ojs_module_node)
  js_nodes <- html_elements(pdf, "script[type='text/javascript']")
  xml2::xml_remove(js_nodes)
  json_node <- html_elements(pdf, "script[type='application/json']")
  xml2::xml_remove(json_node)
  nav_node <- html_element(pdf, ".navigation")
  xml2::xml_remove(nav_node)
  xml2::xml_remove(html_nodes(pdf, "script#quarto-html-after-body"))
  write_html(pdf, out_file)
}

rotate_ccw <- \(x) t(x)[ncol(x):1,]

density_rast <- \(points, n = 100, aoi = NULL) {
  crs <- crs(points)
  data_extent <- ext(points)
  if (!is.null(aoi)) {
    data_extent <- terra::union(data_extent, ext(project(aoi, crs)))
  }
  density_extent <- ext(aspect_buffer(vect(data_extent, crs = crs), aspect_ratio = aspect_ratio))
  points_df <- as_tibble(mutate(points, x = geom(points, df = T)$x, y = geom(points, df = T)$y))
  density <-  MASS::kde2d(points_df$x, points_df$y, n = n, lims = as.vector(density_extent))
  dimnames(density$z) <- list(x = density$x, y = density$y)
  # Rotate density, because top left is lowest x and lowest y, instead of lowest x and highest y
  density$z <- rotate_ccw(density$z)
  rast(scales::rescale((density$z)), crs = crs, extent = density_extent)
}

tryCatch_named <- \(name, expr) {
  tryCatch(expr, error = \(e) {
    message(paste("Failure:", name))
    warning(glue("Error on {name}: {e}"))
  })
}

grow_extent <- \(x, amount) {
  # Given a SpatExtent object, grow (or shrink) it by a given multiplier
  # amount can be length 1 (applied to all sides), 2 (applied to x and y) or 4 (applied to each side)
  stopifnot(inherits(x, "SpatExtent"))
  stopifnot(length(amount) %in% c(1, 2, 4))
  if (length(amount) == 1) amount <- rep(amount, 4)
  if (length(amount) == 2) amount <- c(rep(amount[1], 2), rep(amount[2], 2))
  growth <- amount * c(rep(diff(x[1:2]), 2), rep(diff(x[3:4]), 2))
  x + growth
}

change_zoom <- function(p, zoom) {
  # Update, not the best method (better to use ggproto) but we have a way for 
  # separating q from p!
  
  # This is a bad solution because it changes the zoom level of all plots. 
  # p <- change_zoom(plot) changes the zoom on both plot (output) and p (input).
  # Need to learn how to either 1) create a distinct copy (neither ggplot_build
  # nor rlang::duplicate seem to do this), or 2) create a ggproto (?) that can
  # be used with `+`

  q <- unserialize(serialize(p, NULL))

  # p_copy <- ggplot2::ggplot_build(p)$plot
  tile_layer_index <- detect_index(p$layers, \(x) inherits(x$geom, "GeomMapTile"))
  q$layers[[tile_layer_index]]$mapping$zoom <- zoom
  q
}

zoom_on_extent <- function(p, extent_vect, aspect_ratio, buffer_percent = 0.05, zoom_adj = 0) {
  bounds <- aspect_buffer(extent_vect, aspect_ratio, buffer_percent = buffer_percent)
  (p + theme(legend.position = "none") +
    coord_3857_bounds(bounds)) %>%
    change_zoom(get_zoom_level(bounds) + zoom_adj)
}
