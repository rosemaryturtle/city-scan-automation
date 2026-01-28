#!/usr/bin/env Rscript
# Run the script with $ Rscript --vanilla rename-generic.R "<PATH TO DIRECTORY>" "<City>_"
args <- commandArgs(trailingOnly=TRUE)

if (length(args)!=2) {
  stop("Script requires two arguments:\n  1: Path to directory.\n  2: String for city name, to be replaced.", call.=FALSE)
}

dir <- args[1]
city_string <- args[2]

files <- list.files(dir)
files <- files[grep(city_string, files)]
for (f in files) {
    old_name <- paste0(dir, "/", f)
    new_name <- paste0(dir, "/", gsub(paste0(city_string, "|", tolower(city_string), "(AOI_)?"), "map_", f))
    file.rename(old_name, new_name)
    # print(paste(old_name, "→", new_name))
}
