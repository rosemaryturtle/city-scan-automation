# Clean data for OJS visualization
# R port of frontend/Py/clean.py
# Converts tabular/spatial output to chart-ready CSV format
# Dependencies: dplyr, readr, tidyr, stringr, terra, lubridate (loaded via setup.R)

# Output directory - uses setup.R's tabular_dir
processed_dir <- file.path(tabular_dir, "processed")
if (!dir.exists(processed_dir)) dir.create(processed_dir, recursive = TRUE)

# =============================================================================
# Population Growth (pg.csv)
# =============================================================================
clean_pg <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  result_df <- df %>%
    arrange(Year) %>%
    transmute(
      yearName = Year,
      population = Population,
      populationGrowthPercentage = round((population - lag(population)) / lag(population) * 100, 3)
    )

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "pg.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Years covered: ", min(result_df$yearName), " - ", max(result_df$yearName))
  message("Total data points: ", nrow(result_df))
  message("Population range: ", scales::comma(min(result_df$population)), " - ", scales::comma(max(result_df$population)))

  return(result_df)
}

# =============================================================================
# Population Age Sex (pas.csv)
# =============================================================================
clean_pas <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  # Combine 0-1 and 1-4 into 0-4
  df <- df %>%
    mutate(age_group = case_when(
      age_group %in% c("0-1", "1-4") ~ "0-4",
      TRUE ~ age_group
    ))

  # Group and calculate percentages
  result_df <- df %>%
    group_by(age_group, sex) %>%
    summarize(population = sum(population), .groups = "drop") %>%
    mutate(
      ageBracket = age_group,
      sex = case_when(sex == "f" ~ "female", sex == "m" ~ "male", TRUE ~ sex),
      count = round(population, 2),
      percentage = round(population / sum(population) * 100, 7),
      yearName = 2021
    ) %>%
    select(ageBracket, sex, count, percentage, yearName)

  # Sort by age bracket
  age_order <- c("0-4", "5-9", "10-14", "15-19", "20-24", "25-29",
                 "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
                 "60-64", "65-69", "70-74", "75-79", "80+", "80")

  result_df <- result_df %>%
    mutate(age_sort = match(ageBracket, age_order)) %>%
    arrange(age_sort, sex) %>%
    select(-age_sort)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "pas.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Total population: ", scales::comma(sum(result_df$count)))
  message("Age brackets: ", n_distinct(result_df$ageBracket))
  message("Total records: ", nrow(result_df))

  return(result_df)
}

# =============================================================================
# Age Dependency Ratio (adr.csv) - based on Caroline's calculateAgeDependencyRatios
# Reads from pas.csv (already processed) to calculate dependency ratios
# =============================================================================
clean_adr <- function(input_file = NULL, output_file = NULL) {
  # Read from pas.csv by default
  if (is.null(input_file)) {
    input_file <- file.path(processed_dir, "pas.csv")
  }

  df <- read_csv(input_file, show_col_types = FALSE)

  # Sum population by age bracket (combine male/female)
  age_totals <- df %>%
    group_by(ageBracket) %>%
    summarize(population = sum(count), .groups = "drop")

  # Define age categories (matching Caroline's approach)
  youth_groups <- c("0-4", "5-9", "10-14")
  working_groups <- c("15-19", "20-24", "25-29", "30-34", "35-39",
                      "40-44", "45-49", "50-54", "55-59", "60-64")
  elderly_groups <- c("65-69", "70-74", "75-79", "80+", "80")

  # Calculate totals for each group
  youth_total <- sum(age_totals$population[age_totals$ageBracket %in% youth_groups])
  working_total <- sum(age_totals$population[age_totals$ageBracket %in% working_groups])
  elderly_total <- sum(age_totals$population[age_totals$ageBracket %in% elderly_groups])

  # Calculate dependency ratios (per 100 working-age people)
  youth_ratio <- round((youth_total / working_total) * 100)
  elderly_ratio <- round((elderly_total / working_total) * 100)
  total_ratio <- youth_ratio + elderly_ratio

  result_df <- tibble(
    youthDependencyRatio = youth_ratio,
    elderlyDependencyRatio = elderly_ratio,
    totalDependencyRatio = total_ratio,
    youthTotal = round(youth_total),
    workingAgeTotal = round(working_total),
    elderlyTotal = round(elderly_total)
  )

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "adr.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Youth dependency ratio: ", youth_ratio, " per 100 workers")
  message("Elderly dependency ratio: ", elderly_ratio, " per 100 workers")
  message("Total dependency ratio: ", total_ratio, " per 100 workers")

  return(result_df)
}

