# City Scan

A City Scan is a rapid geospatial assessment of a city's demographic, socioeconomic, climate, and risk conditions. It is a collection of maps and charts made from global and publicly available datasets that provide quick high-level insights into resilience-related topics for a city. These scans are especialy useful for grounding early-stage conversations in geospatial data.

This repository contains the code for two separate processes:
- **Data gathering and processing**: `backend/` hosts Python code that reads global datasets from a variety of sources, cleans them, and clips them to the city boundaries specified by the user. This code is set up to run on Google Cloud Platform as a Cloud Run Job.
- **Visualization and reporting**: `frontend/` hosts R code that reads the processed data from the backend, generates visualizations, and compiles them into a Quarto report. This code is set up to run locally or on Google Cloud Platform as a Cloud Run Job.

## Getting started

The two processes can be run by the standalone scipts `scripts/backend.sh` and `scripts/frontend.sh`: you do not need the full repository. (You can also run them in-browser on Google Cloud Platform, though this is less convenient. See docs/backend.md and docs/frontend.md for instructions on how to run in-browser.)

See [docs/setup.md](docs/setup.md) for more on the required software.

### Data gathering and processing

Requires: [gcloud](docs/setup.md#gcloud) for uploading files and executing the Job

1. Download the script `scripts/backend.sh`, if you don't have it already
2. Run it in your terminal: `bash scripts/backend.sh`
3. Follow the prompts to define city-specific inputs, choose components, and upload the city's area of interest (AOI) shapefile

For more detailed instructions, see [docs/backend.md](docs/backend.md).

### Visualization and reporting

Requires: [gcloud](docs/setup.md#gcloud) for downloading files
Recommends: for creating maps and reports, [Docker](docs/setup.md#docker) obviates need for other dependencies

1. Download the script `scripts/frontend.sh`, if you don't have it already
2. Run it in your terminal with the name of the city directory as it appears on Google Cloud Storage, e.g. `2025-04-colombia-cartagena`
   1. To create the maps using Docker, run `bash scripts/frontend.sh <city-directory> --docker`
   2. To create the maps using R locally without Docker, run `bash scripts/frontend.sh `bash scripts/frontend.sh <city-directory> --native`
   3. To simply download the files without creating maps, run `bash scripts/frontend.sh <city-directory>`
 
For more detailed instructions, see [docs/frontend.md](docs/frontend.md).

## Cloning the repository

If you do want to download the code, for contributing, repurposing, or simply tracking updates to the scripts, you can clone this repository of both processes using the following command: 

```bash
git clone --filter=blob:none https://github.com/rosemaryturtle/city-scan-automation.git
```

If git is not installed, see the GitHub's [git installation guide](https://github.com/git-guides/install-git). The flag `--filter=blob:none` reduces download size by excluding unnecessary historical items until they are needed.
