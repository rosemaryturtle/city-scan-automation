# City Scan Automation

This repository documents the front-end and back-end development of the City Scan Automation project, undertaken by the City Resilience Program.
The main languages used are Python and R.

## Inputs and Outputs

The inputs and outputs are located in `mnt/city-directories`.
The subdirectory `01-user-input` takes 2 input yaml files from the user, which specify the city name and AOI file path (`city_inputs.yml`), and analytical component selection (`menu.yml`).
The subdirectory `02-process-output` holds the output files from the back-end processing, which are then fed into the front-end processing.

## Back-end Processing

The back-end workflow automates the processing and clipping of global environmental and hazard datasets to the urban scale.

## Front-end Processing

The front-end workflow takes the back-end outputs and assembles them into a Quarto document, complete with a text narrative, statistical visualizations, and interactive maps.

## Workflow Improvement

One of the primary motivations for the City Scan Automation project is to drastically speed up and streamline the workflow.
The improvements can be visualized in the flow charts below:

### Original Workflow

Multi-actor, involving repetitive manual processes, high dependencies.

```mermaid
flowchart LR
	subgraph data[Data Sources]
		Fathom
		WorldPop
		WSF
		osm[OpenStreetMap]
		ox[Oxford Economics]
		citypop[CityPopulation.de]
		other[...]
	end
	other --> garrett_rasters
	subgraph Garrett
		subgraph garrett_rasters[Raster Processing]
			direction LR
			avg_rad_sum
			linfit
			nDVI
			SummerMultiYear_LST
			ForestCoverLost
			GreenSpaces
		end
	end
	subgraph tom[Tom]
		subgraph tom_rasters[Raster Processing]
			direction LR
			WSFevolution_reclass.tif
			01_population
			03_landcover
			04_elevation
			06_solar
			11_landslides
			07_air_quality
		end
		WSF --> tom_rasters
		WorldPop --> tom_rasters
		osm --> ntwrk[Network Analysis]
	end
	subgraph Andrii
		direction TB
		arc{{ArcMap Toolbox}} --> png[Map PNGs]
		Fathom --> arc
		tom_rasters --> stats[Stats]
		tom_rasters --> arc
		garrett_rasters --> arc
	end
	subgraph Ben
		stats --> rmd{{R processing}}
		rmd --> Plots
		ox --> rmd
		citypop --> rmd
	end
	Plots --> InDesign
	ntwrk --> InDesign
	png --> InDesign
	ref --> InDesign
	subgraph Writing
		rmd ----> ref[Reference Sheet]
		front[Infrastruce and Services]
		slide_text[Map & Plot Text]
	end
	front --> InDesign
	slide_text --> InDesign
```

### Proposed Workflow

Streamlined, cloud-based,automated, and more efficient.

```mermaid
flowchart LR
	subgraph data[Data Sources]
		direction LR
		Fathom
		WorldPop
		WSF
		osm[OpenStreetMap]
		ox[Oxford Economics]
		citypop[CityPopulation.de]
		other[...]
	end
	data --> rastering
	subgraph gcce[Google Cloud Compute Engine]
		rastering{{Raster Processing}}
		rastering --> TIFs
		TIFs --> mapping{{Mapmaking}}
		mapping --> PNGs
		rastering --> Stats
		PNGs --> jekyll{{Jekyll/Eleventy}}
		Stats --> jekyll
		jekyll --> html_internal[HTML Site]
	end
	html_internal[HTML Site] -.- html_external[HTML Site]
	writing{{Writing}} --- html_external[HTML Site]
```