# =============================================================================
# Relative Wealth Index Area from GeoPackage (rwi_area.csv)
# =============================================================================
clean_rwi_area <- function(input_file, output_file = NULL) {
  # Read GeoPackage
  gdf <- sf::st_read(input_file, quiet = TRUE)

  # Extract RWI values
  rwi_vals <- gdf$rwi[!is.na(gdf$rwi)]

  # Define bins (5 wealth categories)
  bins <- list(
    list(range = "Least wealthy", min_val = -Inf, max_val = -0.5),
    list(range = "Less wealthy", min_val = -0.5, max_val = -0.1),
    list(range = "Average wealth", min_val = -0.1, max_val = 0.1),
    list(range = "More wealthy", min_val = 0.1, max_val = 0.5),
    list(range = "Most wealthy", min_val = 0.5, max_val = Inf)
  )

  total_count <- length(rwi_vals)

  bin_data <- lapply(bins, function(bin) {
    if (is.infinite(bin$min_val)) {
      count <- sum(rwi_vals < bin$max_val)
    } else if (is.infinite(bin$max_val)) {
      count <- sum(rwi_vals >= bin$min_val)
    } else {
      count <- sum(rwi_vals >= bin$min_val & rwi_vals < bin$max_val)
    }

    tibble(
      bin = bin$range,
      count = as.integer(count),
      percentage = round(count / total_count * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "rwi_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned RWI data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Urban Built-up Area (uba.csv)
# =============================================================================
clean_uba <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  result_df <- df %>%
    arrange(year) %>%
    mutate(
      year_seq = row_number(),
      yearName = year,
      uba = round(`cumulative sq km`, 2)
    ) %>%
    mutate(
      ubaGrowthPercentage = round((uba - lag(uba)) / lag(uba) * 100, 3)
    ) %>%
    select(year = year_seq, yearName, uba, ubaGrowthPercentage)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "uba.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Years covered: ", min(result_df$yearName), " - ", max(result_df$yearName))
  message("UBA range: ", round(min(result_df$uba), 2), " - ", round(max(result_df$uba), 2), " sq km")

  return(result_df)
}

# =============================================================================
# Urban Built-up Area from TIF (uba_area.csv)
# =============================================================================
clean_uba_area <- function(input_tif_file, output_file = NULL) {
  r <- rast(input_tif_file)
  vals <- values(r)[, 1]

  # Filter valid data (years 1900-2030)
  valid_vals <- vals[!is.na(vals) & vals >= 1900 & vals <= 2030]

  # Define bins
  bins <- list(
    list(range = "Before 1986", min_year = 0, max_year = 1985),
    list(range = "1986-1995", min_year = 1986, max_year = 1995),
    list(range = "1996-2005", min_year = 1996, max_year = 2005),
    list(range = "2006-2015", min_year = 2006, max_year = 2015)
  )

  total_pixels <- length(valid_vals)

  bin_data <- lapply(bins, function(bin) {
    if (bin$range == "Before 1986") {
      count <- sum(valid_vals <= bin$max_year)
      year_label <- "≤1985"
    } else {
      count <- sum(valid_vals >= bin$min_year & valid_vals <= bin$max_year)
      year_label <- paste0(bin$min_year, "-", bin$max_year)
    }

    tibble(
      bin = bin$range,
      year = year_label,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "uba_area.csv")
  }

  write_csv(bin_data, output_file)

  message("Cleaned UBA data saved to: ", output_file)
  message("Total pixels analyzed: ", scales::comma(sum(bin_data$count)))

  return(bin_data)
}

# =============================================================================
# Land Cover (lc.csv)
# =============================================================================
clean_lc <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  # Filter and calculate
  result_df <- df %>%
    filter(`Pixel Count` > 0, !str_detect(`Land Cover Type`, regex("total", ignore_case = TRUE))) %>%
    mutate(
      lcType = `Land Cover Type`,
      pixelCount = as.integer(round(`Pixel Count`)),
      pixelTotal = sum(`Pixel Count`),
      percentage = round(`Pixel Count` / sum(`Pixel Count`) * 100, 2)
    ) %>%
    arrange(desc(percentage)) %>%
    select(lcType, pixelCount, pixelTotal, percentage)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "lc.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Land cover types: ", nrow(result_df))
  message("Dominant: ", result_df$lcType[1], " (", result_df$percentage[1], "%)")

  return(result_df)
}

# =============================================================================
# Population Urban Growth Ratio (pug.csv)
# =============================================================================
clean_pug <- function(pg_file = NULL, uba_file = NULL, output_file = NULL) {
  chart_data_dir <- processed_dir

  if (is.null(pg_file)) pg_file <- file.path(chart_data_dir, "pg.csv")
  if (is.null(uba_file)) uba_file <- file.path(chart_data_dir, "uba.csv")

  pg_df <- read_csv(pg_file, show_col_types = FALSE)
  uba_df <- read_csv(uba_file, show_col_types = FALSE)

  pug_df <- inner_join(pg_df, uba_df, by = "yearName") %>%
    mutate(
      density = round(population / uba, 3),
      populationUrbanGrowthRatio = if_else(
        ubaGrowthPercentage != 0 & !is.na(ubaGrowthPercentage),
        round(populationGrowthPercentage / ubaGrowthPercentage, 3),
        NA_real_
      )
    ) %>%
    select(yearName, population, populationGrowthPercentage, year, uba,
           ubaGrowthPercentage, density, populationUrbanGrowthRatio)

  if (is.null(output_file)) {
    output_file <- file.path(chart_data_dir, "pug.csv")
  }

  write_csv(pug_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("Years covered: ", min(pug_df$yearName), " - ", max(pug_df$yearName))

  return(pug_df)
}

# =============================================================================
# Photovoltaic Monthly (pv.csv)
# =============================================================================
clean_pv <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  month_names <- c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

  categorize_pv <- function(maxpv) {
    case_when(
      is.na(maxpv) ~ "Unknown",
      maxpv > 4.5 ~ "Excellent",
      maxpv >= 3.5 ~ "Favorable",
      TRUE ~ "Less than Favorable"
    )
  }

  result_df <- df %>%
    arrange(month) %>%
    transmute(
      month = month,
      monthName = month_names[month],
      maxPv = round(max, 2),
      condition = categorize_pv(max)
    )

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "pv.csv")
  }

  write_csv(result_df, output_file)

  message("Cleaned data saved to: ", output_file)
  message("PV range: ", min(result_df$maxPv), " - ", max(result_df$maxPv))

  return(result_df)
}

