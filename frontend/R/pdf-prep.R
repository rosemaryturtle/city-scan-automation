# Prepare pdf.html for vivliostyle
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 3) {
  stop("Usage: Rscript pdf-prep.R <input_file> <output_file> <css_file>")
}

input_file <- args[1]
output_file <- args[2]
css_file <- args[3]

source("R/fns.R")
# Maybe also drop the CSS from prepare_html as I can add it with vivliostyle?

for (file in c(input_file, css_file)) {
  if (!file.exists(file)) {
    stop(paste("File not found:", file))
  }
}
prepare_html(input_file, output_file, css_file)
