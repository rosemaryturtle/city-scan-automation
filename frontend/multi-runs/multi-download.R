# multi-download.R
# Download files from GCS to local mnt/ folder for frontend use
# -------------------------------------------------------------
#
# Main functions:
# - Identifies city scan runs and missing PNGs for a given country and month.
# - Downloads all files for all cities using gcloud and a frontend shell script.
# - Compares local files to GCS files, downloading only those that are new or updated online.
# - Excludes national maps from download (Luzon, Mindanao, Visayas).
# - Uses parallel processing for efficient file transfer.
#
# Requirements: gcloud CLI, R packages (readr, dplyr, stringr, glue, lubridate, parallel),
# and project-specific scripts and CSVs.
# -------------------------------------------------------------


country <- "philippines"
yearmonth <- "2025-08"

if ("frontend" %in% list.files()) setwd("frontend")
source("R/setup.R")
setwd("..")

# Table of missing PNGs
filenames <- read_csv("frontend/source/filenames.csv", col_types = "cc")
list_possible_maps <- \() {
  list.files("mnt") %>%
    str_subset("^2025-08") %>%
    # str_subset("2025-07", negate = TRUE) %>%
    lapply(\(x) mutate(filenames, folder = x)) %>%
    bind_rows() %>%
    mutate(
      city = str_extract(folder, glue("(?<=2025-0\\d-{country}-)[^/]*")),
      path = glue("mnt/{folder}/03-render-output/{city}/{filename}.png"),
      exists = file.exists(path))
}

## Download all files for all cities -------------------------------------------
runs <- system(intern = T,
  glue("gcloud storage ls 'gs://crp-city-scan/2025-0*-{country}-*'")) %>%
  str_extract(glue("2025-0\\d-{country}-[^/]*")) %>%
  unique()

runs %>%
  walk(\(x) {
    # When running for the Philippines, I commented out the part of frontend.sh
    # that asked if you wanted to overwrite the existing code
    if (system2("bash", glue("scripts/frontend.sh {x}")) == 0) {
      # To allow for parallel processing, READY.txt file tells run-frontend.R
      # that the folder is ready
      system2("touch", file.path("mnt", x, "READY.txt"))
    }
  })

# Download updated files only --------------------------------------------------
# See which local files are older than online GCS files
recent_gcs_files <- system(glue(
  "gcloud storage ls -l 'gs://crp-city-scan/{yearmonth}-{country}-*/02-process-output/spatial/'"),
  intern = TRUE)
gcs_files <- recent_gcs_files %>%
  trimws() %>%
   str_split_fixed("  \\s*", n = 3) %>%
   as_tibble(.name_repair = \(x) c("no", "gcs_time", "gcs_path")) %>%
   mutate(
    gcs_time = as.POSIXct(gcs_time, format = "%Y-%m-%dT%H:%M:%S", tz = "UTC"),
    gcs_time = lubridate::with_tz(gcs_time, "America/New_York"),
    folder = str_extract(gcs_path, "2025-\\d\\d-[^/]+"),
    file = basename(gcs_path)) %>%
    filter(!is.na(gcs_time))
local_files <- list.files("mnt", recursive = TRUE, full.names = TRUE) %>%
  str_subset("/spatial/") %>%
  tibble(
    local_path = ., folder = str_extract(., "2025-\\d\\d-[^/]+"), file = basename(.),
    local_mtime = lubridate::force_tz(file.mtime(.), "America/New_York"))
files_comp <- full_join(local_files, gcs_files, by = c("folder", "file")) %>%
  filter(str_detect(folder, "2025-08"))

files_comp %>% filter(is.na(local_mtime)) %>%
  count(folder) %>%
  arrange(desc(n))
files_comp %>% filter(gcs_time > local_mtime) %>%
  count(folder) %>%
  arrange(desc(n))

files_comp %>% filter(gcs_time > local_mtime) %>%
  mutate(
    city = str_extract(folder, glue("(?<=2025-0\\d-{country}-)[^/]*")),
    filestring = str_replace(file, city, "")) %>%
  count(filestring) %>%
  arrange(desc(n))

# Download files that are newer (or only) online
files_comp %>% filter(is.na(local_mtime) | gcs_time > local_mtime) %>%
  # Ignore national maps, at least for now
  filter(folder %ni% c("2025-08-philippines-luzon", "2025-08-philippines-mindanao", "2025-08-philippines-visayas"))
start <- Sys.time()
files_comp %>% filter(is.na(local_mtime) | gcs_time > local_mtime) %>%
  # Ignore national maps, at least for now
  filter(folder %ni% c("2025-08-philippines-luzon", "2025-08-philippines-mindanao", "2025-08-philippines-visayas")) %>%
  group_by(folder) %>%
  mutate(destination = file.path("mnt", folder, "02-process-output/spatial")) %>%
  summarize(n = n(), files_concat = paste(glue("gs://crp-city-scan/{folder}/02-process-output/spatial/{file}"), collapse = " "), destination = destination[1]) %>%
  mutate(cmd = glue("gcloud storage cp {files_concat} {destination}")) %>%
  pull(cmd) %>%
  parallel::mclapply(\(x) system(x))
Sys.time() - start
