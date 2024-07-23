# Plots for LGCRRP
# 1. CCKP plots
# 2. City scan plots

# setwd("frontend")
source("R/setup.R")

# Climate Projection Charts
# Data from Climate Change Knowledge Portal
# https://climateknowledgeportal.worldbank.org
# To download, could do following, but that we send a cropped multi-band raster
# source("R/download.R")

source("R/csdi.R")
source("R/wsdi.R")
source("R/hdtr.R") # Need to revise, maybe use different data
source("R/r20mm-r50mm.R")
# source("R/r95ptot.R")
source("R/rx5day.R") # Needs fixing
source("R/tas-txx.R")

# Standard city scan plots

# Population growth
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
    plot.caption = element_text(color = "grey30", size = rel(0.7)))
ggsave("plots/oxford-pop-growth.png", plot = pop_growth_plot, device = "png",
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

# WSF built-up area time series plot
wsf <- fuzzy_read(process_output_dir, "wsf_stats", read_csv) %>%
  rename(Year = year, uba_km2 = "cumulative sq km")
uba_plot <- wsf %>%
  ggplot +
  geom_line(aes(x = Year, y = uba_km2)) +
  scale_x_continuous(
    breaks = seq(1985, 2020, 5),
    minor_breaks = seq(1985, 2021, 1)) + 
  scale_y_continuous(labels = scales::comma, limits = c(0, NA), expand = c(0, NA)) +
  theme_minimal() +
  labs(title = "",#paste(city, "Urban Built-up Area, 1985-2015"),
        y = bquote('Urban built-up area,'~km^2)) +
  theme(axis.line = element_line(linewidth = .5, color = "black"))
ggsave("plots/wsf-uba-plot.png", plot = uba_plot, device = "png",
        width = 4, height = 3.5, units = "in", dpi = "print")

# Fluvial
fu <- fuzzy_read(process_output_dir, "flood_stats/.*fluvial_wsf.csv", read_csv) %>%
  rename(Year = VALUE, ">0.1%" = VALUE_1, ">1%" = VALUE_2, ">10%" = VALUE_3) %>%
  pivot_longer(cols = -Year, names_to = "Annual Probability", values_to = "Area_m2") %>%
  .[nrow(.):1,] %>%
  arrange(Year) %>%
  mutate(.by = Year, Area_m2 = cumsum(Area_m2)) %>%
  mutate(.by = `Annual Probability`,
    Area_m2 = cumsum(Area_m2),
    Area_km2 = Area_m2/1e6)
fu_plot <- fu %>%
  ggplot(aes(x = Year, y = Area_km2, color = `Annual Probability`)) +
  geom_line() +
  geom_text(
    data = slice_max(fu, Year), aes(label = `Annual Probability`),
    hjust = 0, vjust = 0.5, direction = "y", nudge_x = .5, min.segment.length = 10, size = rel(2.5)) +
  scale_x_continuous(
    expand = expansion(c(0,.1)),
    breaks = seq(1985, 2020, 5),
    minor_breaks = seq(1985, 2021, 1)) + 
  scale_y_continuous(labels = scales::comma, limits = c(0, NA), expand = expansion(c(0, 0.05))) +
  scale_color_manual(values = c(">0.1%" = "black", ">1%" = "darkgrey", ">10%" = "darkgrey")) +
  theme_minimal() +
  labs(title = "",#paste(city, "Built-Up Area Exposed to River Flooding Historical Growth, 1985-2015"),
        y = bquote('Exposed'~km^2)) +
  theme(axis.line = element_line(linewidth = .5, color = "black"),
        axis.title.x = element_blank(),
        legend.position = "none")
ggsave("plots/wsf-fu-plot.png", plot = fu_plot, device = "png",
        width = 4, height = 3.5, units = "in", dpi = "print")

# Pluvial
pu <- fuzzy_read(process_output_dir, "flood_stats/.*pluvial_wsf.csv", read_csv) %>%
  rename(Year = VALUE, ">0.1%" = VALUE_1, ">1%" = VALUE_2, ">10%" = VALUE_3) %>%
  pivot_longer(cols = -Year, names_to = "Annual Probability", values_to = "Area_m2") %>%
  .[nrow(.):1,] %>%
  arrange(Year) %>%
  mutate(.by = Year, Area_m2 = cumsum(Area_m2)) %>%
  mutate(.by = `Annual Probability`,
    Area_m2 = cumsum(Area_m2),
    Area_km2 = Area_m2/1e6)
pu_plot <- pu %>%
  ggplot(aes(x = Year, y = Area_km2, color = `Annual Probability`)) +
  geom_line() +
  geom_text(
    data = slice_max(pu, Year), aes(label = `Annual Probability`),
    hjust = 0, vjust = 0.5, direction = "y", nudge_x = .5, min.segment.length = 10, size = rel(2.5)) +
  scale_x_continuous(
    expand = expansion(c(0,.1)),
    breaks = seq(1985, 2020, 5),
    minor_breaks = seq(1985, 2021, 1)) + 
  scale_y_continuous(labels = scales::comma, limits = c(0, NA), expand = expansion(c(0, 0.05))) +
  scale_color_manual(values = c(">0.1%" = "black", ">1%" = "darkgrey", ">10%" = "darkgrey")) +
  theme_minimal() +
  labs(title = "",#paste(city, "Built-Up Area Exposed to Rainwater Flooding Historical Growth, 1985-2015"),
        y = bquote('Exposed'~km^2)) +
  theme(axis.line = element_line(linewidth = .5, color = "black"),
        axis.title.x = element_blank(),
        legend.position = "none")
ggsave("plots/wsf-pu-plot.png", plot = pu_plot, device = "png",
        width = 4, height = 3.5, units = "in", dpi = "print")

# Add in coastal

# Combined fluvial, pluvial (add in coastal)
comb <- fuzzy_read(process_output_dir, "flood_stats/.*comb_wsf.csv", read_csv) %>%
  rename(Year = VALUE, ">0.1%" = VALUE_1, ">1%" = VALUE_2, ">10%" = VALUE_3) %>%
  pivot_longer(cols = -Year, names_to = "Annual Probability", values_to = "Area_m2") %>%
  .[nrow(.):1,] %>%
  arrange(Year) %>%
  mutate(.by = Year, Area_m2 = cumsum(Area_m2)) %>%
  mutate(.by = `Annual Probability`,
    Area_m2 = cumsum(Area_m2),
    Area_km2 = Area_m2/1e6)
all_flooding <- bind_rows(
  mutate(comb, type = "Combined"), 
  mutate(fu, type = "River"), 
  mutate(pu, type = "Rainwater")) %>%
  filter(`Annual Probability` == ">0.1%")
all_flooding_plot <- all_flooding %>%
ggplot(aes(x = Year, y = Area_km2, color = type)) +
  geom_line() +
  scale_x_continuous(
    expand = expansion(c(0, 0.05)),
    breaks = seq(1985, 2020, 5),
    minor_breaks = seq(1985, 2021, 1)) + 
  scale_y_continuous(labels = scales::comma, limits = c(0, NA), expand = c(0, NA)) +
  theme_minimal() +
  theme(legend.position = "bottom") +
  labs(title = "",#paste(city, "Built-Up Area Exposed to River & Rainwater Flooding, 1985-2015"),
        y = bquote('Exposed'~km^2), color = "") +
  theme(axis.line = element_line(linewidth = .5, color = "black"),
        axis.title.x = element_blank())
ggsave("plots/wsf-all-flooding-plot.png", plot = all_flooding_plot, device = "png",
         width = 4, height = 3.5, units = "in", dpi = "print")
  


# Land cover pie chart
landcover <- fuzzy_read(process_output_dir, "lc.csv", read_csv, col_types = "cd") %>%
  rename(`Land Cover` = `Land Cover Type`, Count = `Pixel Count`) %>%
  filter(!is.na(`Land Cover`)) %>%
  mutate(Decimal = Count/sum(Count)) %>%
  arrange(desc(Decimal))  %>% 
  mutate(`Land Cover` = factor(`Land Cover`, levels = `Land Cover`)) %>%
  mutate(Decimal = round(Decimal, 4))

lc_colors <- c(
  "Tree cover" = "#397e48",
  "Built-up" = "#c4281b",
  "Grassland" = "#88af52",
  "Bare / sparse vegetation" = "#a59b8f",
  "Cropland" = "#e49634",
  "Permanent water bodies" = "#429bdf",
  "Shrubland" = "#dfc25a",
  "Herbaceous wetland" = "#7d87c4",
  "Mangroves" = "#00cf75")

lc_plot <- ggdonut(landcover, "Land Cover", "Count", lc_colors, "Land Cover")

lc_plot_legend <- lc_plot + theme(axis.text.x = element_blank())
ggsave("plots/wsf-landcover-legend.png", plot = lc_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")

lc_plot_plain <- lc_plot_legend + theme(legend.position = "none")
ggsave("plots/wsf-landcover-plain.png", plot = lc_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

lc_plot_labels <- lc_plot + theme(legend.position = "none")
ggsave("plots/wsf-landcover-labels.png", plot = lc_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

# Elevation pie chart
elevation <- fuzzy_read(process_output_dir, "elevation.csv", read_csv, col_types = "cd") %>%
  subset(!is.na(Bin)) %>%
  mutate(base_elevation = as.numeric(str_replace(Bin, "-.*", "")),
         Elevation = factor(Bin, levels = Bin),
         Decimal = Count/sum(Count))
elevation_names <- elevation$Elevation
elevation_colors <- c(
  "#f5c4c0",
  "#f19bb4",
  "#ec5fa1",
  "#c20b8a",
  "#762175") %>%
  setNames(elevation_names)

elevation_plot <- ggdonut(elevation, "Elevation", "Count", elevation_colors, "Elevation")
# elevation_plot + labs(fill = "Elevation (MASL)")

elevation_plot_legend <- elevation_plot + theme(axis.text.x = element_blank())
ggsave("plots/wsf-elevation-legend.png", plot = elevation_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")

elevation_plot_plain <- elevation_plot_legend + theme(legend.position = "none")
ggsave("plots/wsf-elevation-plain.png", plot = elevation_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

elevation_plot_labels <- elevation_plot + theme(legend.position = "none")
ggsave("plots/wsf-elevation-labels.png", plot = elevation_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

# Slope pie chart
slope <- fuzzy_read(process_output_dir, "slope.csv", read_csv, col_types = "cd") %>%
  subset(!is.na(Bin)) %>%
  mutate(Slope = factor(Bin, levels = Bin), Decimal = Count/sum(Count))
slope_names <- arrange(slope, Slope)$Slope
slope_colors <- c(
  "#ffffd4",
  "#fed98e",
  "#fe9929",
  "#d95f0e",
  "#993404") %>%
  setNames(slope_names)

slope_plot <- ggdonut(slope, "Slope", "Count", slope_colors, "Slope")

slope_plot_legend <- slope_plot + theme(axis.text.x = element_blank())
ggsave("plots/wsf-slope-legend.png", plot = slope_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")

slope_plot_plain <- slope_plot_legend + theme(legend.position = "none")
ggsave("plots/wsf-slope-plain.png", plot = slope_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

slope_plot_labels <- slope_plot + theme(legend.position = "none")
ggsave("plots/wsf-slope-labels.png", plot = slope_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")

# Solar availability seasonality chart
pv_path <- file.path(process_output_dir, "Bangladesh_GISdata_LTAy_YearlyMonthlyTotals_GlobalSolarAtlas-v2_AAIGRID/monthly")

files <- list.files(pv_path) %>% 
  subset(stringr::str_detect(., ".tif$|.asc$"))

monthly_pv <- lapply(files, function(f) {
  m <- f %>% substr(7, 8) %>% as.numeric()
  month_country <- terra::rast(file.path(pv_path, f))
  month <- terra::extract(month_country, aoi, include_area = T) %>% .[[2]]
  max <- max(month, na.rm = T)
  min <- min(month, na.rm = T)
  mean <- mean(month, na.rm = T)
  sum <- sum(month, na.rm = T)
  return(c(month = m, max = max, min = min, mean = mean, sum = sum))
}) %>% bind_rows()

pv_plot <- monthly_pv %>%
  mutate(daily = mean/lubridate::days_in_month(month)) %>%
  ggplot(aes(x = month, y = daily)) +
  annotate("text", x = 1, y = 4.6, label = "Excellent Conditions", vjust = 0, hjust = 0, color = "dark grey") +
  annotate("text", x = 1, y = 3.6, label = "Favorable Conditions", vjust = 0, hjust = 0, color = "dark grey") +
  geom_line() +
  geom_point() +
  scale_x_continuous(breaks = 1:12, labels = lubridate::month(1:12, label = T) %>% as.character) +
  scale_y_continuous(labels = scales::label_comma(), limits = c(0, NA), expand = expansion(mult = c(0,.05))) +
  labs(title = "Seasonal availability of solar energy",
       x = "Month", y = "Daily PV energy yield (kWh/kWp") +
  geom_hline(yintercept = c(3.5, 4.5), linetype = "dotted") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(), 
    axis.line = element_line(linewidth = .5, color = "black"),
    panel.grid.minor.x = element_blank())

ggsave("plots/monthly-pv.png", plot = pv_plot, device = "png",
       width = 4, height = 3.5, units = "in", dpi = "print")

# FWI
month_labels <- cumsum(c("Jan" = 31, "Feb" = 28, "Mar"= 31, "Apr" = 30, "May" = 31, "Jun" = 30,
  "Jul" = 31, "Aug" = 31, "Sep"= 30, "Oct" = 31, "Nov" = 30, "Dec" = 31)/7) - 31/7

fwi_file <- fuzzy_read(file.path(process_output_dir, "spatial"), "fwi.csv", paste)
fwi <- read_csv(fwi_file, col_types = "dd")

ggplot(fwi, aes(x = week, y = pctile_95)) +
  geom_line() +
  scale_x_continuous(
    breaks = month_labels, labels = names(month_labels),
    minor_breaks = NULL,
    expand = c(0,0)) +
  scale_y_continuous(expand = expansion(c(0, .1))) +    
  #   scale_color_manual(values = hues) +
  theme_minimal() +
  labs(
    title = paste("FWI in", city, "2016-2021"),
    y = "95th percentile FWI") +
  theme(
    axis.line = element_line(linewidth = .5, color = "black"),
    panel.grid.major = element_line(linewidth = .125, color = "dark gray"),
    panel.grid.minor = element_line(linewidth = .125, linetype = 2, color = "dark gray"),
    axis.title.x = element_blank())
ggsave(
  file.path("plots/nasa-fwi.png"), device = "png",
  width = 4, height = 3.5, units = "in", dpi = "print")
