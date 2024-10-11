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
    Temperature = "Mean Surface Air Temp.")
txx_all_df <- txx_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
    Temperature = "Max. of Daily Max-Temp.")
tas_txx_all_df <- bind_rows(tas_all_df, txx_all_df) %>%
  filter(date > "1980-01-01")

t_observed <- tas_txx_all_df %>%
  select(-file, -ssp) %>%
  filter(historical)
t_projections <- tas_txx_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

t_direct_labels <- t_projections %>% group_by(Temperature) %>%
  slice_max(date) %>% slice_max(median, n = 2) %>% slice_min(median)

common_plot <- ggplot(mapping = aes(x = date)) +
  geom_text(
    data = t_direct_labels, aes(y = median, label = Temperature),
    size = 2, hjust = 0, nudge_x = 300) +
  geom_line(data = t_observed, aes(y = value, group = Temperature), color = "#969696") +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10),
    expand = expansion(c(0, 0.25))) +
  scale_y_continuous(expand = expansion(c(.1, 0.1))) +
  theme_minimal()

# One plot, overlapping scenarios, smoothed projections with historical
common_plot +
  geom_line(data = t_observed, aes(y = value, group = Temperature), color = "#969696") +
  geom_line(data = t_projections, aes(y = median, group = interaction(Temperature, ssp), color = ssp)) +
  labs(
    title = "Projected temperatures",
    x = "Year",
    y = "Temperature, °C",
    fill = "Scenario", color = "Scenario"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(tas_txx_all_df, Likelihood %in% c("Observed", "median"))$value),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(tas_txx_all_df, Likelihood %in% c("Observed", "median"))$value),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "bottom")
ggsave(file.path(charts_dir, "tas-txx.png"), width = 6, height = 4)

# One plot, one SSP only, median, 10th, 90th percentiles, smoothed projections with historical
# Selected SSP is set in setup.R
common_plot +
  geom_line(data = filter(t_projections, ssp == selected_ssp), aes(y = median, group = interaction(Temperature, ssp), color = ssp)) +
  geom_ribbon(data = filter(t_projections, ssp == selected_ssp, Temperature == "Max. of Daily Max-Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
  geom_ribbon(data = filter(t_projections, ssp == selected_ssp, Temperature == "Mean Surface Air Temp."), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.11) +
  labs(
    title = paste("Projected temperatures under", selected_ssp),
    x = "Year",
    y = "Temperature, °C",
    fill = "Scenario", color = "Scenario",
    caption = "Shaded area shows 10th to 90th percentile cases"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(tas_txx_all_df, ssp == selected_ssp)$value),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(tas_txx_all_df, ssp == selected_ssp)$value),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "none")
ggsave(file.path(charts_dir, paste0("tas-txx-", selected_ssp, ".png")), width = 6, height = 4)
