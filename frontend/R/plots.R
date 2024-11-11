# Plots for City Scan

source("R/setup.R")

# 1. Standard City Scan Plots --------------------------------------------------

# tryCatch(source("R/population-growth.R"), error = \(e) warning(e))
tryCatch(source("R/urban-extent.R"), error = \(e) warning(e))
tryCatch(source("R/flooding.R"), error = \(e) warning(e))
tryCatch(source("R/landcover.R"), error = \(e) warning(e))
tryCatch(source("R/elevation.R"), error = \(e) warning(e))
tryCatch(source("R/slope.R"), error = \(e) warning(e))
tryCatch(source("R/solar-pv.R"), error = \(e) warning(e))
tryCatch(source("R/fwi.R"), error = \(e) warning(e))