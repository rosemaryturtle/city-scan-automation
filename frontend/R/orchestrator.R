# orchestrator.R

if (dir.exists("frontend")) setwd("frontend")

# 1. Spatial data processing that does not currently occur in backend
source("R/data-processing.R")
# source("R/pre-mapping.R") # Before moving here from maps-static, need to fix dependencies like aspect_buffer() in density_rast()

# 2. Non-spatial data processing for charts
# source("R/write-population.R") # Don't think we still use this

# 3. Static maps
source("R/maps-static.R")