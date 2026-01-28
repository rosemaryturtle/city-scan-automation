# User inputs for making the R Notebook, so that the calculations sheet only needs code changes
# GCS Configuration ------------------------------------------------------------ 
USE_GCS <- TRUE
# City Configuration ------------------------------------------------------------

# crp-city-scan/2025-11-mauritania-nouakchott
city <- "Nouakchott"
country <- "Mauritania"
run_date <- "2025-11"

scan_id <- paste(run_date, tolower(country), tolower(city), sep = "-")

map_file_prefices <- c(paste0("'", city, "_'"), paste0("'", city, "_'")) # Include single quotations around prefices

# Benchmark Configuration ------------------------------------------------------------

# Selecting Benchmark cities (additional cities will be chosen via Oxford Economics and nearby_countries_string)
# bm_cities_manual <- c("Dakar", "Tambacounda", "Diourbel", "Thiès", "Ziguinchor","Saint-Louis", "Kaolack","Mbacké", "Touba", "Mbour", "Saly Portudal", "Louga", "Kolda", "Kédougou", "Richard-Toll", "Dagana")

nearby_countries_string <- "ivory coast|ghana|nigeria|gambia|mauritania|guinea|sierra leone"

bm_cities_manual <- c("Nouakchott", "Nouadhibou", "Rosso", "Kaédi", "Kiffa","Zouérat", "Atar", "Sélibaby", "Néma", "Aleg")

# nearby_countries_string <-"senegal|mali|algeria|morocco|western sahara|guinea|sierra leone|ivory coast|burkina faso"

