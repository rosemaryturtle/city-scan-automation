# Data Gathering and Processing <!-- omit in toc -->

This document describes how to run the data gathering and processing code for the City Scan project. It covers how to run the code on Google Cloud Platform, how to prepare city-specific files, and how to modify the data processing code.

## Contents <!-- omit in toc -->

- [Running on Google Cloud Platform](#running-on-google-cloud-platform)
  - [In browser](#in-browser)
    - [Prepare city-specific files](#prepare-city-specific-files)
    - [Upload the files](#upload-the-files)
    - [Execute the Job](#execute-the-job)
  - [From the command line](#from-the-command-line)
  - [From the command line, step by step](#from-the-command-line-step-by-step)
    - [Prepare city-specific files](#prepare-city-specific-files-1)
    - [Upload the files](#upload-the-files-1)
    - [Execute the Job](#execute-the-job-1)
    - [Download the outputs](#download-the-outputs)
- [Modifying the data processing code](#modifying-the-data-processing-code)

## Running on Google Cloud Platform

The backend code is set up to run as a Cloud Run Job on Google Cloud Platform (GCP). (_Task: revise main.py, etc. so it can also run locally._) Because of this, we don't need this repository to run the code. Instead, we can run it directly on Google Cloud Platform. We can either run it in-browser using the GCP Console or from the command line. The command line requires a little more setup but is much more convenient once setup, and is especially helpful when running multiple jobs.

> [!NOTE]  
> Both methods require Google Cloud access. If you don't have access, please write Ben Notkin to get set up. For instructions on how to give someone access, see [docs/google-cloud-access.md](google-cloud-access.md).

Whether running in-browser or from the command line, we need to tell the Job details about what we want. We need to specify the city, the boundaries to use for that city (optional), and which layers to include in the scan. For this we use two YAML files (`city_inputs.yml`, `menu.yml`), and a shapefile. (_Task: allow for any vector file format._)

- `city_inputs.yml` contains all city-specific information, including the city name and the path to the optionally provided shapefile; it also includes other options such as which OSM features to include, such as the parameters for the flood analysis.
- `menu.yml` defines which components to run in the Job. (Multiple jobs can be run for the same city, with different components turned on or off, though some components are interdependent.)
- A shapefile defining the analysis's boundaries or _area of interest_ (AOI). If this is not provided, the Job will use default boundaries from GHSL's Urban Centre Database or OpenStreetMap.

Templates for the two YAML files are provided at … (_TASK: Create a templates directory with these files, or decide a different place for them._)

To run the Job, we must provide these two or three files to Google Cloud, and then execute the Job. For instructions on how to do this in-browser or from the command line, see below.

### In browser

#### Prepare city-specific files

1. Edit `city_inputs.yml` and `menu.yml`
2. (Optional) Find or create AOI shapefile (for help with this, see [Finding an AOI](finding-aoi.md))

The AOI shapefile is optional because if it is not included, the Job will use default boundaries from GHSL's Urban Centre Database or OpenStreetMap based on the city name. Beware, however, that these areas, though, can be quite large and also wrong (such as when there are multiple cities with the same name – we do not yet allow for specification by country.) (_Task: allow for specification by country, probably via country name -> iso code.)

#### Upload the files

3. Visit [Google Cloud Storage](https://console.cloud.google.com/storage/browser/crp-city-scan/01-user-input) for the crp-city-scan bucket
4. Upload `city_inputs.yml` and `menu.yml` to the 01-user-input folder in the crp-city-scan bucket\* 
5. Upload the AOI shapefile (and all accompanying files, such as .cpg, .dbf, .prj, .shp, and .shx) to the AOI folder within 01-user-input\*

\*There are many folders called `01-user-input` in the crp-city-scan bucket, as one is created for each city run by Google Cloud. Upload your files to the top-level `01-user-input` folder, not to one for a specific city.

#### Execute the Job

6. Visit [Google Cloud Run Jobs](https://console.cloud.google.com/run/jobs) for the city-scan project
7. Folow the link for one of the jobs named `csb` (typically the most recent one, unless you're running multiple jobs at once)
8. Click "Execute" near the top of the page
 
The job will automatically create a folder in the crp-city-scan bucket for your city, such as 2024-09-zambia-lusaka. Once you see this folder, you can safely upload the next set of city inputs and start a new execution.

To use these outputs, you can download them from the bucket or [run the frontend job](TK). Downloading is very tedious from the browser (you must download one file at a time, and the filenames all change), so we recommend using the command line instead. You can do this manually or, even, easier, by using the interactive script `scripts/frontend.sh` to download the files and run the frontend Job. (_Task: add instructions for running the frontend.sh script._) 

### From the command line

To run from the command line, you will need to have the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed. Slightly simpler instructions are [here](https://cloud.google.com/sdk/docs/downloads-interactive). Once it is installed, you will need to authenticate and set the project.

(For all installations and dependencies, refer to setup instructions at [docs/setup.md](setup.md).)

```bash
gcloud auth login
gcloud config set project city-scan
```

The easiest way to run the Job from the command line is to use interactive script `scripts/backend.sh`. This script will let you download the most recent `city_inputs.yml` and `menu.yml` files, prompt you to edit them, upload them to Google Cloud, and execute the Job.

To use, run `bash scripts/backend.sh` from the repository's root directory, and follow the prompts. The script will create a new directory called `gcs-user-input`. Use this directory, and AOI/ within it, for the YAML files and the shapefiles. This directory is also where the script will download the YAML files if you request them.

### From the command line, step by step

Alternatively, you can run the Job `gcloud` commands more directly.

#### Prepare city-specific files

1. Edit `city_inputs.yml` and `menu.yml`
2. (Optional) Find or create AOI shapefile (for help with this, see [Finding an AOI](finding-aoi.md))

#### Upload the files

3. Run the following, replacing the the paths with the actual paths to your files:
   
```bash
gcloud storage path/to/menu.yml path/to/city_inputs.yml \
  gs://crp-city-scan/01-user-input
gcloud storage cp path/to/aoi-file.shp gs://crp-city-scan/01-user-input/AOI
```

#### Execute the Job

4. Run the following

```bash
gcloud run jobs execute csb
```

The job will automatically create a folder in the crp-city-scan bucket for your city, such as 2024-09-zambia-lusaka. Once you see this folder, you can safely upload the next set of city inputs and start a new execution.

Once the Job is complete, you can download its inputs and outputs using gcloud. Usually we do this as part of running the frontend Job (see [Running the frontend Job](frontend.md)), but you can also do it manually.

#### Download the outputs
 
Once the Job is complete, you can run the frontend Job to create the maps and other outputs. See [Running the frontend Job](frontend.md) for instructions on how to do this. Below, though are instructions for downloading the outputs manually.

To download everything from the Job, use the following command, replacing `<city-directory>` with the name of the city's directory on Google Cloud (e.g., 2024-09-zambia-lusaka) and `<local-directory>` with the directory you want to download to:

```bash
gcloud storage cp -R gs://crp-city-scan/<city-directory> <local-directory>
```

If you want to download only the outputs, you can use the following command instead:

```bash
gcloud storage cp -R gs://crp-city-scan/<city-directory>/02-process-output <local-directory>
```

## Modifying the data processing code

Say you want to change how a data set is processed or add a new data set, what do you need to do? The data collection and processing code lives in `backend/` and is run with the `main.py` script. Most data sets have their own Python module in `backend/`, though some are grouped together.

To change how an existing data set is processed, you will need to modify the relevant module in `backend/`.

To add a new data set, you will need to 
1. create a new module in `backend/` for the data set;
2. add the module to `main.py` as a new task or in an existing task; and
3. add the module to `menu.yml` so users can select it.

After these three steps, you will need to update the Google Cloud Run Job. To do so, you'll need to rebuild and push the Docker container. For more information on working with the Docker container and Google Cloud platform, see [backend/README.md](/backend/README.md).

(_Task: backend and frontend containers should ideally be built the same way._)

For more information on the backend structure

_Task: write an explainer of what tasks are, why they are used (parallelization), and how to add a new task._

_Task: expand on each of these steps. For example, what should the module look like? What are standard parameters? What are existing tools in aoi_helper.py or utils.py that should be used? Are there pre-defined path variables that should be used?_
