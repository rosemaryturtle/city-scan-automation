
# Path to Application Default Credentials - the file that gcloud creates when you run gcloud auth application-default login. If you haven't authenticate your GCS, the you probably (must) need to do that first.


if (!exists("USE_GCS")) {GCS <- TRUE}

GCS_PROJECT <- "city-scan-gee-test"
GCS_BUCKET <- "crp-city-scan"
GLOBAL_DATA_BUCKET <- "city-scan-global-data"

adc_path <- path.expand("~/.config/gcloud/application_default_credentials.json")


# Debug output
message("\n=== GCS AUTH DEBUG ===")
message("USE_GCS: ", USE_GCS)
message("scan_id exists: ", exists("scan_id"))
if (exists("scan_id")) message("scan_id value: ", scan_id)
message("adc_path exists: ", file.exists(adc_path))

# If USE_GCS is true -> Authenticate & override file reading functions
if (USE_GCS && file.exists(adc_path) ){
  message("\nAuthenticating to GCS...")
  Sys.setenv(GOOGLE_APPLICATION_CREDENTIALS = adc_path, GCS_AUTH_FILE = adc_path)
  tryCatch({
      gcs_auth(token = gargle::credentials_app_default(scopes = "https://www.googleapis.com/auth/cloud-platform"))
      message("About to source gcs-overrides.R...")
      source("R/gcs-overrides.R")

      message("GCS authentication successful - override functions loaded")

        }, error = function(e) {
          USE_GCS <- FALSE
          message("GCS authentication failed: ", e$message)
          message("Falling back to using local files.")
    })
} else {
  message("\nUsing local files for data input.")
  if (!USE_GCS) message("Reason: USE_GCS is FALSE")
  if (!file.exists(adc_path)) message("Reason: adc_path does not exist")
}