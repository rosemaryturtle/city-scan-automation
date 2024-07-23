# rx5day ----

rx5day_paths <- unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "rx5day")))

rx5day_all_df <- file.path(
  "source-data/rx5day",
  str_extract(c(rx5day_paths), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

rx5day_observed <- rx5day_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
rx5day_projections <- rx5day_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)


# # Mean values, rather than extremes or change factors 

# ggplot(data = rx5day_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.25) +
#     geom_line(aes(y = median)) +
#     facet_grid(cols = vars(ssp)) + 
#     geom_line(data = rx5day_observed, aes(y = value), color = "#969696") +
#     # geom_vline(xintercept = as.Date("2015-07-01")) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
#       labels = seq(1950, 2100, by = 20)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#     y = "Precipitation over 5 days (mm)",
#     ) +
#     # annotate(x = )
#     theme_minimal() +
#     theme(axis.line = element_line(color = "black"))
# ggsave("plots/rx5day-cols.png", width = 9, height = 4)

# # Overlap, no observed
# ggplot(data = rx5day_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
#     geom_line(aes(y = median, color = ssp)) +
#     # geom_line(data = rx5day_observed, aes(y = value), color = "#969696") +
#     # geom_vline(xintercept = as.Date("2015-07-01")) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
#       labels = seq(1950, 2100, by = 10)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#     y = "Precipitation over 5 days (mm)",
#       fill = "Scenario", color = "Scenario"
#     ) +
#     # annotate(x = )
#     theme_minimal() +
#     theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"))
# ggsave("plots/rx5day-overlap-no-observed.png", width = 6, height = 4)

# # Overlap
# ggplot(data = rx5day_projections, aes(x = date)) +
#   geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
#   geom_line(aes(y = median, color = ssp)) +
#   geom_line(data = rx5day_observed, aes(y = value), color = "#969696") +
#   geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
#   scale_x_date(
#     breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
#     labels = seq(1950, 2100, by = 10)) +
#   scale_y_continuous(expand = c(0, NA)) +
#   labs(
#     x = "Year",
#     y = "Precipitation over 5 days (mm)",
#     fill = "Scenario", color = "Scenario"
#   ) +
#   annotate("text",
#     x = as.Date("2022-07-01"), y = .95*max(c(rx5day_observed$value, rx5day_projections$median), na.rm = T),
#     label = "← Observed",
#     hjust = 1) +
#   annotate("text",
#     x = as.Date("2024-07-01"), y = .95*max(c(rx5day_observed$value, rx5day_projections$median), na.rm = T),
#     label = "Projected →",
#     hjust = 0) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#   axis.line = element_line(color = "black"))
# ggsave("plots/rx5day-overlap.png", width = 6, height = 4)

# # rx5day alt ----

# rx5day_seasons_paths <- list.files(full.names = T, "source-data/rx5day") %>%
#   str_subset("season")

# rx5day_seasons_df <- rx5day_seasons_paths %>%
#   lapply(extract_ts) %>%
#   bind_rows() %>%
#   mutate(
#     ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
#     historical = str_detect(file, "historical"),
#     Likelihood = str_extract(file, "median|p10|p90"),
#     Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
#     month = lubridate::month(date), year = lubridate::year(date))

# # rx5day_alt <- "source-data/rx5day/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp126_timeseries-smooth_median_2015-2100.nc" %>%
# #   extract_ts() %>%
# #   mutate(month = lubridate::month(date), year = lubridate::year(date))

# rx5day_seasons_observed <- rx5day_seasons_df %>%
#   select(-file, -ssp) %>%
#   filter(historical) %>%
#   filter(date > "1980-01-01")
# rx5day_seasons_projections <- rx5day_seasons_df %>%
#   select(-file) %>%
#   filter(!historical) %>%
#   filter(date > "2023-01-01") %>%
#   tidyr::pivot_wider(names_from = Likelihood, values_from = value)

# # Faceted
# # Excluding SSP3-7.0 because I think there's an error; I emailed CCKP
# rx5day_seasons_df %>%
#   # filter(Likelihood == "median") %>% # p10 and p90 are same as median here
#   filter(ssp != "SSP3-7.0") %>%
#   ggplot(aes(x = date)) +
#   geom_point(aes(y = value, color = factor(month, labels = month.name[c(1,4,7,10)]))) +
#   # geom_path(aes(y = value), alpha = .25) +
#   # scale_x_continuous(
#     # breaks = c(1, 4, 7, 10), labels = month.abb[c(1,4,7,10)],
#     # limits = c(0, 12)) +
#   scale_y_continuous(limits = c(0, NA), expand = c(0, NA)) +
#   facet_wrap(vars(ssp), nrow = 3) + # , scales = "free_y") +
#   labs(
#     x = "Year",
#     y = "Precipitation over 5 days (mm)",
#     color = "Month"
#   ) +
#   theme_minimal() +
#   theme(
#     legend.position = "bottom",
#     axis.line = element_line(color = "black"))
# ggsave("plots/rx5day-seasonal-rows.png", width = 6, height = 4)

# # Overlap, as lines
# # Excluding SSP3-7.0 because I think there's an error; I emailed CCKP
# rx5day_seasons_df %>%
#   # filter(Likelihood == "median") %>% # p10 and p90 are same as median here
#   filter(ssp != "SSP3-7.0") %>%
#   ggplot(aes(x = date)) +
#   geom_line(aes(y = value, color = factor(month, labels = month.name[c(1,4,7,10)]), linetype = ssp)) +
#   # geom_path(aes(y = value), alpha = .25) +
#   # scale_x_continuous(
#     # breaks = c(1, 4, 7, 10), labels = month.abb[c(1,4,7,10)],
#     # limits = c(0, 12)) +
#   scale_y_continuous(limits = c(0, NA), expand = c(0, NA)) +
#   # facet_grid(rows = vars(ssp)) + # , scales = "free_y") +
#   labs(
#     x = "Year",
#     y = "Precipitation over 5 days (mm)",
#     color = "Month"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#   axis.line = element_line(color = "black"))
# ggsave("plots/rx5day-seasonal-overlap.png", width = 6, height = 4)

# # Radial
# rx5day_seasons_df %>%
#   filter(ssp != "SSP3-7.0") %>%
#   # .[1:2000,] %>%
#   mutate(plot_order = seq_along(date) * 3 - 2) %>%
#   ggplot(aes(x = plot_order, y = value, color = year)) +
#   geom_point() +
#   geom_path(alpha = .25) +
#   scale_x_continuous(
#     limits = c(0, 12),
#     oob = scales::oob_keep,
#     breaks = 1:12,
#     labels = month.abb) +
#     # breaks = seq.Date(from = as.Date("2015-01-16"), length.out = 4, by = "3 months"),
#     # labels = c("", month.abb[c(1,4,7,10)])) +
#   coord_radial(expand = F, inner.radius = .2) +
#   facet_grid(cols = vars(ssp)) +
#   guides(
#     theta = guide_axis_theta(angle = 0))
#   #   theta.sec = guide_axis_theta(theme = theme(axis.line.theta = element_line()))) +
#   # theme_minimal() +
#   # theme(
#   #   legend.position = "bottom",
#   #   panel.grid.minor.x = element_blank(),
#   #   axis.line.theta = element_line(color = "black"))
# ggsave("plots/rx5day-seasonal-radial-cols.png", width = 6, height = 4)

# test <- rast("source-data/rx5day/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp370_timeseries-smooth_median_2015-2100.nc")

# summary(values(test))

# test[[lubridate::month(time(test)) != 1]] %>% summary()

#####

changefactor <- list.files("source-data/rx5day-extremes", full.names = T) %>%
  str_subset("changefactor") %>%
  str_subset(paste0("ssp", scenario_numbers, collapse = "|")) %>%
  # .[1:2] %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = factor(str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3")),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|(?<=_)p10|(?<=_)p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
    period = str_extract(file, "\\d{4}-\\d{4}"),
    start = as.numeric(str_extract(period, "^\\d{4}")),
    end = as.numeric(str_extract(period, "\\d{4}$")),
    center = (end - start)/2 + start,
    base_return_period = as.numeric(str_extract(file, "\\d+(?=yr-)")),
    new_return_period = base_return_period * value)

