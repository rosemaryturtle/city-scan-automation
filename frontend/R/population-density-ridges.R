# Population density ridge plot
# This script should be sourced after setup.R
# Requires: population.tif in spatial_dir

librarian::shelf(ggridges)

# Read population raster
pop_raster <- fuzzy_read(spatial_dir, "population.*.tif$")

# Extract pixel values to dataframe
pop_df <- as_tibble(pop_raster) %>%
  rename(pop = 1) %>%
  filter(!is.na(pop), pop > 0)

# Calculate x-axis limit (cap at 99th percentile)
x_max <- quantile(pop_df$pop, 0.99)

# Create ridge plot with quantile coloring
p_density <- pop_df %>%
  ggplot(aes(x = pop, y = 1, fill = factor(stat(quantile)))) +
  stat_density_ridges(
    geom = "density_ridges_gradient",
    calc_ecdf = TRUE,
    quantiles = 1:4/5,
    quantile_lines = FALSE,
    alpha = 0.6,
    scale = 0.9
  ) +
  scale_x_continuous(
    breaks = seq(0, ceiling(x_max/10)*10, by = max(10, ceiling(x_max/100)*10)),
    minor_breaks = seq(0, ceiling(x_max/10)*10, by = max(5, ceiling(x_max/200)*10))
  ) +
  scale_fill_manual(
    name = "Percentile",
    values = c('#ECEB72', '#D4BE62', '#BD9252', '#A56542', '#8E3933'),
    labels = c("0-20th", "20-40th", "40-60th", "60-80th", "80-100th")
  ) +
  labs(x = "Population density (people/hectare)") +
  theme_minimal() +
  theme(
    axis.title.y = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    legend.position = "bottom",
    panel.grid.major = element_line(linewidth = .125, color = "dark gray"),
    panel.grid.minor = element_line(linewidth = .125, linetype = 2, color = "dark gray")
  )

# Save plot
ggsave(
  filename = file.path(charts_dir, "population_density_distribution.png"),
  plot = p_density,
  width = 8,
  height = 4,
  dpi = 300
)
