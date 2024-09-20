# Post-render script to duplicate index.html and create a print version
# (This isn't yet called by anything)

file.copy("index.html", "pdf.html", overwrite = T)

# Web version
#  - Remove PNG maps
#  - Remove PNG plots
html <- readLines("index.html") %>%
  # Delete PNG maps from web version
  .[-str_which(., "static-maps/")]
  # When we've included PNG plots to index.qmd, remove those as well
cat(html, sep = "\n", file = "index-web.html")

# PDF version
# pdf <- readLines("pdf.html")
# stylesheet_indices <- str_which(pdf, "<link href=.*stylesheet")
# # Add custom CSS sheet
# pdf[stylesheet_indices[1]] <- '  <link href="source/custom.css" rel="stylesheet">'
# # Remove other stylesheets
# if (length(stylesheet_indices) > 1) pdf <- pdf[-stylesheet_indices[-1]]
# cat(pdf, sep = "\n", file = "pdf.html")

library(rvest)
library(xml2)
pdf <- read_html("pdf.html")
stylesheet_nodes <- html_elements(pdf, "link[rel=stylesheet]")
xml_attr(stylesheet_nodes[1], "href") <- "source/custom.css"
xml2::xml_remove(stylesheet_nodes[-1])
setup_node <- html_elements(pdf, ".setup")
xml2::xml_remove(setup_node)
# Do I want to remove all div.cell? NO
# xml2::xml_remove(html_nodes(pdf, ".cell"))
ojs_script_node <- html_element(pdf, "script[src='index_files/libs/quarto-ojs/quarto-ojs-runtime.js']")
xml2::xml_remove(ojs_script_node)
module_nodes <- html_elements(pdf, "script[type=module]")
xml2::xml_remove(module_nodes)
ojs_module_node <- html_element(pdf, "script[type=ojs-module-contents]")
xml2::xml_remove(ojs_module_node)
js_nodes <- html_elements(pdf, "script[type='text/javascript']")
xml2::xml_remove(js_nodes)
json_node <- html_elements(pdf, "script[type='application/json']")
xml2::xml_remove(json_node)
nav_node <- html_element(pdf, ".navigation")
xml2::xml_remove(nav_node)
xml2::xml_remove(html_nodes(pdf, "script#quarto-html-after-body"))
write_html(pdf, "pdf.html")

# system("vivliostyle preview pdf.html")
system("vivliostyle build pdf.html")
