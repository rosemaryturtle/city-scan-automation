# Plots for LGCRRP
# 1. Standard City Scan Plots
# 2. Climate Projection Charts
# 3. Other Plots

source("R/setup.R")

# 1. Standard City Scan Plots --------------------------------------------------
source("R/population-growth.R")
source("R/urban-extent.R")
source("R/flooding.R")
source("R/landcover.R")
source("R/elevation.R")
source("R/slope.R")
source("R/solar-pv.R")
source("R/fwi.R")

# 2. Climate Projection Charts -------------------------------------------------
# Data from Climate Change Knowledge Portal
# https://climateknowledgeportal.worldbank.org
# Files are already on Google Cloud, but to download from source use
# source("R/download.R")

source("R/csdi.R")
source("R/wsdi.R")
source("R/hdtr.R") # Need to revise, maybe use different data
source("R/r20mm-r50mm.R")
# source("R/r95ptot.R")
source("R/rx5day.R") # Needs fixing
source("R/tas-txx.R")

# 3. Other Plots ---------------------------------------------------------------
# Lightning
source("R/lightning.R")
