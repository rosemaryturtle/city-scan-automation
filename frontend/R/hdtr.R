# HDTR
# hdtr_test <- rast("source-data/hdtr/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp126_climatology_median_2040-2059.nc")

hdtr_all_df <- list.files("source-data/hdtr", full.names = T) %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

# # None
# hdtr_observed <- hdtr_all_df %>%
#   select(-file, -ssp) %>%
#   filter(historical) %>%
#   filter(date > "1980-01-01")

hdtr_projections <- hdtr_all_df %>%
  filter(!historical) %>%
  select(-file, -historical) %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

# Radial bar, 3 col
hdtr_projections %>%
  ggplot(aes(x = date)) +
  geom_col(aes(y = median, fill = ssp), position = "dodge") +
  facet_wrap(vars(ssp), ncol = 3) +
  labs(
    title = "Hot Days with Tropical Nights",
    x = "Month",
  ) +
  theme_minimal() +
  theme(legend.position = "none",
    axis.line = element_line(color = "black"),
    axis.title.y = element_blank(),
    panel.grid.major.x = element_blank(),
    plot.background = element_rect(color = NA, fill = "white")) +
  scale_x_continuous(
    breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
    minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
    labels = month.abb) +
  scale_y_continuous(
    breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
    limits = c(0, 4.5)) +
  coord_radial(expand = F,
    inner.radius = .4)
ggsave(file.path(charts_dir, "hdtr.png"), width = 9, height = 4)

# Radial bar, 3 col
hdtr_projections %>%
  filter(ssp == "SSP3-7.0") %>%
  # mutate(across(c(median, p10, p90), \(x) x + as.numeric(str_extract(ssp, "(?<=SSP)\\d"))/20)) %>%
  # filter(ssp == "SSP1-2.6") %>%
  ggplot(aes(x = date)) +
  geom_col(aes(y = median, fill = ssp), position = "dodge") +
  geom_step(aes(y = p10), direction = "mid", linetype = "dotted") +
  geom_step(aes(y = p90), direction = "mid", linetype = "dotted") +
  # geom_step(aes(y = median, color = ssp), direction = "mid") +
  # pammtools::geom_stepribbon(aes(ymin = p10, ymax = p90, color = ssp), fill = NA, linetype = "dashed", direction = "mid") +
  facet_wrap(vars(ssp), ncol = 3) +
  labs(
    title = "Hot Days with Tropical Nights under SSP3-7.0",
    x = "Month",
    # y = "Category of Risk",
    caption = "Dashed line shows 10th and 90th percentile cases"
  ) +
  theme_minimal() +
  theme(legend.position = "none",
    axis.line = element_line(color = "black"),
    axis.title.y = element_blank(),
    panel.grid.major.x = element_blank(),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    plot.background = element_rect(color = NA, fill = "white")) +
  scale_x_continuous(
    breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
    minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
    labels = month.abb) +
  scale_y_continuous(
    breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
    limits = c(0, 4.5)) +
  coord_radial(expand = F,
    # r.axis.inside = T,
    inner.radius = .4)
ggsave(file.path(charts_dir, "hdtr-ssp3.png"), width = 6, height = 4)
 
# # Line chart (Bar chart would be better?), 3 cols
# hdtr_projections %>%
#   ggplot(aes(x = date)) +
#   geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.33) +
#   geom_line(aes(y = median)) +
#     scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   facet_wrap(vars(ssp), nrow = 1) +
#   labs(
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-line-cols.png", width = 6, height = 4)

# # Bar chart, 3 rows
# hdtr_projections %>%
#   ggplot(aes(x = date)) +
#   # geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.33) +
#   geom_col(aes(y = median), fill = "blue", alpha = .3) +
#   # geom_errorbar(aes(ymin = p10, ymax = p90)) +
#   geom_linerange(aes(ymin = p10, ymax = p90), linetype = "dashed") +
#   # geom_pointrange(aes(y = median, ymin = p10, ymax = p90)) +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4)) +
#   facet_wrap(vars(ssp), nrow = 3) +
#   labs(
#     # title = "Hot Days with Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-bar-rows.png", width = 6, height = 4)

# # Point range
# hdtr_projections %>%
#   mutate(date = date + 2*as.numeric(str_extract(ssp, "(?<=SSP)\\d")) - 4) %>%
#   ggplot(aes(x = date)) +
#   geom_pointrange(aes(y = median, ymin = p10, ymax = p90, color = ssp), linetype = "dashed") +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4)) +
#   # facet_wrap(vars(ssp), nrow = 3) +
#   labs(
#     # title = "Hot Days with Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)",
#     color = "SSP",
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-points.png", width = 6, height = 4)

