# Plotting land cover pie chart
landcover <- fuzzy_read(tabular_dir, "lc.csv", read_csv, col_types = "cd") %>%
  rename(`Land Cover` = `Land Cover Type`, Count = `Pixel Count`) %>%
  filter(!is.na(`Land Cover`)) %>%
  mutate(Decimal = Count/sum(Count)) %>%
  arrange(desc(Decimal))  %>% 
  mutate(`Land Cover` = factor(`Land Cover`, levels = `Land Cover`)) %>%
  mutate(Decimal = round(Decimal, 4))

lc_colors <- layer_params$land_cover$palette %>%
  setNames(layer_params$land_cover$labels)

lc_plot <- ggdonut(landcover, "Land Cover", "Count", lc_colors, "Land Cover")
lc_plot_legend <- lc_plot + theme(axis.text.x = element_blank())
ggsave(file.path(charts_dir, "wsf-landcover-legend.png"), plot = lc_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")
lc_plot_plain <- lc_plot_legend + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-landcover-plain.png"), plot = lc_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
lc_plot_labels <- lc_plot + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-landcover-labels.png"), plot = lc_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
