eq_file <- "mnt/multi-scan-materials/earthquake-archive.csv"
if (!file.exists(eq_file)) {
get_earthquake_data <- function() {
  # Previously, in httr, used set_cookies(`csrftoken` = "CJOWAoXjdFb7fL1Xf3asS9mj6GVJmbvvIKj365nRxupF27lO5UfkZECjtZoHLuuD")
  library(httr2)
  resps <- request("http://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes") %>%
    req_url_query(minYear = 1900, maxYear = lubridate::year(Sys.Date())) %>%
    req_perform_iterative(iterate_with_offset("page"))
  eq <- resps %>%
    resps_successes() %>%
    resps_data(\(resp) bind_rows(resp_body_json(resp)$items)) %>%
    bind_rows()
    return(eq)
}
write_csv(eq, eq_file)
} else eq <- read_csv(eq_file)

damages <- c("0" = "None",
             "1" = "Limited",
             "2" = "Moderate",
             "3" = "Severe",
             "4" = "Extreme")

if (!exists("eq")) eq <- get_earthquake_data()

y_ratio <- 51498 / 13514
# 3.324 

city_point <- aoi %>% st_as_sf %>% st_combine() %>% st_centroid()

eq_near <- eq %>%
  subset(!is.na(latitude)) %>%
  st_as_sf(coords = c("longitude", "latitude"), crs = st_crs(city_point)) %>%
  mutate(distance = st_distance(geometry, city_point) %>% units::set_units(km),
         magXdist = eqMagnitude * (2000 - units::drop_units(distance))) %>%
  filter(
    (damageAmountOrder >= 2 | damageMillionsDollars >= 1 |
       deaths >= 10 | deathsAmountOrder >= 2 |
       eqMagnitude >= 7.5 |
       intensity >= 10 |
       !is.na(tsunamiEventId)) &
      distance < units::set_units(500, km))
eq_text <- eq_near %>%
  mutate(
    location = gsub("([\\s-][A-Z])([A-Z]*)", "\\1\\L\\2", locationName, perl = T) %>% 
      str_extract("[^:][\\s]+.*") %>% trimws(),
    fatalities = paste(scales::label_comma()(deaths), "fatalities"),
    fatalities = str_replace_all(fatalities,
                                 c("1 fatalities" = "1 fatality",
                                   "NA fatalities" = "")),
    damage = paste(damages[as.character(damageAmountOrder)], "damage"),
    day = replace_na(day, 1),
    BEGAN = as.Date(paste(year, month, day, sep='-'))) %>%
  arrange(BEGAN) %>%
  mutate(
    line1 = toupper(paste(lubridate::month(BEGAN, label = T, abbr = F), lubridate::year(BEGAN))),
    # line2 = paste0(ifelse(!is.na(location), paste0(location, " "), "") , "(", eqMagnitude, ")"),
    line2 = paste0(eqMagnitude, "-magnitude; ", scales::label_comma(accuracy= 1)(units::drop_units(distance)), " km away"),
    line3 = damage,
    line4 = fatalities,
    text = paste(line1, line2, line3, line4, sep = "; "),
    above_line = (2*(row_number() %% 2) - 1)*-1) %>%
  select(BEGAN, text, line1, line2, line3, line4, above_line, distance, eqMagnitude, magXdist, location) %>%
  mutate(node_x = BEGAN + y_ratio * 1460*above_line,
         node_y = above_line * (1460 * tanpi(1/6) + 466/2) * y_ratio )

# print_paged_df(select(st_drop_geometry(eq_text), text, location))

eq_plot <-
  ggplot(eq_text, aes(y = BEGAN, x = drop_units(distance))) +
  # geom_text(data = filter(eq_text, !is.na(eqMagnitude)), aes(size = eqMagnitude, label = eqMagnitude)) +
  geom_text_repel(
    data = \(x) slice_max(x, magXdist, n = 10), aes(label = text),
    size = 4, hjust = 0, direction = "y",
    xlim = c(515, 1000),
    segment.color = "grey46", segment.size = .25,
    segment.curvature = 1e-20, segment.square = T) +
  geom_point(data = \(x) filter(x, !is.na(eqMagnitude)), aes(size = eqMagnitude), shape = 1, color = "black") +
  geom_point(data = \(x) slice_max(x, magXdist, n = 10), aes(size = eqMagnitude), color = "grey46") +
  geom_point(data = \(x) filter(x, is.na(eqMagnitude)), shape = 1, color = "grey92") +
  scale_x_continuous(
    limits = c(0, 500),
    labels = \(x) paste(x, "km"),
    breaks = seq(0, 500, 100),
    expand = expansion(c(0, 0))) +
  scale_y_continuous(
    # limits = c(NA, as.Date("1900-01-01")),
    # expand = expansion(c(0, 0.05)),
    breaks = seq.Date(as.Date("1900-01-01"), Sys.Date(), by = "20 years"),
    minor_breaks = seq.Date(as.Date("1900-01-01"), as.Date("2030-01-01"), by = "5 years"),
    labels = seq(1900, 2025, by = 20),
    trans = c("date", "reverse")) +
  scale_size(range = c(1, 6)) + # max_size = 7,
  # scale_color_manual(values = c(" " = "grey"), guide = "none") +
  labs(
    x = paste("Distance from", city),
    y = "Year",
    size = "Magnitude",
    # color = "Magnitude unavailable"
    ) +
  theme_minimal() +
  coord_cartesian(clip = 'off') +
  theme(
    axis.line = element_line(linewidth = .5, color = "black"),
    axis.text = element_text(size = 12),
    axis.title = element_text(size = 12),
    legend.position = "right",
    legend.justification.right = "bottom",
    legend.direction = "horizontal",
    legend.box.margin = margin(0, 0, -37, 15),
    plot.margin = margin(5.5, 300, 5.5, 5.5, "pt"),
    plot.background = element_rect(fill = "white", color = NULL))
  ggsave(file.path(charts_dir, "earthquake-archive.png"), device = "png",
         width = 20, height = 5.833, units = "in", dpi = "print")
