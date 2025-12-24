# There is also a philippines cloud-runs.R file which might actually be better suited for generic use? learn from both

# Run Cloud Run jobs for each AOI
librarian::shelf(tidyr, terra, tidyterra, stringr, purrr, dplyr, glue)
`%ni%` <- Negate(`%in%`)

# Read city_inputs.yml as a template
city_inputs <- yaml::read_yaml("gcs-user-input/city_inputs.yml")

# Requires uploading AOI shapefiles to GCS manually for now
# TASK: automate, would also be easier if backend could read other vector formats

# Function to run a city on Google Cloud Run; regions alternated to distribute load
# Takes dataframe with columns for 'city', 'aoi', 'yearmonth' (e.g., `runs` above)
# Updates and uploads city_inputs 
run_on_cloud <- function(x, job = "csb", regions = c("us-central1", "us-south1", "us-east1")) {
  counter <- 0
  apply(x, 1, \(x) {
    if (!all(are_jobs_started(job, regions))) {
      cat("Previous job is yet to complete first task. It could be just starting, or it could have failed with no successful tasks.\n")
      choice <- menu(c("Proceed (may override existing job)", "Exit"), title = "Do you want to proceed?")
      if (choice == 2) stop("User chose to stop waiting.")
    }
    counter <<- counter + 1
    city_inputs$city_name <- x[["city"]]
    city_inputs$AOI_shp_name <- x[["aoi"]]
    # city_inputs$prev_run_date <- x[["yearmonth"]]
    yaml::write_yaml(city_inputs, file.path("gcs-user-input", paste0("city_inputs-", x[["city"]], ".yml")))
    system("gcloud storage cp gcs-user-input/menu.yml gs://crp-city-scan/01-user-input/menu.yml")
    system(paste0("gcloud storage cp gcs-user-input/city_inputs-", x[['city']], ".yml gs://crp-city-scan/01-user-input/city_inputs.yml"))
    # I should add the same check as below to ensure a job is not already running
    # if (counter %% 2 == 0) region <- "us-central1" else region <- "us-south1"
    region <- regions[(counter - 1) %% length(regions) + 1]
    print(glue::glue("Starting job for {x[['city']]} in region {region}"))
    system(glue::glue("gcloud run jobs execute {job} --region={region}"))
    # wait 20 seconds for the job to complete
    started <- 0
    # To avoiding overriding previous job's city_inputs.yml, wait until previous job has started
    while(!all(started)) {
      started <- are_jobs_started(job, regions)
      if (all(started)) break
      print("Previous job is yet to complete first task. Waiting to not override.")
      Sys.sleep(20)
    }
  })
}

are_jobs_started <- function(job = "csb", regions) {
  unlist(lapply(regions, \(r) {
    system(glue::glue("gcloud run jobs executions list --job={job} --region={r} --limit=1 --format=\"value(COMPLETE)\""), intern = TRUE) %>%
      str_extract("^\\d+") %>% as.numeric()
  })) >= 1
}

##### Define which cities to run -----------------------------------------------

# run_on_cloud() requires a dataframe with columns city, aoi, yearmonth
# We can define this manually, e.g., below
runs <- tibble::tribble(
  ~city,                    ~aoi,   ~yearmonth,
  "Taytay-Rizal", "Taytay-Rizal",    "2025-08",
  "Kalibo-Aklan", "Kalibo-Aklan",         NULL,
)

# or use folders in mnt/ if they already exist
# Outputs tibble with folder name, yearmonth, city name and AOI file name
# runs <- list.files("mnt") %>%
#   tibble(gcs = ., yearmonth = str_extract(., "2025-0\\d"), city = str_extract(., "(?<=2025-0\\d-).*")) %>%
#   filter(!is.na(city)) %>%
#   apply(1, simplify = F, \(row) {
#     row["city"] <- yaml::read_yaml(file.path("mnt", row["gcs"], "01-user-input/city_inputs.yml"))$city_name
#     row["aoi"] <- yaml::read_yaml(file.path("mnt", row["gcs"], "01-user-input/city_inputs.yml"))$AOI_shp_name
#     row
#   }) %>% bind_rows()

#### Run selected cities on cloud ----------------------------------------------

runs %>% 
  filter(city == "Matam") %>%
  run_on_cloud()

#### Helpers -------------------------------------------------------------------

# See what has already been run, useful for filtering `runs` above 
already <- system("gcloud storage ls gs://crp-city-scan", intern = TRUE) %>%
  basename() %>% str_subset("2025-0\\d-senegal") %>%
  str_extract("(?<=2025-0\\d-senegal-).*")
