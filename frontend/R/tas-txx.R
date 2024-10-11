# tas, txx ----

tas_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/tas",
  basename(unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "tas"))))) %>%
  str_replace(".nc", "-cog.tif")
txx_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/txx",
  basename(unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "txx"))))) %>%
  str_replace(".nc", "-cog.tif")

setGDALconfig("GS_NO_SIGN_REQUEST=YES")
tas_all_df <- tas_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
    Temperature = "Max. of Daily Max-Temp.")

txx_all_df <- file.path(
  "source-data/txx",
  str_extract(c(txx_paths), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
    Temperature = "Avg. Mean Surface Air Temp.")

tas_txx_all_df <- bind_rows(tas_all_df, txx_all_df)

t_observed <- tas_txx_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
t_projections <- tas_txx_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

t_direct_labels <- t_projections %>% group_by(Temperature) %>% slice_max(date) %>% slice_max(median, n = 2) %>% slice_min(median)

# Overlap
ggplot(mapping = aes(x = date)) +
    geom_text(data = t_direct_labels, aes(y = median, label = Temperature),
      size = 2, hjust = 0, nudge_x = 300) +
    geom_line(data = t_observed, aes(y = value, group = Temperature), color = "#969696") +
    geom_line(data = t_projections, aes(y = median, group = interaction(Temperature, ssp), color = ssp)) +
    # geom_ribbon(data = filter(t_projections, Temperature == "Max. of Daily Max-Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
    # geom_ribbon(data = filter(t_projections, Temperature == "Avg. Mean Surface Air Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
      labels = seq(1950, 2100, by = 10),
      expand = expansion(c(0, 0.25))) +
    scale_y_continuous(expand = expansion(c(0.1, 0.1))) +
    labs(
      title = "Projected temperatures",
      x = "Year",
      y = "Temperature, °C",
      fill = "Scenario", color = "Scenario"
    ) +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(t_observed$value, t_projections$p90)),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(t_observed$value, t_projections$p90)),
    label = "Projected →",
    hjust = 0) +
    theme_minimal() +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "tas-txx.png"), width = 6, height = 4)

ggplot(mapping = aes(x = date)) +
    geom_text(data = t_direct_labels, aes(y = median, label = Temperature),
      size = 2, hjust = 0, nudge_x = 300) +
    geom_line(data = t_observed, aes(y = value, group = Temperature), color = "#969696") +
    geom_line(data = filter(t_projections, ssp == "SSP3-7.0"), aes(y = median, group = interaction(Temperature, ssp), color = ssp)) +
    geom_ribbon(data = filter(t_projections, ssp == "SSP3-7.0", Temperature == "Max. of Daily Max-Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
    geom_ribbon(data = filter(t_projections, ssp == "SSP3-7.0", Temperature == "Avg. Mean Surface Air Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
      labels = seq(1950, 2100, by = 10),
      expand = expansion(c(0, 0.25))) +
    scale_y_continuous(
      # limits = c(0, NA),
      # expand = expansion(c(0, 0.05))) +
      expand = expansion(c(0.1, 0.1))) +
    labs(
      title = "Projected temperatures under SSP3-7.0",
      x = "Year",
      y = "Temperature, °C",
      fill = "Scenario", color = "Scenario",
      caption = "Shaded area shows 10th to 90th percentile cases"
    ) +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(t_observed$value, t_projections$p90)),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(t_observed$value, t_projections$p90)),
    label = "Projected →",
    hjust = 0) +
    theme_minimal() +
  theme(
    legend.position = "none",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "tas-txx-ssp3.png"), width = 6, height = 4)

# ggplot(data = t_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90, fill = Temperature), alpha = 0.25) +
#     geom_line(aes(y = median, color = Temperature)) +
#     facet_grid(cols = vars(ssp)) + 
#     geom_line(data = t_observed, aes(y = value, color = Temperature)) +
#     # geom_vline(xintercept = as.Date("2015-07-01")) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
#       labels = seq(1950, 2100, by = 20)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#       y = "Days"
#     ) +
#     # annotate(x = )
#     theme_minimal() +
#     theme(
#       legend.position = "bottom",
#       axis.line = element_line(color = "black"))
# ggsave("plots/tas_txx-cols.png", width = 9, height = 4)

# # Overlap, no observed
# ggplot(mapping = aes(x = date)) +
#     # geom_line(data = t_observed, aes(y = value)) +
#     geom_text(data = direct_labels, aes(y = median, label = Temperature),
#       size = 2, hjust = 0, nudge_x = 300) +
#     geom_line(data = t_projections, aes(y = median, group = interaction(Temperature, ssp), color = ssp)) +
#     geom_ribbon(data = filter(t_projections, Temperature == "Max. of Daily Max-Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
#     geom_ribbon(data = filter(t_projections, Temperature == "Avg. Mean Surface Air Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
#       labels = seq(1950, 2100, by = 10),
#       expand = expansion(c(0, .25))
#       ) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#       y = "Temperature, °C",
#       fill = "Scenario", color = "Scenario"
#     ) +
#     # facet_grid(rows = vars(Temperature)) + 
#     # annotate(x = )
#     theme_minimal() +
#     theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"))
# ggsave("plots/tas_txx-overlap-no-observed.png", width = 6, height = 4)