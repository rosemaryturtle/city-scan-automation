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
# r20_50mm_all_df %>%
#   filter(date > "2000-01-01") %>%
#   ggplot(aes(x = date, y = value, linetype = Likelihood, color = ssp)) +
#   geom_line()

# ggplot(r20mm_all_df, aes(x = date, y = value, linetype = Likelihood, color = ssp)) +
#   geom_line() +
#   facet_grid(rows = vars(ssp))

r_observed <- r20_50mm_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
r_projections <- r20_50mm_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

# ggplot(data = r_projections, aes(x = date)) +
#     geom_ribbon(aes(ymin = p10, ymax = p90, fill = Precipitation), alpha = 0.25) +
#     geom_line(aes(y = median, color = Precipitation)) +
#     facet_grid(cols = vars(ssp)) + 
#     geom_line(data = r_observed, aes(y = value, color = Precipitation)) +
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
#     theme(axis.line = element_line(color = "black"))
# ggsave("plots/r20_50mm-cols.png", width = 9, height = 4)

# Overlap
ggplot(mapping = aes(x = date)) +
  geom_line(data = r_observed, aes(y = value, linetype = Precipitation)) +
  geom_line(data = r_projections, aes(y = median, color = ssp, linetype = Precipitation)) +
  geom_ribbon(data = filter(r_projections, Precipitation == "20 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  # geom_line(data = filter(r_projections, Precipitation == "20 mm"), aes(y = median, color = ssp)) +
  geom_ribbon(data = filter(r_projections, Precipitation == "50 mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  # geom_line(data = filter(r_projections, Precipitation == "50 mm"), aes(y = median, color = ssp)) +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  scale_linetype_manual(values = c("20 mm" = "longdash", "50 mm" = "dotted")) +
  labs(
    x = "Year",
    y = "Days exceeding threshold precipitation",
    fill = "Scenario", color = "Scenario"
  ) +
  # facet_grid(rows = vars(Precipitation)) + 
  # annotate(x = )
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  annotate("text",
    x = as.Date("2022-07-01"), y = .95*max(c(r_observed$value, r_projections$p90), na.rm = T),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = .95*max(c(r_observed$value, r_projections$p90), na.rm = T),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(
    legend.position = "bottom",
    legend.title = element_text(size = rel(0.7)), legend.text = element_text(size = rel(0.7)),
ggsave(file.path(charts_dir, "r20mm-r50mm.png"), width = 6, height = 4)

# # Overlap, no observed
# ggplot(mapping = aes(x = date)) +
#     geom_line(data = r_projections, aes(y = median, color = ssp, linetype = Precipitation)) +
#     geom_ribbon(data = filter(r_projections, Precipitation == "20mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
#     # geom_line(data = filter(r_projections, Precipitation == "20mm"), aes(y = median, color = ssp)) +
#     geom_ribbon(data = filter(r_projections, Precipitation == "50mm"), aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
#     # geom_line(data = filter(r_projections, Precipitation == "50mm"), aes(y = median, color = ssp)) +
#     scale_x_date(
#       breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
#       labels = seq(1950, 2100, by = 10)) +
#     scale_y_continuous(expand = c(0, NA)) +
#     labs(
#       x = "Year",
#       y = "Days exceeding threshold precipitation",
#       fill = "Scenario", color = "Scenario"
#     ) +
#     # facet_grid(rows = vars(Precipitation)) + 
#     # annotate(x = )
#     theme_minimal() +
#     theme(legend.position = "bottom",
#     axis.line = element_line(color = "black"))
# ggsave("plots/r20_50mm-overlap-no-observed.png", width = 6, height = 4)