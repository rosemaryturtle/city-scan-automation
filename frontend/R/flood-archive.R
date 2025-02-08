flood_archive_dir <- "mnt/multi-scan-materials/flood-archive"
if (!file.exists(file.path(flood_archive_dir, "FloodArchive_region.shp"))) {
  c("dbf", "prj", "shp", "shx") %>% lapply(function(suffix) {
    curl_download(
      url = paste0("https://floodobservatory.colorado.edu/temp/FloodArchive_region.", suffix),
      destfile = paste0(flood_archive_dir, "/FloodArchive_region.", suffix))
  })
}

flood_archive <- vect(flood_archive_file)
flood_archive <- makeValid(flood_archive)
flood_archive <- flood_archive[is.valid(flood_archive),]
aoi_flood <- project(aoi, crs(flood_archive))
intersections <- which(apply(relate(flood_archive, aoi_flood, "intersects"), 1, any))
flood_archive <- flood_archive[intersections,]

# print_text("Map of floods")
# ggplot(flood_archive) +
#   geom_sf(aes(fill = DEAD)) +
#   geom_sf(data = aoi)

floods <- as.data.frame(flood_archive) %>%
  select(BEGAN, ENDED, DEAD, DISPLACED, MAINCAUSE, SEVERITY)

# print_text("Tally of flood events")
# summarize(floods, count = n(), across(.cols = c(DEAD, DISPLACED), sum), .groups = "drop") %>% print_paged_df()
# print_text("Median flood event")
# floods %>% mutate(
#   duration = as.numeric(ENDED - BEGAN)) %>%
#   summarize(across(.cols = c(DEAD, DISPLACED, duration), median), .groups = "drop") %>% print_paged_df()

# print_text("Causes of flood events")
# count(floods, MAINCAUSE) %>% print_paged_df()

if (nrow(floods) > 0) {
  flood_text_all <- floods %>% mutate(
    severity = ordered(SEVERITY, levels = c(1, 1.5, 2), labels = c("Large event", "Very large event", "Extreme event")),
    duration = paste(ENDED - BEGAN, "days"),
    fatalities = paste(scales::label_comma()(DEAD), "fatalities"),
    displaced = paste(scales::label_comma()(DISPLACED), "displaced"),
    line1 = toupper(paste(lubridate::month(BEGAN, label = T, abbr = F), lubridate::year(BEGAN))),
    line2 = paste(severity, (MAINCAUSE), sep = ", "),
    line3 = paste(as.character(duration), fatalities, displaced, sep = ", "),
    text = paste0(line1, ": ", line2, "\n", line3),
    mag = normalize(DEAD) * normalize(DISPLACED) * SEVERITY,
    begin_day = lubridate::yday(BEGAN),
    end_day = lubridate::yday(ENDED),
    begin_month = lubridate::month(BEGAN),
    end_month = lubridate::month(ENDED),
    begin_year = lubridate::year(BEGAN) + begin_day/1000, # The /1000 helps keep labels in proper vertical order
    end_year = lubridate::year(ENDED))

  # flood_text_all2[which(order(flood_text_all2$mag, decreasing = TRUE) > 10),"text"] <- NA
  flood_text_all[which(rank(-flood_text_all$mag) > 10),"text"] <- NA
  # flood_text_all2[order(flood_text_all2$mag, decreasing = T)[1:10],"text"]

  month_labels <- cumsum(c("Jan" = 31, "Feb" = 28, "Mar"= 31, "Apr" = 30, "May" = 31, "Jun" = 30,
    "Jul" = 31, "Aug" = 31, "Sep"= 30, "Oct" = 31, "Nov" = 30, "Dec" = 31))

  flood_text_all %>%
    ggplot(aes(y = begin_year, x = begin_day)) +
    geom_text_repel(
      aes(label = text),
      hjust = 0, size = 4, lineheight = 0.9,
      min.segment.length = 0, force_pull = .25, box.padding = .5,
      xlim = c(370, 700), direction = "y",
      segment.color = "grey46", segment.size = .25,
      segment.curvature = 1e-20, segment.square = T) +
    geom_point(aes(size = DISPLACED, alpha = severity), color = "darkblue") +
    scale_x_continuous(
      limits = c(0, 366), expand = c(0, 0),
      breaks = month_labels - 15, minor_breaks = c(0, month_labels)) +
    scale_y_reverse(
      # expand = c(0,0),
      limits = c(2020, 1985),
      breaks = seq(1985, 2020, by = 5), minor_breaks = 1985:2022 - 0.5) +
    scale_alpha_discrete(range = c(0.3, 1)) +
    scale_size_continuous(
      range = c(3, 10),
      breaks = range(flood_text_all$DISPLACED),
      labels = scales::label_number(scale_cut = scales::cut_short_scale())) +
    labs(y = "Year", alpha = "Severity", size = "Displaced") +
    theme_minimal() +
    coord_cartesian(clip = 'off') +
    theme(
      axis.line = element_line(linewidth = .5, color = "black"),
      panel.grid.major = element_blank(),
      panel.grid.minor = element_line(linewidth = .5, color = "grey92"),
      axis.text = element_text(size = 12),
      axis.title.y = element_text(size = 12),
      axis.title.x = element_blank(),
      legend.position = "bottom",
      plot.margin = margin(5.5, 300, 5.5, 5.5, "pt"),
      plot.background = element_rect(fill = "white", color = NULL))
  ggsave(file.path(charts_dir, "flood-archive.png"), device = "png",
    width = 20, height = 5.833, units = "in", dpi = "print")
}
