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

### Locally

The City Scan is a standardized process, but sometimes cities need special treatment. Running the frontend locally lets you make changes to the code, add new maps, etc. To allow for reproducability and city-specific changes, we create a copy of the frontend code and save it to the same folder as the city data. (For now, we copy rather than clone because the frontend code is in a subfolder of the repository and this clutters the city directory. At some point we may pull the frontend code into its own repository, which would allow us to clone it directly into the city directory.)

The script `scripts/frontend.sh` 
1. Copies the latest frontend code from the Github repository*
2. Downloads the city data from Google Cloud Storage
3. Runs the frontend code to create the maps and charts†

Before running, you'll need to set the name of the city directory you want to download from Google Cloud Storage. To do so, edit the `GCS_CITY_DIR` variable in `scripts/frontend.sh`. This should be the name of the directory as created by the backend Job (e.g., 2024-09-zambia-lusaka).

*To use a different branch of the frontend code, edit the `BRANCH` variable in `scripts/frontend.sh`.

†The third step uses Docker to ensure all users have the necessary dependencies. You can forgo this step (for now by commenting out the Docker section of the script), and simply `R/maps-static.R` 

Soon, we will set frontend.sh to use flags so you don't need to edit the script to run it.

## Creating the charts

## Writing City Scan text

## Assembling PDF version

### Assembling the web version

## Modifications

### Adding a new map layer

#### The map itself

#### Accompanying text
