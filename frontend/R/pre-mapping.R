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

# Combine school zones
schools_800 <- fuzzy_read(spatial_dir, "schools_800", FUN = vect)
schools_1600 <- fuzzy_read(spatial_dir, "schools_1600", FUN = vect)
schools_2400 <- fuzzy_read(spatial_dir, "schools_2400", FUN = vect)
schools_2400_only <- erase(schools_2400, schools_1600)
schools_1600_only <- erase(schools_1600, schools_800)
school_zones <- reduce(c(schools_800, schools_1600_only, schools_2400_only), rbind) %>%
  select(-level_1, -nodez)
writeVector(school_zones, filename = file.path(spatial_dir, "school-journeys.gpkg"), overwrite = T)
school_points <- fuzzy_read(spatial_dir, "schools$", FUN = vect) %>%
  # rename(School = amenity)
  mutate(Feature = "School")
writeVector(school_points, filename = file.path(spatial_dir, "school-points.gpkg"), overwrite = T)

# Combine health zones
health_1000 <- fuzzy_read(spatial_dir, "health_1000", FUN = vect)
health_2000 <- fuzzy_read(spatial_dir, "health_2000", FUN = vect)
health_3000 <- fuzzy_read(spatial_dir, "health_3000", FUN = vect)
health_3000_only <- erase(health_3000, health_2000)
health_2000_only <- erase(health_2000, health_1000)
health_zones <- reduce(c(health_1000, health_2000_only, health_3000_only), rbind) %>%
  select(-level_1, -nodez)
writeVector(health_zones, filename = file.path(spatial_dir, "health-journeys.gpkg"), overwrite = T)
health_points <- fuzzy_read(spatial_dir, "health$", FUN = vect) %>%
  # rename(`Health Facility` = amenity)
  mutate(Feature = "Health facility")
writeVector(health_points, filename = file.path(spatial_dir, "health-points.gpkg"), overwrite = T)
