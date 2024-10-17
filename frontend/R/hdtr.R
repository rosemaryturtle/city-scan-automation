# HDTR

hdtr_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/hdtr",
  glue("climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp{sort(rep(scenario_numbers, 3))}_climatology_{rep(c('p10', 'median', 'p90'), 3)}_2040-2059-cog.tif"))

setGDALconfig("GS_NO_SIGN_REQUEST=YES")
hdtr_all_df <- hdtr_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood)) %>%
  filter(date > "1980-01-01")

# # None
# hdtr_observed <- hdtr_all_df %>%
#   select(-file, -ssp) %>%
#   filter(historical) %>%

hdtr_projections <- hdtr_all_df %>%
  filter(!historical) %>%
  select(-file, -historical) %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

common_plot <- ggplot(mapping = aes(x = date)) +
  scale_x_continuous(
    breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
    minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
    labels = month.abb) +
  scale_y_continuous(
    breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
    limits = c(0, 4.5)) +
  coord_radial(expand = F,
    # r.axis.inside = T,
    inner.radius = .4) +
  theme_minimal() +
  theme(
    legend.position = "none",
    axis.line = element_line(color = "black"),
    axis.title.y = element_blank(),
    panel.grid.major.x = element_blank(),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    plot.background = element_rect(color = NA, fill = "white"))

# Three radial bar charts, 1 per scenario, median only, no historical
common_plot +
  geom_col(data = hdtr_projections, aes(y = median, fill = ssp), position = "dodge") +
  facet_wrap(vars(ssp), ncol = 3) +
  labs(
    title = "Hot Days with Tropical Nights",
    x = "Month",
  )
ggsave(file.path(charts_dir, "hdtr.png"), width = 9, height = 4)

# One radial bar chart, one SSP only, median, 10th, 90th percentiles, no historical
# Selected SSP is set in setup.R
common_plot +
  geom_col(data = filter(hdtr_projections, ssp == selected_ssp), aes(y = median, fill = ssp), position = "dodge") +
  geom_step(data = filter(hdtr_projections, ssp == selected_ssp), aes(y = p10), direction = "mid", linetype = "dotted") +
  geom_step(data = filter(hdtr_projections, ssp == selected_ssp), aes(y = p90), direction = "mid", linetype = "dotted") +
  labs(
    title = paste("Hot Days with Tropical Nights under", selected_ssp),
    x = "Month",
    caption = "Dashed line shows 10th and 90th percentile cases"
  )
ggsave(file.path(charts_dir, paste0("hdtr-", selected_ssp, ".png")), width = 6, height = 4)
