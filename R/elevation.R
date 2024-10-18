# Plotting elevation pie chart
elevation <- fuzzy_read(process_output_dir, "elevation.csv", read_csv, col_types = "cd") %>%
  subset(!is.na(Bin)) %>%
  mutate(base_elevation = as.numeric(str_replace(Bin, "-.*", "")),
         Elevation = factor(Bin, levels = Bin),
         Decimal = Count/sum(Count))
elevation_names <- elevation$Elevation

elevation_colors <- c(
  "#f5c4c0", #F5C4C0" "#DCA3B1" "#C283A2" "#A96393" "#904384" "#762175
  "#f19bb4",
  "#ec5fa1",
  "#c20b8a",
  "#762175") %>%
  setNames(elevation_names)

elevation_plot <- ggdonut(elevation, "Elevation", "Count", elevation_colors, "Elevation")
# elevation_plot + labs(fill = "Elevation (MASL)")
elevation_plot_legend <- elevation_plot + theme(axis.text.x = element_blank())
ggsave(file.path(charts_dir, "wsf-elevation-legend.png"), plot = elevation_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")
elevation_plot_plain <- elevation_plot_legend + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-elevation-plain.png"), plot = elevation_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
elevation_plot_labels <- elevation_plot + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-elevation-labels.png"), plot = elevation_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
