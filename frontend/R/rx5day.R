# rx5day ----

rx5day_urls <- file.path(
  "/vsigs/city-scan-global-data/cckp/rx5day-extremes", 
  pmap_chr(expand_grid(!!!list(
    string1 = "changefactorfaep",
    return_period = c(5, 10, 20),
    string2 = "yr-rx5day-period-mean_cmip6_period_all-regridded-bct-ssp",
    scenarios = scenario_numbers,
    string3 = "-climatology_median_",
    period = c("2010-2039", "2035-2064", "2060-2089", "2070-2099"),
    string4 = "-cog.tif"
  )), paste0))

setGDALconfig("GS_NO_SIGN_REQUEST=YES")
changefactor <- rx5day_urls %>%
  lapply(extract_ts) %>%
  bind_rows() %>%
  mutate(
    ssp = factor(str_replace(str_extract(file, "ssp\\d{3}"), "ssp(\\d)(\\d)(\\d)", "SSP\\1-\\2.\\3")),
    historical = str_detect(file, "historical"),
    Likelihood = str_extract(file, "median|(?<=_)p10|(?<=_)p90"),
    Likelihood = case_when(historical ~ "Observed", T ~ Likelihood),
    period = str_extract(file, "\\d{4}-\\d{4}"),
    start = as.numeric(str_extract(period, "^\\d{4}")),
    end = as.numeric(str_extract(period, "\\d{4}$")),
    center = (end - start)/2 + start,
    base_return_period = as.numeric(str_extract(file, "\\d+(?=yr-)")),
    new_return_period = base_return_period * value) %>%
  bind_rows(
    full_join(relationship = "many-to-many",
      tibble(
        period = "1985-2014",
        center = 2000,
        base_return_period = c(5, 10, 20),
        new_return_period = c(5, 10, 20)),
      tibble(center = 2000, ssp = levels(.$ssp)),
      by = "center"))

common_plot <- ggplot(mapping = aes(x = center, y = new_return_period, color = ssp)) +
  scale_x_continuous(
    breaks = unique(changefactor$center),
    labels = unique(changefactor$period)) +
  scale_y_continuous(breaks = seq(0, 100, 5), limits = c(0, NA), expand = expansion(c(0, 0.05))) +
  theme_minimal()
# One plot, overlapping scenarios, median only, with historical
common_plot +
  geom_point(data = changefactor, size = 0.5) +
  geom_line(data = changefactor, aes(group = interaction(base_return_period, ssp))) +
  labs(
    title = "Projected frequencies of extreme 5-day precipitation",
    x = "Time period", y = "Return period (years)", color = "Scenario"
    ) +
  theme_cckp_chart(legend.position = "bottom")

# One plot, one SSP only, median only, with historical
# Selected SSP is set in setup.R
common_plot +
  geom_point(data = filter(changefactor, ssp == "SSP3-7.0"), size = 0.5) +
  geom_line(data = filter(changefactor, ssp == "SSP3-7.0"), aes(group = interaction(base_return_period, ssp))) +
  labs(
    title = "Projected frequencies of extreme 5-day precipitation in SSP3-7.0",
    x = "Time period", y = "Return period (years)", color = "Scenario"
    ) +
  theme_cckp_chart(legend.position = "none")
ggsave(file.path(charts_dir, paste0("rx5day-", selected_ssp, ".png")), width = 6, height = 4)
