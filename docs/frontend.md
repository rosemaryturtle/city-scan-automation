# Visualization and Reporting

## Creating the maps

Once the data  has all been [processed](backend.md), the next step is to create the maps and charts that will be included in the City Scan report. This is done using R code in the `frontend/` directory. these maps can be made locally or on Google Cloud (though the web version must be made locally).

<!-- The City Scan exists in two formats, as an interactive web site and as a slide deck, and the maps for eac -->

### On Google Cloud

To run on Google Cloud, you simply need to execute the `frontend` Job. You can execute the Job from the browser, but (once you've set it up), it's more convenient to use `gcloud` from the command line:

```sh
gcloud beta run jobs execute $JOB \
	--update-env-vars CITY_DIR=<city-directory>
```

where `<city-directory>` is the name of the city's directory on Google Cloud (e.g., 2024-09-zambia-lusaka), as created by the backend Job.

This method works well for standardized maps, but it still requires you to download the maps in order to assemble the Scan. Because of this, it can make more sense to run the frontend fully locally.

### Locally, with scripts/frontend.sh

The City Scan is a standardized process, but sometimes cities need special treatment. Running the frontend locally lets you make changes to the code, add new maps, etc. To allow for reproducability and city-specific changes, we create a copy of the frontend code and save it to the same folder as the city data. (For now, we copy rather than clone because the frontend code is in a subfolder of the repository and this clutters the city directory. At some point we may pull the frontend code into its own repository, which would allow us to clone it directly into the city directory.)

The script `scripts/frontend.sh` does both of the steps:

1. Copies the latest frontend code from the Github repository (to use a different repository branch, edit the `BRANCH` variable in `scripts/frontend.sh`)
2. Downloads the city data from Google Cloud Storage

To run, you'll need to have the name of the city directory on Google Cloud Storage, which is the name of the folder created by the backend Job (e.g., 2024-09-zambia-lusaka):

```bash
bash scripts/frontend.sh <city-directory>
```

This will create a directory called `mnt/` in your working directory and, inside of that directory, the city directory with the latest frontend code and the city data. We recommend always running the script from the same location, so that all city directories are housed in the same `mnt/` folder.

You can also use the script to create the maps using the latest frontend code from the repository. You can either use Docker or run the R code natively. With Docker, you don't need any other dependencies installed – they are all included in the Docker container. To run the maps using Docker, run `bash scripts/frontend.sh <city-directory> --docker`. To run the maps natively, use `bash scripts/frontend.sh <city-directory> --native`. 

Currently, `frontend.sh` is set up to create the static maps but not the PDF or HTML reports.

### Creating the maps manually

If you already have a local city directory with the frontend code and city data, you can run the maps directly using , you can run the R code directly either from a shell terminal or from R. This approach is useful if you want to edit the R code or add new maps. For either approach, you'll need to be working from the city directory, which contains the R code and the city data.

Rscript:

```bash
cd <path/to/city/directory>
Rscript R/maps-static.R
```

R:

```r
setwd("<path/to/city/directory>")
source("R/maps-static.R")
```

## Creating the charts

## Writing City Scan text

## Assembling PDF version

### Assembling the web version

## Modifications

### Adding a new map layer

#### The map itself

#### Accompanying text
