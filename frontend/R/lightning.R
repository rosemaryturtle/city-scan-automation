# lightning.R

# Lightning
readr::read_csv("/Users/bennotkin/Documents/world-bank/crp/city-scans/city-scan-automation/mnt/2024-06-bangladesh-cumilla/02-process-output/spatial/avg_lightning.csv") %>%
# read_csv(file.path(spatial_dir, "avg_lightning.csv")) %>%
  arrange(-avg) %>%
  mutate(
    city = ordered(city, levels = unique(.$city)),
    group = case_when(city == "Cumilla" ~ "focus", T ~ "other")) %>%
  ggplot() +
  geom_col(aes(x = city, y = avg, fill = group)) +
  labs(y = "Daily flash rate") +
  theme_minimal() +
  theme(legend.position = "none", axis.title.x = element_blank())
ggsave("plots/lightning-bar.png", width = 9, height = 4)
