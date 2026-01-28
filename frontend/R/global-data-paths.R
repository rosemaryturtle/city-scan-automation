
# change before running if GCS not authenticated!
local_materials <- "../../../03-multi-scan-materials/" 

if (USE_GCS && exists(GLOBAL_DATA_BUCKET)) {
    # GCS paths - relative to city-scan-global-data bucket

    oxford_file <- "oxford-economics/Oxford Global Cities Data.csv"
    oxford_areas_file <- "oxford-economics/oxford-economics-areas.csv"
    oxford_location_file <- "oxford-economics/oxford-locations.csv"

    undata_file <- "Population/undata-pop.csv"  # add Population/
    koeppen_file <- "climate-classification/Koeppen-Geiger-ASCII.csv" 

    flood_archive_file <- "flood-archive/FloodArchive_region.shp"
    cyclone_archive_file <- "IBTrACS-tropical-cyclones/IBTrACS.since1980.list.v04r00.lines.shp"

    # pv_path <- "World_PVOUT_GISdata_LTAm_AvgDailyTotals_GlobalSolarAtlas-v2_AAIGRID/"
    pv_path <- "globalsolar/PVOUT-monthly.tif"
    
    fwi_directory <- "NASA FWI/"

    wb_counties <- "wb_countries_admin0_10m/WB_countries_Admin0_10m.shp"

    } else {

    oxford_file <- file.path(local_materials,  "Oxford Global Cities Data.csv")
    oxford_areas_file <- file.path(local_materials, "oxford-economics-areas.csv")
    oxford_location_file <- file.path(local_materials, "oxford-locations.csv")

    undata_file <-  file.path(local_materials, "undata-pop.csv")
    koeppen_file <- file.path(local_materials, "Koeppen-Geiger-ASCII.csv")

    flood_archive_file <- file.path(local_materials, "flood-archive", "FloodArchive_region.shp")

    cyclone_archive_file <- file.path(local_materials, "IBTrACS-tropical-cyclones", "IBTrACS.since1980.list.v04r00.lines.shp")

    pv_path <- paste0(local_materials, "/World_PVOUT_GISdata_LTAm_AvgDailyTotals_GlobalSolarAtlas-v2_AAIGRID.nosync/")

    fwi_directory <- paste0(local_materials, "wildfire-exploration.nosync/source-data.nosync/nasa-fwi/")

    wb_counties <- file.path(local_materials, "WB_countries_Admin0_10m.shp")


}