# CSDI ----
csdi_paths <- unlist(lapply(generic_paths, \(s) glue::glue(s, codes = "csdi")))

csdi_all_df <- file.path(
  "source-data/csdi",
  str_extract(c(csdi_paths), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

csdi_observed <- csdi_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
csdi_projections <- csdi_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

# Columns
ggplot(data = csdi_projections, aes(x = date)) +
    geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.25) +
    geom_line(aes(y = median)) +
    facet_grid(cols = vars(ssp)) + 
    geom_line(data = csdi_observed, aes(y = value), color = "#969696") +
    # geom_vline(xintercept = as.Date("2015-07-01")) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
      labels = seq(1950, 2100, by = 20)) +
    scale_y_continuous(expand = c(0, NA)) +
    labs(
      x = "Year",
      y = "Cold Spell Duration Index (days)"
    ) +
    # annotate(x = )
    theme_minimal() +
    theme(axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-cols.png"), width = 9, height = 4)

# Rows
ggplot(data = csdi_projections, aes(x = date)) +
    geom_ribbon(aes(ymin = p10, ymax = p90), color = "black", linetype = "dashed", fill = NA) +
    geom_line(aes(y = median)) +
    facet_grid(rows = vars(ssp)) + 
    geom_line(data = csdi_observed, aes(y = value), color = "#969696") +
    # geom_vline(xintercept = as.Date("2015-07-01")) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
      labels = seq(1950, 2100, by = 20)) +
    scale_y_continuous(expand = c(0, NA)) +
    labs(
      x = "Year",
      y = "Cold Spell Duration Index (days)"
    ) +
    # annotate(x = )
    theme_minimal() +
    theme(axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-rows.png"), width = 9, height = 4)

# Overlap, no observed
ggplot(data = csdi_projections, aes(x = date)) +
    geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
    geom_line(aes(y = median, color = ssp)) +
    # geom_line(data = csdi_observed, aes(y = value), color = "#969696") +
    # geom_vline(xintercept = as.Date("2015-07-01")) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
      labels = seq(1950, 2100, by = 10)) +
    scale_y_continuous(expand = c(0, NA)) +
    labs(
      x = "Year",
      y = "Cold Spell Duration Index (days)",
      fill = "Scenario", color = "Scenario"
    ) +
    # annotate(x = )
    theme_minimal() +
    theme(legend.position = "bottom",
    axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-overlap-no-observed.png"), width = 6, height = 4)

# Overlap
ggplot(data = csdi_projections, aes(x = date)) +
  geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_line(aes(y = median, color = ssp)) +
  geom_line(data = csdi_observed, aes(y = value), color = "#969696") +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dotted") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  labs(
    x = "Year",
    y = "Cold Spell Duration Index (days)",
    fill = "Scenario", color = "Scenario"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"), y = .95*max(c(csdi_observed$value, csdi_projections$median), na.rm = T),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = .95*max(c(csdi_observed$value, csdi_projections$median), na.rm = T),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(legend.position = "bottom",
  axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-overlap.png"), width = 6, height = 4)

# CSDI no smooth
csdi_paths_no_smooth <- csdi_paths %>% str_replace("-smooth", "")

csdi_no_smooth_all_df <- file.path(
  "source-data/csdi",
  str_extract(c(csdi_paths_no_smooth), "[^/]+$")) %>%
  # str_subset("median") %>%
  # rast()
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3"),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|p10|p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood))

csdi_no_smooth_observed <- csdi_no_smooth_all_df %>%
  select(-file, -ssp) %>%
  filter(historical) %>%
  filter(date > "1980-01-01")
csdi_no_smooth_projections <- csdi_no_smooth_all_df %>%
  select(-file) %>%
  filter(!historical) %>%
  filter(date > "2023-01-01") %>%
  tidyr::pivot_wider(names_from = Likelihood, values_from = value)

ggplot(data = csdi_no_smooth_projections, aes(x = date)) +
    geom_ribbon(aes(ymin = p10, ymax = p90), fill = "blue", alpha = 0.25) +
    geom_line(aes(y = median)) +
    facet_grid(cols = vars(ssp)) + 
    geom_line(data = csdi_no_smooth_observed, aes(y = value), color = "#969696") +
    # geom_vline(xintercept = as.Date("2015-07-01")) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "20 years"),
      labels = seq(1950, 2100, by = 20)) +
    scale_y_continuous(expand = c(0, NA)) +
    labs(
      x = "Year",
      y = "Cold Spell Duration Index (days)"
    ) +
    # annotate(x = )
    theme_minimal() +
    theme(axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-cols-no-smooth.png"), width = 9, height = 4)

ggplot(data = csdi_no_smooth_projections, aes(x = date)) +
    geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
    geom_line(aes(y = median, color = ssp)) +
    # geom_line(data = csdi_no_smooth_observed, aes(y = value), color = "#969696") +
    # geom_vline(xintercept = as.Date("2015-07-01")) +
    scale_x_date(
      breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
      labels = seq(1950, 2100, by = 10)) +
    scale_y_continuous(expand = c(0, NA)) +
    labs(
      x = "Year",
      y = "Cold Spell Duration Index (days)",
      fill = "Scenario", color = "Scenario"
    ) +
    # annotate(x = )
    theme_minimal() +
    theme(legend.position = "bottom",
    axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-overlap-no-observed-no-smooth.png"), width = 6, height = 4)

# Overlap
ggplot(data = csdi_no_smooth_projections, aes(x = date)) +
  geom_ribbon(aes(ymin = p10, ymax = p90, fill = ssp), alpha = 0.33) +
  geom_line(aes(y = median, color = ssp)) +
  geom_line(data = csdi_no_smooth_observed, aes(y = value), color = "#969696") +
  geom_vline(xintercept = as.Date("2023-07-01"), linetype = "dashed") +
  scale_x_date(
    breaks = seq.Date(as.Date("1950-01-01"), as.Date("2100-01-01"), by = "10 years"),
    labels = seq(1950, 2100, by = 10)) +
  scale_y_continuous(expand = c(0, NA)) +
  labs(
    x = "Year",
    y = "Cold Spell Duration Index (days)",
    fill = "Scenario", color = "Scenario"
  ) +
  annotate("text",
    x = as.Date("2022-07-01"), y = .95*max(c(csdi_observed$value, csdi_projections$median), na.rm = T),
    label = "← Observed",
    hjust = 1) +
  annotate("text",
    x = as.Date("2024-07-01"), y = .95*max(c(csdi_observed$value, csdi_projections$median), na.rm = T),
    label = "Projected →",
    hjust = 0) +
  theme_minimal() +
  theme(legend.position = "bottom",
  axis.line = element_line(color = "black"))
ggsave(file.path(charts_dir, "csdi-overlap-no-smooth.png"), width = 6, height = 4)
