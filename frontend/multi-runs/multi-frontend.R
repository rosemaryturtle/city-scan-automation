# Running frontend for multiple cities

# 2 approaches: shared code vs city-specific code ------------------------------

# For both, first efine cities to run on
scan_ids <- c("2025-08-benin-cotonou", "2025-08-benin-djougou", "2025-08-benin-porto_novo", "2025-08-chad-ndjamena", "2025-08-democratic_republic_of_the_congo-boma")
# You can also do this programmatically, such as by reading what is in mnt/

# Helper time logging functions used by both -----------------------------------
.GlobalEnv$task_times <- data.frame(start_time = as.POSIXct(character(0)), end_time = as.POSIXct(character(0)))
lap_start <- function(x) .GlobalEnv$task_times[x,] <- c(Sys.time(), NA)
lap_print <- function(x, message = NULL) {
  # browser()
  .GlobalEnv$task_times[x,2] <- Sys.time()
  duration <- .GlobalEnv$task_times[x,2] - .GlobalEnv$task_times[x,1]
  output <- paste0(
    ifelse(!is.null(message), paste0(message, ": "), ""),
    round(duration,2), " ", units(duration))
  message(output)
}

##### Approach 1: city-specific code -------------------------------------------
# Uses scripts/frontend.sh in loop

# Loop through each city using scripts/frontend.sh
# - frontend.sh by default only downloads data and clones repository
# - it can be modified to run maps-static.R with flags:
#   --native creates static maps using local environment
#   --docker creates static maps using Docker container
# - however, if you want to make any edits first, then delay
walk(scan_ids, \(x) system2("bash", glue("scripts/frontend.sh {x} --native")))

# Alternatively, to separately download and code running, use
# multi-runs/multi-download.R or
# walk(scan_ids, \(x) system2("bash", glue("scripts/frontend.sh {x}")))
# and then loop through each city (though setting the working directory like this
# can get a bit hairy with errors):
wd <- getwd()
scan_ids %>%
  walk(\(x) {
    setwd(wd)
    message(glue("{x}..."))
    setwd(file.path("mnt", x))
    source("R/maps-static.R", local = T)
    message(glue("Finished: {x}"))
  })

##### Approach 2: shared code --------------------------------------------------

#### 2.a. Simple loop
# For a small batch of cities, the loop is very easy, and similar to approach 1:
setwd("frontend")
scan_ids %>%
  walk(\(x) {
    lap_start(x)
    message(glue("{x}..."))
    writeLines(file.path("mnt", x), "city-dir.txt")
    source("R/maps-static.R", local = T)
    # If, instead, you want to create transparencies:
    # source("R/transparencies.R", local = T)
    lap_print(x, glue("**** Finished! ({x}"))
  })

#### 2.b. Parallel processing

# Define cities to run ----------------------------------------------------------
# You can skip this part and define scan_ids however you prefer, but this was
# helpful for keeping track of progress when running 200 cities 

# First, find status of all possible maps for each city based on filenames.csv
filenames <- read_csv("frontend/source/filenames.csv")
list_possible_maps <- \() {
  list.files("mnt") %>%
    str_subset("^2025-08") %>%
    lapply(\(x) mutate(filenames, folder = x)) %>%
    bind_rows() %>%
    mutate(
      city = str_extract(folder, "(?<=2025-0\\d-philippines-)[^/]*"),
      path = glue("mnt/{folder}/03-render-output/{city}/{filename}.png"),
      exists = file.exists(path))
}

ready_to_run <- list_possible_maps() %>%
  filter(!exists) %>%
  count(folder) %>%
  # Only rerun if at least 60 maps are missing
  filter(n >= 30) %>%
  mutate(ready = file.exists(file.path("mnt", folder, "READY.txt"))) %>%
  filter(ready) %>%
  mutate(area = sapply(file.path("mnt", folder, "01-user-input/AOI"), \(x) {
      if (!file.exists(x)) return(NA)
      expanse(vect(x), unit = "km")
      })) %>%
  # Prioritize largest cities for greater efficiency
  arrange(desc(area))

# Run for all cities -----------------------------------------------------------

scan_ids <- ready_to_run$folder

# Running multiple cities in parallel
# - city-dir.txt can't be used, as many cities would need it at once, so you
#   must comment out "city_dir <- readLines("city-dir.txt")" in R/setup.R
# - READY.txt, IN-PROCESS.txt, DONE.txt are helpful for tracking progress in
#   parallel runs; READY.txt was created by multi-runs/multi-download.R
parallel::mclapply(scan_ids, \(x) {
  if ("frontend" %in% list.files()) setwd("frontend")
  city_dir <- file.path("mnt", x)
  # Only run if READY.txt exists and neither IN-PROCESS.txt nor DONE.txt exist
  if (!file.exists(file.path(city_dir, "READY.txt"))) return(NULL)
  if (file.exists(file.path(city_dir, "IN-PROCESS.txt"))) return(NULL)
  if (file.exists(file.path(city_dir, "DONE.txt"))) return(NULL)
  lap_start(x)
  message(glue("{x}..."))
  file.rename(
    file.path("mnt", x, "READY.txt"),
    file.path("mnt", x, "IN-PROCESS.txt"))
  tryCatch({
    source("R/maps-static.R", local = T)
    file.rename(
      file.path("mnt", x, "IN-PROCESS.txt"),
      file.path("mnt", x, "DONE.txt"))
  },
    error = function(e) {
      message(glue("Error in {x}: {e$message}"))
    file.rename(
      file.path("mnt", x, "IN-PROCESS.txt"),
      file.path("mnt", x, "ERROR.txt"))
    })
  lap_print(x, glue("**** Finished! {x}"))
})

# Alt maps-static.R ------------------------------------------------------------
# For the Philippines Atlas we had to rerun some maps, with modifications. It
# was easiest to create adjusted copies of maps-static.R for this purpose.
lapply((ready_to_run$folder, \(x) {
  if ("frontend" %in% list.files()) setwd("frontend")
  city_dir <- file.path("mnt", x)
  lap_start(x)
  message(glue("{x}..."))
  tryCatch({
    source("R/maps-static-veg.R", local = T)
    lap_print(x, glue("**** Finished! {x}"))
  },
    error = function(e) {
      message(glue("Error in {x}: {e$message}"))
      lap_print(x, glue("**** Error! {x}"))
    })
})
