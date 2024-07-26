# pre-mapping.R

# Combine infrastructure base points
fire_points <- fuzzy_read(spatial_dir, "osm_fire") %>% mutate(Feature = "Fire station")
police_points <- fuzzy_read(spatial_dir, "osm_police") %>% mutate(Feature = "Police station")
health_points <- fuzzy_read(spatial_dir, "osm_health") %>% mutate(Feature = "School")
school_points <- fuzzy_read(spatial_dir, "osm_school") %>% mutate(Feature = "Hospital or clinic")
infrastructure_points <- rbind(fire_points, police_points, health_points, school_points)
writeVector(infrastructure_points, filename = file.path(spatial_dir, "infrastructure.gpkg"), overwrite = T)

# Combine flooding
combined_flooding <- str_subset(list.files(spatial_dir, full.names = T), "(fluvial|pluvial|coastal)_2020.tif$") %>%
  lapply(rast) %>% 
  reduce(\(x, y) max(x, y, na.rm = T))
writeRaster(combined_flooding, filename = file.path(spatial_dir, paste0(city, "_combined_flooding_2020.tif")), overwrite = T)

# Road network centrality
roads <- fuzzy_read(spatial_dir, "road_network/.*edges.shp$") %>%
  mutate(
    primary = highway %in% c("motorway", "trunk", "primary"),
    road_type = case_when(primary ~ "Primary", T ~ "Secondary"),
    edge_centr = edge_centr * 100) %>%
  select(edge_centr, road_type)
writeVector(roads, filename = file.path(spatial_dir, "edges-edit.gpkg"), overwrite = T)
