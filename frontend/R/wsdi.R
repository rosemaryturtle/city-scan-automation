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
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

wsdi_observed <- wsdi_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
wsdi_projections <- wsdi_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)


# Overlap
# Should title include what the 90th percentile max temp is?
# See https://www.ecad.eu/maxtemp_EOBS_indices.php for definition attempt
# Also https://www.climdex.org/learn/indices/
ggplot(data = wsdi_projections, aes(x = date)) +
  # geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_line(aes(y = median, color = ssp)) +
  geom_line(data = wsdi_observed, aes(y = value), color = "#969696") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  labs(
    title = "Projected duration of warm spells",
    x = "Year",
    y = "Days in a row",
    fill = "Scenario", color = "Scenario",
    caption = break_lines("Number of days when temperature exceeds base period's 90th percentile max temperature for that calendar day, day before, and day after", 80, "\n"),
  ) +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = .95*max(c(wsdi_observed$value, wsdi_projections$median), na.rm = T),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = .95*max(c(wsdi_observed$value, wsdi_projections$median), na.rm = T),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "wsdi.png"), width = 6, height = 4)

ggplot(data = filter(wsdi_projections, ssp == "SSP3-7.0"), aes(x = date)) +
  geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_line(aes(y = median, color = ssp)) +
  geom_line(data = wsdi_observed, aes(y = value), color = "#969696") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  labs(
    title = "Projected duration of warm spells under SSP3-7.0",
    x = "Year",
    y = "Days in a row",
    fill = "Scenario", color = "Scenario",
    caption = break_lines("Number of days when temperature exceeds base period's 90th percentile max temperature for that calendar day, day before, and day after.\nShaded area shows 10th to 90th percentile cases", 80, "\n"),
  ) +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = .95*max(c(wsdi_observed$value, wsdi_projections$p90), na.rm = T),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = .95*max(c(wsdi_observed$value, wsdi_projections$p90), na.rm = T),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(
    legend.position = "none",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
    plot.caption = element_text(color = "grey30", size = rel(0.7), hjust = 0),
    axis.line = element_line(color = "black"),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "wsdi-ssp3.png"), width = 6, height = 4)

# # Alternatives
# ggplot(data = wsdi_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.25) +
#     geom_line(aes(y = median)) +
#     facet_grid(cols = vars(ssp)) + 
#     geom_line(data = wsdi_observed, aes(y = value), color = "#969696") +
#     # geom_vline(xintercept = as.Date("2015-07-01")) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
#       labels = seq(1950, 2100, by = 20)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#       y = "Warm Spell Duration Index (days)"
#     ) +
#     # annotate(x = )
#     theme_minimal() +
#     theme(axis.line = element_line(color = "black"))
# ggsave("plots/wsdi-cols.png", width = 9, height = 4)

# # Overlap, no observed
# ggplot(data = wsdi_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
#     geom_line(aes(y = median, color = ssp)) +
#     # geom_line(data = wsdi_observed, aes(y = value), color = "#969696") +
#     # geom_vline(xintercept = as.Date("2015-07-01")) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
#       labels = seq(1950, 2100, by = 10)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#       y = "Warm Spell Duration Index (days)",
#       fill = "Scenario", color = "Scenario"
#     ) +
#     # annotate(x = )
#     theme_minimal() +
#     theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"))
# ggsave("plots/wsdi-overlap-no-observed.png", width = 6, height = 4)

