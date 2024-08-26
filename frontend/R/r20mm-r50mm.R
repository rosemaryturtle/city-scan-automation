# r20mm, r50mm ----

r20mm_paths <- unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "r20mm")))
r50mm_paths <- unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "r50mm")))

r20mm_all_df <- file.path(
  "source-data/r20mm",
  str_extract(c(r20mm_paths), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

r50mm_all_df <- file.path(
  "source-data/r50mm",
  str_extract(c(r50mm_paths), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

r20_50mm_all_df <- bind_rows(r20mm_all_df, r50mm_all_df) %>% 
  mutate(Precipitation = str_replace(str_extract(file, "\\d{2}mm"), "(?<=0)", " "))

r_observed <- r20_50mm_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
r_projections <- r20_50mm_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

r_direct_labels <- r_projections %>% group_by(Precipitation)  %>%
  slice_max(date) %>% slice_max(median, n = 2) %>% slice_min(median) %>%
  mutate(label = paste(Precipitation, "of rain"))

# Overlap
ggplot(mapping = aes(x = date)) +
  geom_text(data = r_direct_labels, aes(y = median, label = label),
      size = 2, hjust = 0, nudge_x = 300) +
  geom_line(data = r_observed, aes(y = value, linetype = Precipitation), color = "#969696") +
  geom_line(data = r_projections, aes(y = median, color = ssp, linetype = Precipitation)) +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10),
    expand = expansion(c(0, 0.15))) +
    scale_y_continuous(expand = expansion(c(0.1, 0.1))) +
  scale_linetype_manual(values = c("20 mm" = "solid", "50 mm" = "solid"), guide = "none") +
  labs(
    title = "Days with more than 20 & 50 mm of rain",
    x = "Year",
    y = "Days exceeding threshold precipitation",
    fill = "Scenario", color = "Scenario"
  ) +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(r_observed$value, r_projections$median)),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(r_observed$value, r_projections$median)),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "r20mm-r50mm.png"), width = 6, height = 4)

ggplot(mapping = aes(x = date)) +
  geom_text(data = r_direct_labels, aes(y = median, label = label),
      size = 2, hjust = 0, nudge_x = 300) +
  geom_line(data = r_observed, aes(y = value, linetype = Precipitation), color = "#969696") +
  geom_line(data = filter(r_projections, ssp == "SSP3-7.0"), aes(y = median, color = ssp, linetype = Precipitation)) +
  geom_ribbon(data = filter(r_projections, ssp == "SSP3-7.0", Precipitation == "20 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  # geom_line(data = filter(r_projections, Precipitation == "20 mm"), aes(y = median, color = ssp)) +
  geom_ribbon(data = filter(r_projections, ssp == "SSP3-7.0", Precipitation == "50 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  # geom_line(data = filter(r_projections, Precipitation == "50 mm"), aes(y = median, color = ssp)) +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10),
    expand = expansion(c(0, 0.15))) +
    scale_y_continuous(expand = expansion(c(0.1, 0.1))) +
  scale_linetype_manual(values = c("20 mm" = "solid", "50 mm" = "solid"), guide = "none") +
  labs(
    title = "Days with more than 20 & 50 mm of rain under SSP3-7.0",
    x = "Year",
    y = "Days exceeding threshold precipitation",
    fill = "Scenario", color = "Scenario",
    caption = "Shaded area shows 10th to 90th percentile cases"
  ) +
  # facet_grid(rows = vars(Precipitation)) + 
  # annotate(x = )
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(r_observed$value, r_projections$p90)),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = (\(v) .95*diff(range(v)) + min(v))(c(r_observed$value, r_projections$p90)),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(
    legend.position = "none",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "r20mm-r50mm-ssp3.png"), width = 6, height = 4)