# X as base return period, Y as new return period
ggplot(changefactor, aes(x = base_return_period, y = new_return_period, color = ssp)) +
  geom_line(aes(group = period), color = "black", alpha = 0.5) +
  geom_point(aes(shape = Likelihood)) +
  facet_grid(rows = vars(ssp)) +
  scale_x_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05))) +
  scale_y_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05)))

# In the future, want to draw arrows showing the path of each scenario, starting from base conditions
bind_rows(
  mutate(changefactor, adjusted_y = as.numeric(ssp)),
  tibble(
    base_return_period = c(5, 10, 20),
    new_return_period = c(5, 10, 20),
    ssp = "Observed (add year)",
    adjusted_y = 1)) %>%
ggplot(aes(y = adjusted_y, x = new_return_period, color = ssp)) +
geom_point() +
scale_y_continuous(limits = c(-1, 5)) +
facet_grid(rows = vars(base_return_period))

# Attempt at time contours, doesn't quite work
bind_rows(
  mutate(changefactor, adjusted_y = as.numeric(ssp)),
  tibble(
    base_return_period = c(5, 10, 20),
    new_return_period = c(5, 10, 20),
    ssp = "Observed (add year)",
    adjusted_y = 1)) %>%
ggplot(aes(y = -adjusted_y, x = new_return_period, color = ssp)) +
geom_point() +
# scale_y_continuous(limits = c(1, -5)) +
facet_grid(rows = vars(base_return_period)) +
ggnewscale::new_scale_color() +
geom_path(aes(group = period))

