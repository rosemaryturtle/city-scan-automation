# Plotting solar availability seasonality line chart
pv_path <- file.path(spatial_dir, "Bangladesh_GISdata_LTAy_YearlyMonthlyTotals_GlobalSolarAtlas-v2_AAIGRID/monthly")

files <- list.files(pv_path) %>% 
  subset(stringr::str_detect(., ".tif$|.asc$"))
if (length(files) == 0) stop("No PV files found")
monthly_pv <- lapply(files, function(f) {
  m <- f %>% substr(7, 8) %>% as.numeric()
  month_country <- terra::rast(file.path(pv_path, f))
  month <- terra::extract(month_country, aoi, include_area = T) %>% .[[2]]
  max <- max(month, na.rm = T)
  min <- min(month, na.rm = T)
  mean <- mean(month, na.rm = T)
  sum <- sum(month, na.rm = T)
  return(c(month = m, max = max, min = min, mean = mean, sum = sum))
}) %>% bind_rows()

pv_plot <- monthly_pv %>%
  mutate(daily = mean/lubridate::days_in_month(month)) %>%
  ggplot(aes(x = month, y = daily)) +
  annotate("text", x = 1, y = 4.6, label = "Excellent Conditions", vjust = 0, hjust = 0, color = "dark grey") +
  annotate("text", x = 1, y = 3.6, label = "Favorable Conditions", vjust = 0, hjust = 0, color = "dark grey") +
  geom_line() +
  geom_point() +
  scale_x_continuous(breaks = 1:12, labels = lubridate::month(1:12, label = T) %>% as.character) +
  scale_y_continuous(labels = scales::label_comma(), limits = c(0, NA), expand = expansion(mult = c(0,.05))) +
  labs(title = "Seasonal availability of solar energy",
       x = "Month", y = "Daily PV energy yield (kWh/kWp") +
  geom_hline(yintercept = c(3.5, 4.5), linetype = "dotted") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(), 
    axis.line = element_line(linewidth = .5, color = "black"),
    panel.grid.minor.x = element_blank(),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "monthly-pv.png"), plot = pv_plot, device = "png",
       width = 6, height = 4, units = "in", dpi = "print")
