# Plots for City Scan

source("R/setup.R", local = T)

# 1. Standard City Scan Plots --------------------------------------------------

# tryCatch(source("R/population-growth.R", local = T), error = \(e) warning(e))
tryCatch(source("R/urban-extent.R", local = T), error = \(e) warning(e))
tryCatch(source("R/flooding.R", local = T), error = \(e) warning(e))
tryCatch(source("R/landcover.R", local = T), error = \(e) warning(e))
tryCatch(source("R/elevation.R", local = T), error = \(e) warning(e))
tryCatch(source("R/slope.R", local = T), error = \(e) warning(e))
tryCatch(source("R/solar-pv.R", local = T), error = \(e) warning(e))
tryCatch(source("R/fwi.R", local = T), error = \(e) warning(e))
tryCatch(source("R/age-sex-distribution.R", local = T), error = \(e) warning(e))
tryCatch(source("R/flood-archive.R", local = T), error = \(e) warning(e))
tryCatch(source("R/earthquakes.R", local = T), error = \(e) warning(e))