# # Step plot
# hdtr_projections %>%
#   ggplot(aes(x = date)) +
#   # geom_col(aes(y = median), position = "dodge") +
#   geom_step(aes(y = median), direction = "mid") +
#   pammtools::geom_stepribbon(aes(ymin = p10, ymax = p90), color = "black", linetype = "dashed", fill = NA, direction = "mid") +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4)) +
#   facet_wrap(vars(ssp), nrow = 3) +
#   labs(
#     # title = "Hot Days with Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-step-rows.png", width = 6, height = 4)

# # Bar, overlaid
# hdtr_projections %>%
#   ggplot(aes(x = date)) +
#   # geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.33) +
#   geom_col(aes(y = median, fill = ssp), position = "dodge") +
#   geom_errorbar(aes(ymin = p10, ymax = p90, group = ssp), position = "dodge", linetype = "dashed", linewidth = 0.25) +
#   # geom_linerange(aes(ymin = p10, ymax = p90)) +
#   # geom_pointrange(aes(ymin = p10, ymax = p90)) +
#   # facet_wrap(vars(ssp), nrow = 3) +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4)) +
#   labs(
#     # title = "Hot Days and Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-bar-overlap.png", width = 8, height = 6)

# # Bar, overlaid, errorline
# hdtr_projections %>%
#   ggplot(aes(x = date)) +
#   # geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.33) +
#   geom_col(aes(y = median, fill = ssp), position = "dodge") +
#   # geom_errorbar(aes(ymin = p10, ymax = p90, group = ssp), position = "dodge", linetype = "dashed", linewidth = 0.25) +
#   geom_linerange(aes(ymin = p10, ymax = p90, group = ssp), position = position_dodge(width = 20), color = "darkgrey", linewidth = 0.5) +
#   # geom_pointrange(aes(ymin = p10, ymax = p90)) +
#   # facet_wrap(vars(ssp), nrow = 3) +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4)) +
#   labs(
#     # title = "Hot Days and Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank())
# ggsave("plots/hdtr-bar-errorline-overlap.png", width = 8, height = 6)

# # Radial
# hdtr_projections %>%
#   mutate(across(c(median, p10, p90), \(x) x + as.numeric(str_extract(ssp, "(?<=SSP)\\d"))/20)) %>%
#   # filter(ssp == "SSP1-2.6") %>%
#   ggplot(aes(x = date)) +
#   # geom_col(aes(y = median, fill = ssp), position = "dodge") +
#   geom_step(aes(y = median, color = ssp), direction = "mid") +
#   pammtools::geom_stepribbon(aes(ymin = p10, ymax = p90, color = ssp), fill = NA, linetype = "dashed", direction = "mid") +
#   # facet_wrap(vars(ssp), nrow = 3) +
#   labs(
#     # title = "Hot Days with Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank()) +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4.5)) +
#   coord_radial(expand = F,
#     r.axis.inside = T,
#     inner.radius = .4)
# ggsave("plots/hdtr-radial-line.png", width = 9, height = 9)

# # Radial bar
# hdtr_projections %>%
#   # mutate(across(c(median, p10, p90), \(x) x + as.numeric(str_extract(ssp, "(?<=SSP)\\d"))/20)) %>%
#   # filter(ssp == "SSP1-2.6") %>%
#   ggplot(aes(x = date)) +
#   geom_col(aes(y = median, fill = ssp), position = "dodge") +
#   # geom_step(aes(y = median, color = ssp), direction = "mid") +
#   # pammtools::geom_stepribbon(aes(ymin = p10, ymax = p90, color = ssp), fill = NA, linetype = "dashed", direction = "mid") +
#   # facet_wrap(vars(ssp), nrow = 3) +
#   labs(
#     # title = "Hot Days with Tropical Nights (error bar shows 10th and 90th percentile case)",
#     x = "Month",
#     y = "Category of Risk (4 is Extreme Risk)"
#   ) +
#   theme_minimal() +
#   theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"),
#     panel.grid.major.x = element_blank()) +
#   scale_x_continuous(
#     breaks = seq.Date(from = as.Date("2040-01-16"), length.out = 12, by = "month"),
#     minor_breaks = seq.Date(from = as.Date("2040-01-01"), length.out = 12, by = "month"),
#     labels = month.abb) +
#   scale_y_continuous(
#     breaks = 0:4, labels = c("Low Risk", "Moderate Risk", "Moderate High Risk", "High Risk", "Extreme Risk"),
#     limits = c(0, 4.5)) +
#   coord_radial(expand = F,
#     # r.axis.inside = T,
#     inner.radius = .4)
# ggsave("plots/hdtr-radial-bar.png", width = 7, height = 7)

