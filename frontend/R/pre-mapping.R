# pre-mapping.R

# Combine infrastructure base points
combine_infrastructure_points <- function() {
  health_points <- fuzzy_read(spatial_dir, "osm_health") %>% mutate(Feature = "School") %>% tryCatch(error = \(e) {warning(e); return(NULL)})
  school_points <- fuzzy_read(spatial_dir, "osm_school") %>% mutate(Feature = "Hospital or clinic") %>% tryCatch(error = \(e) {warning(e); return(NULL)})
  fire_points <- fuzzy_read(spatial_dir, "osm_fire") %>% mutate(Feature = "Fire station") %>% tryCatch(error = \(e) {warning(e); return(NULL)})
  police_points <- fuzzy_read(spatial_dir, "osm_police") %>% mutate(Feature = "Police station") %>% tryCatch(error = \(e) {warning(e); return(NULL)})
  rbind_if_non_null <- \(...) Reduce(rbind, unlist(list(...)))
  infrastructure_points <- rbind_if_non_null(health_points, school_points, fire_points, police_points)
  if (!is.null(infrastructure_points)) writeVector(infrastructure_points, filename = file.path(spatial_dir, "infrastructure.gpkg"), overwrite = T)
}
combine_infrastructure_points()

combine_flood_types <- function() {
  flood_files <- str_subset(list.files(spatial_dir, full.names = T), "(fluvial|pluvial|coastal)_2020.tif$")
  if (length(flood_files) > 0) {
    combined_flooding <- flood_files %>%
      lapply(rast) %>% 
      reduce(\(x, y) max(x, y, na.rm = T))
    writeRaster(combined_flooding, filename = file.path(spatial_dir, paste0(city, "_combined_flooding_2020.tif")), overwrite = T)
  }
}
combine_flood_types()

# Road network centrality
assign_road_types <- function() {
  roads <- fuzzy_read(spatial_dir, "nodes_and_edges", layer = "edges") %>%
    mutate(
      primary = highway %in% c("motorway", "trunk", "primary"),
      road_type = case_when(primary ~ "Primary", T ~ "Secondary"),
      edge_centrality = edge_centrality * 100) %>%
    select(edge_centrality, road_type)
  writeVector(roads, filename = file.path(spatial_dir, "edges-edit.gpkg"), overwrite = T)
}
assign_road_types()
