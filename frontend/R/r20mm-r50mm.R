# r20mm, r50mm ----

r20mm_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/r20mm",
  basename(unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "r20mm"))))) %>%
  str_replace(".nc", "-cog.tif")
r50mm_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/r50mm",
  basename(unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "r50mm"))))) %>%
  str_replace(".nc", "-cog.tif")

setGDALconfig("GS_NO_SIGN_REQUEST=YES")
r20mm_all_df <- r20mm_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))
r50mm_all_df <- r50mm_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))
r20_50mm_all_df <- bind_rows(r20mm_all_df, r50mm_all_df) %>% 
  mutate(Precipitation = str_replace(str_extract(file, "\\d{2}mm"), "(?<=0)", " ")) %>%
  filter(date > "1980-01-01")

r_observed <- r20_50mm_all_df %>%
  select(-file, -ssp) %>%
  filter(historical)
r_projections <- r20_50mm_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

r_direct_labels <- r_projections %>% group_by(Precipitation)  %>%
  slice_max(date) %>% slice_max(median, n = 2) %>% slice_min(median) %>%
  mutate(label = paste(Precipitation, "of rain"))

common_plot <- ggplot(mapping = aes(x = date)) +
  geom_text(
    data = r_direct_labels, aes(y = median, label = label),
    size = 2, hjust = 0, nudge_x = 300) +
  geom_line(data = r_observed, aes(y = value, linetype = Precipitation), color = "#969696") +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10),
    expand = expansion(c(0, 0.15))) +
  scale_y_continuous(expand = expansion(c(0, 0.15)), limits = c(0, NA)) +
  scale_linetype_manual(values = c("20 mm" = "solid", "50 mm" = "solid"), guide = "none") +
  theme_minimal()

# One plot, overlapping scenarios, smoothed projections with historical
common_plot +
  geom_line(data = r_projections, aes(y = median, color = ssp, linetype = Precipitation)) +
  labs(
    title = "Days with more than 20 & 50 mm of rain",
    x = "Year",
    y = "Days per year",
    fill = "Scenario", color = "Scenario"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(r20_50mm_all_df, Likelihood %in% c("Observed", "median"))$value, lower_limit = 0),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(r20_50mm_all_df, Likelihood %in% c("Observed", "median"))$value, lower_limit = 0),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "bottom")
ggsave(file.path(charts_dir, "r20mm-r50mm.png"), width = 6, height = 4)

# One plot, one SSP only, median, 10th, 90th percentiles, smoothed projections with historical
# Selected SSP is set in setup.R
common_plot +
  geom_line(data = filter(r_projections, ssp == selected_ssp), aes(y = median, color = ssp, linetype = Precipitation)) +
  geom_ribbon(data = filter(r_projections, ssp == selected_ssp, Precipitation == "20 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_ribbon(data = filter(r_projections, ssp == selected_ssp, Precipitation == "50 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  labs(
    title = paste("Days with more than 20 & 50 mm of rain under", selected_ssp),
    x = "Year",
    y = "Days per year",
    fill = "Scenario", color = "Scenario",
    caption = "Shaded area shows 10th to 90th percentile cases"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"),
    y = annotation_height(filter(r20_50mm_all_df, ssp == selected_ssp)$value, lower_limit = 0),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"),
    y = annotation_height(filter(r20_50mm_all_df, ssp == selected_ssp)$value, lower_limit = 0),
    label = "Projected →",
    hjust = 0) +
  theme_cckp_chart(legend.position = "none")
ggsave(file.path(charts_dir, paste0("r20mm-r50mm-", selected_ssp, ".png")), width = 6, height = 4)
