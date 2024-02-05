# Load Packages

library(readr)
library(magrittr)
library(dplyr)
library(sf)
library(terra)
library(ggplot2)
library(xml2)
library(rvest)
library(tidyterra)

# Set parameters
aoi <- vect("C:/Users/Owner/Documents/Career/World Bank/CRP/Armenia & Georgia/shapefile/goris.shp") %>% project("EPSG:4326")
fwi_directory <- "D:/World Bank/CRP/data/NASA FWI/" # Include final forward slash
dates <- as.Date("2016-01-01"):as.Date("2021-12-31") %>% as.Date(origin = as.Date("1970-01-01")) # We have data for 2016-01-01 through 2022-09-04

# Extract AOI-specific data
extract_aoi <- function(aoi, dates) {
  extent <- ext(aoi) %>% extend(2)
  cord <- dates %>% # cord is a bad fire pun
    lapply(function(date) {
      file_name <- paste0(fwi_directory, "FWI.GEOS-5.Daily.Default.", date %>% stringr::str_replace_all("-", ""), ".tif")
      # path <- paste0(fwi_directory, file_name)
      if (file.exists(file_name)) {
        # Read file
        fwi <- terra::rast(file_name)
        crs(fwi) <- "epsg:4326"
        names(fwi) <- stringr::str_replace(names(fwi), ".*_", "")
        fwi_crop <- terra::crop(fwi, extent, extend = T)
        output <- list(date = date, fwi_raster = fwi_crop)      
        return(output)
      } else {
        warning(paste("No file exists for", date)) 
        return(NA)
      }
    })
  cord <- subset(cord, !is.na(cord))
  return(cord)
}

cord_to_df <- function(cord) {
  df <- lapply(cord, function(item) {
    fwi_crop_df <- values(item$fwi_raster$FWI) %>% as_tibble()
    fwi_crop_df$date <- item$date
    return(fwi_crop_df)
  }) %>% bind_rows()
  return(df)
}

cord <- extract_aoi(aoi, dates)
cord_df <- cord_to_df(cord)

write_csv(cord_df, 'output/goris_fwi.csv')

# TIFF of 5th hottest day
cord_raster <- lapply(cord, \(i) i$fwi_raster$FWI)
q99_raster <- do.call(c, cord_raster) %>% quantile(.986, na.rm = T)

writeRaster(q99_raster, filename = 'output/goris_fwi.tif', 
            overwrite = T)

# Plot FWI over year (line chart)
week_95th <- cord_df %>%
  filter(!is.na(FWI)) %>%
  mutate(
    year = ordered(lubridate::year(date)),
    month = lubridate::month(date),
    week = lubridate::week(date),
    yday = lubridate::yday(date),
    ) %>%
{  bind_rows(
    summarize(., .by = c(week, year), q90 = quantile(FWI, .95)),
    summarize(., .by = c(week), q90 = quantile(FWI, .9), year = "All")
  ) } %>%
  mutate(year = ordered(year, levels = c(2016:2023, "All")))

month_labels <- cumsum(c("Jan" = 31, "Feb" = 28, "Mar"= 31, "Apr" = 30, "May" = 31, "Jun" = 30,
  "Jul" = 31, "Aug" = 31, "Sep"= 30, "Oct" = 31, "Nov" = 30, "Dec" = 31)/7) - 31/7

ggplot(week_95th, aes(x = week, y = q90, color = year)) +
  # geom_line(data = week_95th %>% filter(year != "All"), alpha = 0.5) +
  geom_line(data = week_95th %>% filter(year == "All"), color = "black", linewidth = 2) +
  scale_x_continuous(breaks = month_labels, labels = names(month_labels), minor_breaks = NULL,
                     expand = c(0,0)) +
  scale_y_continuous(expand = expansion(c(0, .1))) +    
  #   scale_color_manual(values = hues) +
  theme_minimal() +
  labs(title = "FWI in Goris",
       y = "95th percentile FWI", x = "Date") +
  theme(axis.line = element_line(linewidth = .5, color = "black"),
        panel.grid.major = element_line(linewidth = .125, color = "dark gray"),
        panel.grid.minor = element_line(linewidth = .125, linetype = 2, color = "dark gray"),)
ggsave("C:/Users/Owner/Documents/Career/World Bank/CRP/Armenia & Georgia/Goris/fwi.png", device = "png",
             width = 4, height = 3.5, units = "in", dpi = "print")
