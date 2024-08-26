# These come from https://raw.githubusercontent.com/compoundrisk/monitor/databricks/src/fns/helpers.R
# Would be better to make a package

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