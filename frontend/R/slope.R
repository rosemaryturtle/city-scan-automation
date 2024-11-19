# Plotting slope pie chart
slope <- fuzzy_read(process_output_dir, "slope.csv", read_csv, col_types = "cd") %>%
  subset(!is.na(Bin)) %>%
  mutate(
    Bin = paste0(Bin, "°"),
    Slope = factor(Bin, levels = Bin), Decimal = Count/sum(Count))
slope_names <- arrange(slope, Slope)$Slope
slope_colors <- colorRampPalette(prepare_parameters("slope")$palette)(5) %>%
  setNames(slope_names)

slope_plot <- ggdonut(slope, "Slope", "Count", slope_colors, "Slope")
slope_plot_legend <- slope_plot + theme(axis.text.x = element_blank())
ggsave(file.path(charts_dir, "wsf-slope-legend.png"), plot = slope_plot_legend, device = "png",
       width = 8, height = 5, units = "in", dpi = "print")
slope_plot_plain <- slope_plot_legend + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-slope-plain.png"), plot = slope_plot_plain, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
slope_plot_labels <- slope_plot + theme(legend.position = "none")
ggsave(file.path(charts_dir, "wsf-slope-labels.png"), plot = slope_plot_labels, device = "png",
       width = 5, height = 5, units = "in", dpi = "print")
