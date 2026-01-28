# <!-- COMMENTED OUT - InDesign workflow not needed for mnt/ structure
# ```{r}
# if (!any(str_detect(list.files("scan/Links"), "_admin.png"))) {
#   list.files("Maps") %>%
#     lapply(function(file) {
#       file.copy(paste0("Maps/", file), "scan/Links")
#     }) %>% invisible()
# }

# rename_command <- paste0("Rscript --vanilla rename-generic.R '", getwd(), "/scan/Links' ", map_file_prefices)
# for (x in rename_command) system(x)
# # system(paste0("magick ", getwd(), "/scan/Links/map_network_plot.png -trim -fuzz 30% -fill white -opaque '#111111' ", getwd(), "/scan/Links/map_network_plot_white.png"))

# # This checks which maps are missing. I could do the same for plots, but would need to be at end of document
# slide_list <- read_csv("slide-list.csv", col_types = "cccddcc")
# maps <- list.files("scan/links") %>% .[str_detect(., "^map_")]
# occasional_maps <- filter(slide_list, filename %in% maps & conditions == "occasional" & type == "map")

# if (nrow(occasional_maps > 0)) {
#   print_text("These maps exist. Make sure they are included in the InDesign.")
#   occasional_maps %>% select(slide, filename, warning_text)
# }

# missing_maps <- filter(slide_list, filename %ni% maps & type == "map" & slide != "Not shown")
# # Use the following to make a warning instead of printing a table
# # mutate(
# #   slide_number = paste(section, section_order, sep = "."),
# #   # gap = 27 - nchar(filename),
# #   slide = leading_zeros(substr(slide, 1, 10), length = 10, filler = " ", trailing = T),
# #   filename = leading_zeros(filename, length = 28, filler = " ", trailing = T),
# #   warning_message = paste0(slide, ": ", filename, warning_text),
# #   .keep = "none")
# # warning(paste0("missing maps:\n", paste(missing_maps$warning_message, collapse = "\n")))

# if (nrow(missing_maps) > 0) {
#   print_text("The following maps are not included. Should they be?")
#   missing_maps %>% select(slide, filename, warning_text)
# }
# ```
# -->