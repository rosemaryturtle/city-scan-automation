download_from_aws <- function(codes) {
  system(
    glue::glue(paste0(
      "aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/",
      generate_generic_paths(), " source-data/{codes}/",
      collapse = "\n")))
}

codes <- c("tas", "txx", "wsdi", "csdi", "r20mm", "r50mm", "rx5day")

download_from_aws(codes)

# hdtr and r95ptot have different format
# hdtr
cat(
  glue::glue(
    paste(
      glue::glue(
        "aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp{scenario_numbers}/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp{scenario_numbers}_climatology_<c('median', 'p90', 'p10')>_2040-2059.nc source-data/hdtr/;"),
      collapse = "\n"),
    .open = "<", .close = ">")
)

system("
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp126/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp126_climatology_p90_2040-2059.nc source-data/hdtr/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp245/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp245_climatology_p90_2040-2059.nc source-data/hdtr/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp370/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp370_climatology_p90_2040-2059.nc source-data/hdtr/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp126/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp126_climatology_p10_2040-2059.nc source-data/hdtr/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp245/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp245_climatology_p10_2040-2059.nc source-data/hdtr/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/hdtr/ensemble-all-ssp370/climatology-hdtr-monthly-mean_cmip6-x0.25_ensemble-all-ssp370_climatology_p10_2040-2059.nc source-data/hdtr/
")

# Alternate rx5day (seasonal instead of annual)
system("
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp126/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp126_timeseries-smooth_median_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp126/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp126_timeseries-smooth_p10_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp126/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp126_timeseries-smooth_p90_2015-2100.nc source-data/rx5day/

aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp245/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp245_timeseries-smooth_median_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp245/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp245_timeseries-smooth_p10_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp245/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp245_timeseries-smooth_p90_2015-2100.nc source-data/rx5day/

aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp370/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp370_timeseries-smooth_median_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp370/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp370_timeseries-smooth_p10_2015-2100.nc source-data/rx5day/
aws s3 --region us-west-2 cp --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp370/timeseries-rx5day-seasonal-mean_cmip6-x0.25_ensemble-all-ssp370_timeseries-smooth_p90_2015-2100.nc source-data/rx5day/
")

system("
aws s3 --region us-west-2 ls --no-sign-request s3://wbg-cckp/data/cmip6-x0.25/rx5day/ensemble-all-ssp126/")

# rx5day extreme
# Formerly system("bash bash wbcckp-download.sh") (haven't tested edit)
system("bash bash wbcckp-download.sh")