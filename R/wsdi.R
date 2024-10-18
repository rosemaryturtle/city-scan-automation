# WSDI ----

wsdi_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/wsdi",
  basename(unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "wsdi"))))) %>%
  str_replace(".nc", "-cog.tif")

setGDALconfig("GS_NO_SIGN_REQUEST=YES")
wsdi_all_df <- wsdi_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood)) %>%
  filter(date > "1980-01-01")
wsdi_observed <- wsdi_all_df %>%
  select(-file, -ssp) %>%
  filter(historical)
wsdi_projections <- wsdi_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

common_plot <- ggplot(mapping = aes(x = date)) +
  geom_line(data = wsdi_observed, aes(y = value), color = "#969696") +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  theme_minimal()

# One plot, overlapping scenarios, median only, smoothed projections with historical
# Should title include what the 90th percentile max temp is?
# See https://www.ecad.eu/maxtemp_EOBS_indices.php for definition attempt
# Also https://www.climdex.org/learn/indices/
common_plot +
  geom_line(data = wsdi_projections, aes(y = median, color = ssp)) +
  labs(
    title = "Projected duration of warm spells",
    x = "Year",
    y = "Days in a row",
    fill = "Scenario", color = "Scenario",
    caption = break_lines("Number of days when temperature exceeds base period's 90th percentile max temperature for that calendar day, day before, and day after", 80, "\n"),
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(wsdi_all_df, Likelihood %in% c("Observed", "median"))$value, lower_limit = 0),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(wsdi_all_df, Likelihood %in% c("Observed", "median"))$value, lower_limit = 0),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "bottom")
ggsave(file.path(charts_dir, "wsdi.png"), width = 6, height = 4)

# One plot, one SSP only, median, 10th, 90th percentiles, smoothed projections with historical
# Selected SSP is set in setup.R
common_plot +
  geom_ribbon(data = filter(wsdi_projections, ssp == selected_ssp), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_line(data = filter(wsdi_projections, ssp == selected_ssp), aes(y = median, color = ssp)) +
  labs(
    title = paste("Projected duration of warm spells under", selected_ssp),
    x = "Year",
    y = "Days in a row",
    fill = "Scenario", color = "Scenario",
    caption = break_lines("Number of days when temperature exceeds base period's 90th percentile max temperature for that calendar day, day before, and day after.\nShaded area shows 10th to 90th percentile cases", 80, "\n"),
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(wsdi_all_df, ssp == selected_ssp)$value, lower_limit = 0),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(wsdi_all_df, ssp == selected_ssp)$value, lower_limit = 0),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "none")
ggsave(file.path(charts_dir, paste0("wsdi-", selected_ssp, ".png")), width = 6, height = 4)
