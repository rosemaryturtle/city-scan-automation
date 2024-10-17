# Plotting population growth
# Get population data once and for all (don't need to share, but include in metadata)
if (!file.exists("source-data/paurashava-populations.csv")) {
  url <- paste0("https://www.citypopulation.de/en/bangladesh/cities/")
  paurashava_populations <- read_html(url) %>%
    html_node("section#citysection") %>%
      html_node("table") %>%
      html_table(na.strings = "...") %>%
      select(
        Location = Name, Location_bn = Native, Status, Administration = "Adm.",
        contains("Population"), Area = starts_with("Area")) %>%
    # filter(str_detect(tolatin(Location), tolatin(city))) %>%
    pivot_longer(cols = contains("Population"), values_to = "Population", names_to = "Year") %>%
    mutate(
      Location = Location,
      Year = str_extract(Year, "\\d{4}") %>% as.numeric(),
      Population = str_replace_all(Population, ",", "") %>% as.numeric(),
      Area_km = as.numeric(Area)/100,
      .keep = "unused") %>%
    arrange(Location, Year)
  paurashava_populations[paurashava_populations$Year != 2022, "Area_km"] <- NA
  write_csv(paurashava_populations, "source-data/paurashava-populations.csv")
}

# Make plot
paurashava_populations <- read_csv("source-data/paurashava-populations.csv", col_types = "ccccddd")

pop_growth <- paurashava_populations %>%
  # Beware that city names may be spelled differently
  filter(str_detect(Location, city))

pop_growth_plot <- ggplot(pop_growth, aes(x = Year, y = Population, group = Location)) + #, color = Source))
  geom_line() +
  geom_point() +
  scale_x_continuous(
    expand = expansion(c(0, 0)),
    breaks = seq(1990,2025, by = 5), minor_breaks = 1990:2025) +
  expand_limits(x = c(1990, 2023)) +
  scale_y_continuous(
    limits = c(0, max(pop_growth$Population)), labels = scales::comma, expand = expansion(c(0, .1))) +    
  theme_minimal() +
  labs(
    title = paste0(city, " Population Growth, ", min(pop_growth$Year), "-", max(pop_growth$Year)),
    caption = "Census data aggregated by Thomas Brinkhoff, City Population") +
  theme(
    axis.line = element_line(linewidth = .5, color = "black"),
    panel.grid.major = element_line(linewidth = .125, color = "grey"),
    panel.grid.minor = element_line(linewidth = .125, linetype = 2, color = "grey"),
    plot.caption = element_text(color = "grey30", size = rel(0.7)),
    plot.background = element_rect(color = NA, fill = "white"))
ggsave(file.path(charts_dir, "oxford-pop-growth.png"), plot = pop_growth_plot, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")

# # Do we want to plot all paurashavas? Do we want to plot with nearby ones? Or similarly sized ones?
# ggplot(paurashava_populations) +
#   geom_line(
#     data = ~ filter(.x, str_detect(Location, city)),
#     aes(x = Year, y = Population, group = Location)) +
#   geom_line(
#     data = ~ filter(.x, !str_detect(Location, city)),
#     aes(x = Year, y = Population, group = Location),
#     color = "grey")