ggplot(changefactor, aes(x = factor(ssp), y = new_return_period, color = ssp)) +
  geom_point(aes(shape = Likelihood)) +
  facet_grid(cols = vars(factor(base_return_period))) +
  geom_text(aes(label = period))
  scale_x_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05))) +

  scale_y_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05)))

ggplot(changefactor, aes(x = center, y = base_return_period * value, color = ssp)) +
  geom_point() +
  geom_arro
  facet_grid(rows = vars(ssp)) +
  scale_x_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05))) +
  scale_y_continuous(limits = c(0, NA), expand = expansion(c(0, 0.05)))



ggplot(changefactor, aes(x = center, y = value, color = ssp)) +
  geom_line() +
  facet_grid(rows = vars(base_return_period))

ggplot(changefactor, aes(x = center, y = value, color = factor(base_return_period))) +
  geom_line() +
  geom_point() +
  geom_vline(xintercept = c(2010, 2035, 2039, 2060, 2070, 2089, 2099)) +
  facet_grid(rows = vars(ssp)) +
  scale_y_continuous(limits = c(1, NA), expand = c(0, 0.05), labels = \(x) paste0(x, "x")) +
  facet_wrap(vars(ssp), nrow = 3) + # , scales = "free_y") +
  labs(
    x = "Year",
    y = "Change in Annual Exceedance Probability",
    color = "Return Period in 1985–2014"
  ) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    axis.line = element_line(color = "black"),
    panel.border = element_rect(color = "black", fill = NA))
ggsave("plots/rx5day-extremes-line.png", width = 6, height = 4)

ggplot(changefactor, aes(x = center, y = value, color = factor(base_return_period))) +
  # geom_rect(aes(xmin = start, xmax = end, ymin = value - 0.01, ymax = value + 0.01)) +
  geom_linerange(aes(xmin = start, xmax = end, y = value)) +
  # geom_line() +
  # geom_point() +
  # geom_vline(xintercept = c(2010, 2035, 2039, 2060, 2070, 2089, 2099)) +
  scale_y_continuous(limits = c(1, NA), expand = c(0, 0.05), labels = \(x) paste0(x, "x")) +
  facet_grid(rows = vars(ssp)) +
  labs(
    x = "Year",
    y = "Change in Annual Exceedance Probability",
    color = "Return Period in 1985–2014"
  ) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    axis.line = element_line(color = "black"),
    panel.border = element_rect(color = "black", fill = NA))
ggsave("plots/rx5day-extremes-linerange.png", width = 6, height = 4)

changefactor %>%
  filter(start != "2070") %>%
ggplot(aes(x = center, y = value, color = factor(base_return_period))) +
  # geom_rect(aes(xmin = start, xmax = end, ymin = value - 0.01, ymax = value + 0.01)) +
  geom_linerange(aes(xmin = start, xmax = end, y = value)) +
  # geom_line() +
  # geom_point() +
  # geom_vline(xintercept = c(2010, 2035, 2039, 2060, 2070, 2089, 2099)) +
  scale_y_continuous(limits = c(1, NA), expand = c(0, 0.05), labels = \(x) paste0(x, "x")) +
  facet_grid(cols = vars(ssp)) +
  labs(
    x = "Year",
    y = "Change in Annual Exceedance Probability",
    color = "Return Period in 1985–2014"
  ) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    axis.line = element_line(color = "black"),
    panel.border = element_rect(color = "black", fill = NA))
ggsave("plots/rx5day-extremes-linerange-cols.png", width = 6, height = 4)