# =============================================================================
# PV Area from TIF (pv_area.csv)
# =============================================================================
clean_pv_area <- function(input_tif_file, output_file = NULL) {
  r <- rast(input_tif_file)
  vals <- values(r)[, 1]
  valid_vals <- vals[!is.na(vals) & is.finite(vals)]

  bins <- list(
    list(range = "<3.5", condition = "Less than Favorable", min_val = 0, max_val = 3.5),
    list(range = "3.5-4.5", condition = "Favorable", min_val = 3.5, max_val = 4.5),
    list(range = ">4.5", condition = "Excellent", min_val = 4.5, max_val = Inf)
  )

  total_pixels <- length(valid_vals)

  bin_data <- lapply(bins, function(bin) {
    if (is.infinite(bin$max_val)) {
      count <- sum(valid_vals >= bin$min_val)
    } else {
      count <- sum(valid_vals >= bin$min_val & valid_vals < bin$max_val)
    }

    tibble(
      bin = bin$range,
      condition = bin$condition,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "pv_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned PV data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Air Quality Area from TIF (aq_area.csv)
# =============================================================================
clean_aq_area <- function(input_tif_file, output_file = NULL) {
  r <- rast(input_tif_file)
  vals <- values(r)[, 1]
  valid_vals <- vals[!is.na(vals) & is.finite(vals) & vals >= 0]

  bins <- list(
    list(range = "0-5", min_val = 0, max_val = 5),
    list(range = "5-10", min_val = 5, max_val = 10),
    list(range = "10-15", min_val = 10, max_val = 15),
    list(range = "15-20", min_val = 15, max_val = 20),
    list(range = "20-30", min_val = 20, max_val = 30),
    list(range = "30-40", min_val = 30, max_val = 40),
    list(range = "40-50", min_val = 40, max_val = 50),
    list(range = "50-100", min_val = 50, max_val = 100),
    list(range = "100+", min_val = 100, max_val = Inf)
  )

  total_pixels <- length(valid_vals)

  bin_data <- lapply(bins, function(bin) {
    if (is.infinite(bin$max_val)) {
      count <- sum(valid_vals >= bin$min_val)
    } else {
      count <- sum(valid_vals >= bin$min_val & valid_vals < bin$max_val)
    }

    tibble(
      bin = bin$range,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "aq_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned air quality data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Summer Surface Temperature from TIF (summer_area.csv)
# =============================================================================
clean_summer_area <- function(input_tif_file, output_file = NULL) {
  r <- rast(input_tif_file)
  vals <- values(r)[, 1]
  valid_vals <- vals[!is.na(vals) & is.finite(vals)]

  # Get min/max for dynamic binning
  min_temp <- floor(min(valid_vals) / 5) * 5
  max_temp <- ceiling(max(valid_vals) / 5) * 5

  # Create 5-degree bins
  breaks <- seq(min_temp, max_temp, by = 5)

  total_pixels <- length(valid_vals)

  bin_data <- lapply(seq_along(breaks[-length(breaks)]), function(i) {
    lower <- breaks[i]
    upper <- breaks[i + 1]

    if (i == length(breaks) - 1) {
      count <- sum(valid_vals >= lower & valid_vals <= upper)
    } else {
      count <- sum(valid_vals >= lower & valid_vals < upper)
    }

    tibble(
      bin = paste0(lower, "-", upper),
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "summer_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned summer temperature data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# NDVI Area from TIF (ndvi_area.csv)
# =============================================================================
clean_ndvi_area <- function(input_tif_file, output_file = NULL) {
  r <- rast(input_tif_file)
  vals <- values(r)[, 1]
  valid_vals <- vals[!is.na(vals) & is.finite(vals)]

  bins <- list(
    list(range = "-1-0.015", type = "Water", min_val = -1.0, max_val = 0.015),
    list(range = "0.015-0.14", type = "Built-up", min_val = 0.015, max_val = 0.14),
    list(range = "0.14-0.18", type = "Barren", min_val = 0.14, max_val = 0.18),
    list(range = "0.18-0.27", type = "Shrub and Grassland", min_val = 0.18, max_val = 0.27),
    list(range = "0.27-0.36", type = "Sparse", min_val = 0.27, max_val = 0.36),
    list(range = "0.36-1", type = "Dense", min_val = 0.36, max_val = 1.0)
  )

  total_pixels <- length(valid_vals)

  bin_data <- lapply(bins, function(bin) {
    if (bin$range == "0.36-1") {
      count <- sum(valid_vals >= bin$min_val & valid_vals <= bin$max_val)
    } else {
      count <- sum(valid_vals >= bin$min_val & valid_vals < bin$max_val)
    }

    tibble(
      bin = bin$range,
      type = bin$type,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "ndvi_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned NDVI data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Deforestation Area from TIF (deforestation_area.csv)
# =============================================================================
clean_deforestation_area <- function(forest_tif_file, deforestation_tif_file,
                                     output_file = NULL, base_year = 2000) {
  forest_r <- rast(forest_tif_file)
  deforest_r <- rast(deforestation_tif_file)

  # Resample if needed
  if (!compareGeom(forest_r, deforest_r, stopOnError = FALSE)) {
    message("Resampling deforestation to match forest...")
    deforest_r <- resample(deforest_r, forest_r, method = "near")
  }

  forest_vals <- values(forest_r)[, 1]
  deforest_vals <- values(deforest_r)[, 1]

  # Valid mask from forest
  valid_mask <- !is.na(forest_vals) & is.finite(forest_vals)
  forest_valid <- forest_vals[valid_mask]
  deforest_valid <- deforest_vals[valid_mask]
  deforest_valid[is.na(deforest_valid)] <- 0

  baseline_forest <- sum(forest_valid == 1)

  # Get unique deforestation years
  deforest_years <- sort(unique(deforest_valid[deforest_valid > 0]))

  # Build year-over-year data
  result_data <- list(tibble(
    year = base_year,
    forest_remaining = baseline_forest,
    deforested_this_year = 0,
    cumulative_deforested = 0,
    percent_forest_remaining = 100.0,
    percent_forest_lost = 0.0
  ))

  cumulative_deforested <- 0

  for (year_code in deforest_years) {
    actual_year <- base_year + as.integer(year_code)
    deforested_count <- sum(forest_valid == 1 & deforest_valid == year_code)
    cumulative_deforested <- cumulative_deforested + deforested_count

    forest_remaining <- baseline_forest - cumulative_deforested

    result_data <- c(result_data, list(tibble(
      year = actual_year,
      forest_remaining = as.integer(forest_remaining),
      deforested_this_year = as.integer(deforested_count),
      cumulative_deforested = as.integer(cumulative_deforested),
      percent_forest_remaining = round(forest_remaining / baseline_forest * 100, 2),
      percent_forest_lost = round(cumulative_deforested / baseline_forest * 100, 2)
    )))
  }

  result_df <- bind_rows(result_data)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "deforestation_area.csv")
  }

  write_csv(result_df, output_file)
  message("Cleaned deforestation data saved to: ", output_file)

  return(result_df)
}

# =============================================================================
# Flood Data (fu.csv, pu.csv, cu.csv, comb.csv)
# =============================================================================
clean_flood <- function(input_file, output_dir = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  if (is.null(output_dir)) {
    output_dir <- processed_dir
  }

  # Check for available flood types
  flood_mappings <- list(
    fluvial = list(col = "fluvial_2020", short = "fu", file = "fu.csv"),
    pluvial = list(col = "pluvial_2020", short = "pu", file = "pu.csv"),
    coastal = list(col = "coastal_2020", short = "cu", file = "cu.csv"),
    combined = list(col = "comb_2020", short = "comb", file = "comb.csv")
  )

  created_files <- c()

  for (flood_type in names(flood_mappings)) {
    mapping <- flood_mappings[[flood_type]]

    if (mapping$col %in% names(df)) {
      result_df <- df %>%
        arrange(year) %>%
        transmute(
          year = row_number(),
          yearName = year,
          !!mapping$short := round(.data[[mapping$col]], 2)
        )

      output_path <- file.path(output_dir, mapping$file)
      write_csv(result_df, output_path)
      created_files <- c(created_files, mapping$file)

      message("Created ", mapping$file, ": ", nrow(result_df), " records")
    }
  }

  message("Files created: ", paste(created_files, collapse = ", "))

  return(created_files)
}

# =============================================================================
# Elevation (e.csv)
# =============================================================================
clean_e <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  extract_elev <- function(bin_str) {
    if (str_starts(bin_str, "-")) {
      return(as.numeric(bin_str))
    } else if (str_detect(bin_str, "-")) {
      return(as.numeric(str_split(bin_str, "-")[[1]][1]))
    } else {
      return(as.numeric(bin_str))
    }
  }

  result_df <- df %>%
    filter(Count > 0, !str_detect(Bin, regex("total", ignore_case = TRUE))) %>%
    mutate(sort_val = sapply(Bin, extract_elev)) %>%
    arrange(sort_val) %>%
    mutate(
      bin = Bin,
      count = as.integer(Count),
      percentage = round(Count / sum(Count) * 100, 2)
    ) %>%
    select(bin, count, percentage)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "e.csv")
  }

  write_csv(result_df, output_file)
  message("Cleaned elevation data saved to: ", output_file)

  return(result_df)
}

# =============================================================================
# Slope (s.csv)
# =============================================================================
clean_s <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  extract_slope <- function(bin_str) {
    if (str_detect(bin_str, "-")) {
      return(as.numeric(str_split(bin_str, "-")[[1]][1]))
    } else {
      return(as.numeric(bin_str))
    }
  }

  result_df <- df %>%
    filter(Count > 0, !str_detect(Bin, regex("total", ignore_case = TRUE))) %>%
    mutate(sort_val = sapply(Bin, extract_slope)) %>%
    arrange(sort_val) %>%
    mutate(
      bin = Bin,
      count = as.integer(Count),
      percentage = round(Count / sum(Count) * 100, 2)
    ) %>%
    select(bin, count, percentage)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "s.csv")
  }

  write_csv(result_df, output_file)
  message("Cleaned slope data saved to: ", output_file)

  return(result_df)
}

# =============================================================================
# Landslide Susceptibility from TIF (ls_area.csv)
# =============================================================================
clean_ls_area <- function(input_tif_file, output_file = NULL, include_nodata = FALSE) {
  r <- rast(input_tif_file)
  vals <- as.integer(values(r)[, 1])
  valid_vals <- vals[!is.na(vals) & is.finite(vals)]

  if (!include_nodata) {
    analysis_vals <- valid_vals[valid_vals > 0]
  } else {
    analysis_vals <- valid_vals
  }

  susceptibility_mapping <- if (include_nodata) {
    list(
      `0` = list(bin = "No Data", label = "0"),
      `1` = list(bin = "Very low", label = "1"),
      `2` = list(bin = "Low", label = "2"),
      `3` = list(bin = "Medium", label = "3"),
      `4` = list(bin = "High", label = "4"),
      `5` = list(bin = "Very high", label = "5")
    )
  } else {
    list(
      `1` = list(bin = "Very low", label = "1"),
      `2` = list(bin = "Low", label = "2"),
      `3` = list(bin = "Medium", label = "3"),
      `4` = list(bin = "High", label = "4"),
      `5` = list(bin = "Very high", label = "5")
    )
  }

  total_pixels <- length(analysis_vals)

  bin_data <- lapply(names(susceptibility_mapping), function(val) {
    mapping <- susceptibility_mapping[[val]]
    count <- sum(analysis_vals == as.integer(val))

    tibble(
      bin = mapping$bin,
      susceptibility = mapping$label,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  # Sort order
  susc_order <- c("No Data", "Very low", "Low", "Medium", "High", "Very high")
  bin_data <- bin_data %>%
    mutate(sort_order = match(bin, susc_order)) %>%
    arrange(sort_order) %>%
    select(-sort_order)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "ls_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned landslide data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Earthquake Events (ee.csv)
# =============================================================================
clean_ee <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  result_df <- df %>%
    mutate(begin_year = year(ymd(BEGAN))) %>%
    filter(!is.na(begin_year)) %>%
    transmute(
      begin_year = as.integer(begin_year),
      distance = as.integer(round(distance)),
      eqMagnitude = round(eqMagnitude, 1),
      text = text,
      line1 = line1,
      line2 = line2,
      line3 = line3
    ) %>%
    arrange(begin_year)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "ee.csv")
  }

  write_csv(result_df, output_file)
  message("Cleaned earthquake data saved to: ", output_file)
  message("Events: ", nrow(result_df))
  message("Year range: ", min(result_df$begin_year), " - ", max(result_df$begin_year))

  return(result_df)
}

# =============================================================================
# Liquefaction Susceptibility from TIF (l_area.csv)
# =============================================================================
clean_l_area <- function(input_tif_file, output_file = NULL, include_nodata = FALSE) {
  # Same logic as landslide
  r <- rast(input_tif_file)
  vals <- as.integer(values(r)[, 1])
  valid_vals <- vals[!is.na(vals) & is.finite(vals)]

  if (!include_nodata) {
    analysis_vals <- valid_vals[valid_vals > 0]
  } else {
    analysis_vals <- valid_vals
  }

  susceptibility_mapping <- if (include_nodata) {
    list(
      `0` = list(bin = "No Data", label = "0"),
      `1` = list(bin = "Very low", label = "1"),
      `2` = list(bin = "Low", label = "2"),
      `3` = list(bin = "Medium", label = "3"),
      `4` = list(bin = "High", label = "4"),
      `5` = list(bin = "Very high", label = "5")
    )
  } else {
    list(
      `1` = list(bin = "Very low", label = "1"),
      `2` = list(bin = "Low", label = "2"),
      `3` = list(bin = "Medium", label = "3"),
      `4` = list(bin = "High", label = "4"),
      `5` = list(bin = "Very high", label = "5")
    )
  }

  total_pixels <- length(analysis_vals)

  bin_data <- lapply(names(susceptibility_mapping), function(val) {
    mapping <- susceptibility_mapping[[val]]
    count <- sum(analysis_vals == as.integer(val))

    tibble(
      bin = mapping$bin,
      susceptibility = mapping$label,
      count = as.integer(count),
      percentage = round(count / total_pixels * 100, 2)
    )
  }) %>% bind_rows()

  susc_order <- c("No Data", "Very low", "Low", "Medium", "High", "Very high")
  bin_data <- bin_data %>%
    mutate(sort_order = match(bin, susc_order)) %>%
    arrange(sort_order) %>%
    select(-sort_order)

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "l_area.csv")
  }

  write_csv(bin_data, output_file)
  message("Cleaned liquefaction data saved to: ", output_file)

  return(bin_data)
}

# =============================================================================
# Fire Weather Index (fwi.csv)
# =============================================================================
clean_fwi <- function(input_file, output_file = NULL) {
  df <- read_csv(input_file, show_col_types = FALSE)

  # ISO 8601 week to month mapping
  get_month_name_iso <- function(week) {
    case_when(
      week <= 4 ~ "Jan",
      week <= 9 ~ "Feb",
      week <= 13 ~ "Mar",
      week <= 17 ~ "Apr",
      week <= 22 ~ "May",
      week <= 26 ~ "Jun",
      week <= 30 ~ "Jul",
      week <= 35 ~ "Aug",
      week <= 39 ~ "Sep",
      week <= 43 ~ "Oct",
      week <= 47 ~ "Nov",
      TRUE ~ "Dec"
    )
  }

  categorize_danger <- function(fwi) {
    case_when(
      is.na(fwi) ~ "Unknown",
      fwi < 5.2 ~ "Very low",
      fwi < 11.2 ~ "Low",
      fwi < 21.3 ~ "Moderate",
      fwi < 38.0 ~ "High",
      fwi < 50.0 ~ "Very high",
      TRUE ~ "Extreme"
    )
  }

  result_df <- df %>%
    arrange(week) %>%
    transmute(
      week = week,
      monthName = get_month_name_iso(week),
      fwi = round(pctile_95, 2),
      danger = categorize_danger(pctile_95)
    )

  if (is.null(output_file)) {
    output_file <- file.path(processed_dir, "fwi.csv")
  }

  write_csv(result_df, output_file)
  message("Cleaned FWI data saved to: ", output_file)
  message("FWI range: ", min(result_df$fwi), " - ", max(result_df$fwi))

  return(result_df)
}

# =============================================================================
# Main function to clean all data
# =============================================================================
clean_all <- function() {
  # Uses global tabular_dir and spatial_dir from setup.R

  message("\n=== Cleaning data for OJS visualization ===\n")

  # Helper to find files
  find_file <- function(pattern) {
    files <- list.files(tabular_dir, pattern = pattern, full.names = TRUE)
    if (length(files) > 0) files[1] else NULL
  }

  find_tif <- function(pattern) {
    files <- list.files(spatial_dir, pattern = pattern, full.names = TRUE)
    if (length(files) > 0) files[1] else NULL
  }

  find_gpkg <- function(pattern) {
    files <- list.files(spatial_dir, pattern = paste0(pattern, "\\.gpkg$"), full.names = TRUE)
    if (length(files) > 0) files[1] else NULL
  }

  # ===================== TABULAR DATA =====================

  tryCatch({
    f <- find_file("population-growth")
    if (!is.null(f)) { message("Processing population growth..."); clean_pg(f) }
  }, error = function(e) message("Skipping pg: ", e$message))

  tryCatch({
    f <- find_file("demographics")
    if (!is.null(f)) { message("Processing demographics..."); clean_pas(f) }
  }, error = function(e) message("Skipping pas: ", e$message))

  tryCatch({
    # clean_adr reads from pas.csv (already processed above)
    message("Processing age dependency ratios...")
    clean_adr()
  }, error = function(e) message("Skipping adr: ", e$message))

  tryCatch({
    f <- find_file("wsf_stats")
    if (!is.null(f)) { message("Processing WSF stats..."); clean_uba(f) }
  }, error = function(e) message("Skipping uba: ", e$message))

  tryCatch({
    f <- find_file("_lc\\.csv")
    if (!is.null(f)) { message("Processing land cover..."); clean_lc(f) }
  }, error = function(e) message("Skipping lc: ", e$message))

  tryCatch({
    f <- find_file("monthly-pv")
    if (!is.null(f)) { message("Processing monthly PV..."); clean_pv(f) }
  }, error = function(e) message("Skipping pv: ", e$message))

  tryCatch({
    f <- find_file("flood_wsf")
    if (!is.null(f)) { message("Processing flood data..."); clean_flood(f) }
  }, error = function(e) message("Skipping flood: ", e$message))

  tryCatch({
    f <- find_file("elevation\\.csv")
    if (!is.null(f)) { message("Processing elevation..."); clean_e(f) }
  }, error = function(e) message("Skipping elevation: ", e$message))

  tryCatch({
    f <- find_file("slope\\.csv")
    if (!is.null(f)) { message("Processing slope..."); clean_s(f) }
  }, error = function(e) message("Skipping slope: ", e$message))

  tryCatch({
    f <- find_file("fwi\\.csv")
    if (!is.null(f)) { message("Processing FWI..."); clean_fwi(f) }
  }, error = function(e) message("Skipping fwi: ", e$message))

  tryCatch({
    f <- find_file("earthquake-events")
    if (!is.null(f)) { message("Processing earthquakes..."); clean_ee(f) }
  }, error = function(e) message("Skipping earthquakes: ", e$message))

  # ===================== SPATIAL DATA (TIF) =====================

  tryCatch({
    f <- find_tif("wsf.*\\.tif")
    if (!is.null(f)) { message("Processing WSF TIF..."); clean_uba_area(f) }
  }, error = function(e) message("Skipping uba_area: ", e$message))

  tryCatch({
    f <- find_tif("pv.*\\.tif|solar.*\\.tif")
    if (!is.null(f)) { message("Processing PV TIF..."); clean_pv_area(f) }
  }, error = function(e) message("Skipping pv_area: ", e$message))

  tryCatch({
    f <- find_tif("air\\.tif")
    if (!is.null(f)) { message("Processing air quality TIF..."); clean_aq_area(f) }
  }, error = function(e) message("Skipping aq_area: ", e$message))

  tryCatch({
    f <- find_tif("summer.*\\.tif|lst.*\\.tif")
    if (!is.null(f)) { message("Processing summer temperature TIF..."); clean_summer_area(f) }
  }, error = function(e) message("Skipping summer_area: ", e$message))

  tryCatch({
    f <- find_tif("ndvi.*\\.tif")
    if (!is.null(f)) { message("Processing NDVI TIF..."); clean_ndvi_area(f) }
  }, error = function(e) message("Skipping ndvi_area: ", e$message))

  tryCatch({
    forest_f <- find_tif("forest.*\\.tif")
    deforest_f <- find_tif("deforestation.*\\.tif")
    if (!is.null(forest_f) && !is.null(deforest_f)) {
      message("Processing deforestation TIFs...")
      clean_deforestation_area(forest_f, deforest_f)
    }
  }, error = function(e) message("Skipping deforestation_area: ", e$message))

  tryCatch({
    f <- find_tif("landslide\\.tif")
    if (!is.null(f)) { message("Processing landslide TIF..."); clean_ls_area(f) }
  }, error = function(e) message("Skipping ls_area: ", e$message))

  tryCatch({
    f <- find_tif("liquefaction\\.tif")
    if (!is.null(f)) { message("Processing liquefaction TIF..."); clean_l_area(f) }
  }, error = function(e) message("Skipping l_area: ", e$message))

  # ===================== SPATIAL DATA (GPKG) =====================

  tryCatch({
    f <- find_gpkg("rwi")
    if (!is.null(f)) { message("Processing RWI GeoPackage..."); clean_rwi_area(f) }
  }, error = function(e) message("Skipping rwi_area: ", e$message))

  # ===================== DERIVED DATA =====================

  # PUG requires pg and uba first
  tryCatch({
    message("Processing population-urban growth ratio...")
    clean_pug()
  }, error = function(e) message("Skipping pug: ", e$message))

  message("\n=== OJS data cleaning complete ===\n")
}

clean_all()