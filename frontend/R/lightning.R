# lightning.R

# Lightning
read_csv(file.path(tabular_dir, "avg_lightning.csv")) %>%
  arrange(-avg) %>%
  rename(location = city) %>%
  mutate(
    location = ordered(location, levels = unique(.$location)),
    group = case_when(location == city ~ "focus", T ~ "other")) %>%
  ggplot() +
  geom_col(aes(x = location, y = avg, fill = group)) +
  scale_fill_manual(values = c(focus = "black", other = "darkgrey")) +
  labs(y = "Annual flash rate") +
  theme_minimal() +
  theme(legend.position = "none", axis.title.x = element_blank())
ggsave(file.path(charts_dir, "lightning-bar.png"), width = 9, height = 4)
