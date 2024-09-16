# Download CCKP Data

# Download tas, txx, wsdi, csdi, r20mm, r50mm
codes <- c("tas", "txx", "wsdi", "csdi", "r20mm", "r50mm")
scenario_numbers <- c(126, 245, 370)

# To see the available files, use this, selectively removing elements following
# a slash to "ascend" the bucket. The terminal / is necessary.
# system("aws s3 --region us-west-2 ls --no-sign-request --human-readable s3://wbg-cckp/data/cmip6-x0.25/csdi/ensemble-all-ssp126/")

generate_generic_paths <- function() {
    statless_paths <- paste0(
        "cmip6-x0.25/{codes}/ensemble-all-ssp", scenario_numbers,
        "/timeseries-{codes}-annual-mean_cmip6-x0.25_ensemble-all-ssp", scenario_numbers,
        "_timeseries-smooth_")
  yearless_paths <- unlist(lapply(statless_paths, \(x) paste0(x, c("median", "p10", "p90"))))
  cmip6_paths <- paste0(yearless_paths, "_2015-2100.nc")

  era5_paths <- "era5-x0.25/{codes}/era5-x0.25-historical/timeseries-{codes}-annual-mean_era5-x0.25_era5-x0.25-historical_timeseries_mean_1950-2022.nc"

  paths <- c(cmip6_paths, era5_paths)
  return(paths)
}
download_from_aws <- function(codes) {
  system(
    glue::glue(paste0(
      "aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/",
      generate_generic_paths(), " source-data/{codes}/",
      collapse = "\n")))
}


download_from_aws(codes)

# hdtr and rx5day have different format

# Download hdtr
system("
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp126/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp126_climatology_p90_2040-2059.nc source-data/hdtr/
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp245/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp245_climatology_p90_2040-2059.nc source-data/hdtr/
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp370/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp370_climatology_p90_2040-2059.nc source-data/hdtr/
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp126/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp126_climatology_p10_2040-2059.nc source-data/hdtr/
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp245/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp245_climatology_p10_2040-2059.nc source-data/hdtr/
  aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp370/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp370_climatology_p10_2040-2059.nc source-data/hdtr/
")

# Download rx5day extreme
# Formerly system("bash bash wbcckp-download.sh") (haven't tested edit)
system("bash wbcckp-download.sh")