# City Scan Data Processing Pipeline as a Google Cloud Run Job

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Directory Structure](#directory-structure)
4. [Initial Build and Deploy](#initial-build-and-deploy)
    - [Authenticate with Google Cloud](#authenticate-with-google-cloud)
    - [Create an Artifact Registry Repository](#create-an-artifact-registry-repository)
    - [Build and Push the Docker Image to Artifact Registry](#build-and-push-the-docker-image-to-artifact-registry)
    - [Deploy the Docker Image to Cloud Run Job](#deploy-the-docker-image-to-cloud-run-job)
    - [Execute the Cloud Run Job](#execute-the-cloud-run-job)
5. [Access the Data Outputs](#access-the-data-outputs)
6. [Modify the Container](#modify-the-container)
7. [Simultaneous Data Processing for Multiple Cities](#simultaneous-data-processing)
8. [Environment Variables](#environment-variables)
9. [Troubleshooting](#troubleshooting)

## Overview

This directory contains the containerized data processing pipeline used for executing jobs on **Google Cloud Run**. The pipeline automates the download, ingestion, transformation, and output of data for the City Scan. It is designed to run efficiently in a serverless environment, leveraging **Docker** for containerization. The inputs and outputs for the pipeline are stored in Google Cloud Storage.

## Prerequisites

Before you can run this pipeline, ensure you have the following installed:

- **Docker**: [Installation Guide](https://docs.docker.com/get-docker/)
- **Google Cloud SDK**: [Installation Guide](https://cloud.google.com/sdk/docs/install)
- **Python 3.10**: [Download](https://www.python.org/downloads/)

## Directory Structure

```
/backend-gcp
│   Dockerfile
│
│   config.yaml
│
│   main.py
│   accessibility.py
│   burned_area.py
│   elevation.py
│   fathom.py
│   fwi.py
│   gee_fun.py
│   landcover_burnability.py
│   raster_pro.py
│   road_network.py
│   rwi.py
│   utils.py
│   wsf.py
│
│   requirements.txt
│   README.md
│
│   fathom_aws_credentials.yml
│
└───/GOSTnets
│   └─── ...
```

- **Dockerfile**: Defines the environment used for running the job.
- **config.yaml**: Configures the environment variables.
- **main.py**: The entry point for executing the pipeline.
- **Other Python scripts**: Processes various data inputs.
- **requirements.txt**: Lists Python dependencies.
- **fathom_aws_credentials.yml**: Stores the credentials (`aws_access_key_id` and `aws_secret_access_key`) for accessing Fathom flood data from the WBG AWS bucket.
- **/GOSTnets**: Package developed by the World Bank GOST team, used for network analysis.

## Initial Build and Deploy

### Authenticate with Google Cloud

1. Authenticate with Google Cloud and set your project:
    ```bash
    gcloud auth login
    gcloud config set project <your-project-id>
    ```

    Example:

     ```bash
    gcloud auth login
    gcloud config set project city-scan
    ```

2. Enable the Artifact Registry and Cloud Run APIs if they are not already enabled:
    ```bash
    gcloud services enable artifactregistry.googleapis.com run.googleapis.com
    ```

### Create an Artifact Registry Repository

If you do not already have a repository set up, create one with the following command:

```bash
gcloud artifacts repositories create <repository-name> \
    --repository-format=docker \
    --location=<region> \
    --description="Repository description"
```

Example:

```bash
gcloud artifacts repositories create city-scan-data \
    --repository-format=docker \
    --location=us \
    --description="City Scan data processing repository"
```

### Build and Push the Docker Image to Artifact Registry

1. Modify the `cloud` section of `config.yaml` to match your Google Cloud Storage setup. Alternatively, set up your Cloud Storage buckets and directories to match the defaults in `config.yaml`:

    - `data_bucket`: name of the bucket that contains the global datasets
    - `bucket`: name of the bucket for storing user inputs and data outputs
    - `input_dir`: name of the directory where the user uploads the inputs
    - `output_dir`: name of the directory where the data outputs are stored

2. Configure **Docker** to authenticate with **Artifact Registry**:
    ```bash
    gcloud auth configure-docker <region>-docker.pkg.dev
    ```

    Example:

    ```bash
    gcloud auth configure-docker us-docker.pkg.dev
    ```

3. Build your Docker image:
    ```bash
    docker build -t <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag> .
    ```

    Example:

    ```bash
    docker build -t us-docker.pkg.dev/city-scan/city-scan-data/csd:latest .
    ```

4. Push the image to **Artifact Registry**:
    ```bash
    docker push <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag>
    ```

    Example:

    ```bash
    docker push us-docker.pkg.dev/city-scan/city-scan-data/csd:latest
    ```

### Deploy the Docker Image to Cloud Run Job

1. Deploy the job to **Cloud Run Jobs** using the following command:
    ```bash
    gcloud run jobs create <your-job-name> \
    --image <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag> \
    --region <your-region> \
    --max-retries 1 \
    --timeout 1d \
    --cpu 8 \
    --memory 32Gi
    ```

    Example:

    ```bash
    gcloud run jobs create csd \
    --image us-docker.pkg.dev/city-scan/city-scan-data/csd:latest \
    --region us-east4 \
    --max-retries 1 \
    --timeout 1d \
    --cpu 8 \
    --memory 32Gi
    ```

### Execute the Cloud Run Job

1. Upload your inputs to the directory specified in the `cloud` section of `config.yaml`, under `bucket` > `input_dir`. The required inputs are:

    - **city_inputs.yml**: Specifies the city name, country name, the name of the Area of Interest (AOI) shapefile, as well as parameters for the data processing.
    - **global inputs.yml**: Lists the data sources, which generally remain the same across City Scan iterations, but can be modified to take in alternate/local datasets. If the user chooses to provide their own dataset, the data must be uploaded to the data bucket under the same Google Cloud project, as specified in the `cloud` section of `config.yaml`, under `data_bucket`.
    - **menu.yml**: Specifies which components of the data processing to run, which allows the user to generate a subset of the City Scan data outputs if the full set is not needed.
    - **AOI shapefile**: The entire shapefile must be uploaded to a subdirectory named `AOI/` within the input directory. The AOI must be a polygon shapefile (i.e., no lines or points accepted) that does not exceed 1,000 square kilometers. It can be of any projection.

2. You can then execute the job using:
    ```
    gcloud run jobs execute <your-job-name> --region <your-region>
    ```

    Example:

    ```
    gcloud run jobs execute csd --region us-east4
    ```

## Access the Data Outputs

To maintain clean organization of the outputs, the Cloud Run job automatically creates a city directory in the Cloud Storage bucket specified in `config.yaml`, consisting of the date and city name (e.g., `2024-09-indonesia-banda_neira`). Within this directory, two subdirectories are created:

- The input subdirectory (as specified in `input_dir` of `config.yaml`; defaults to `01-user-input`) contains a copy of the user inputs provided for the job execution
- The output subdirectory (as specified in `output_dir` of `config.yaml`; defaults to `02-process-output`) contains the data outputs

To access the data outputs, simply download the files from the output subdirectory of the city directory.

## Modify the Container

This containerized pipeline is intended to be flexible and adaptable toward your own use. After modifying the pipeline, simply rebuild the Docker image and repush it to the Artifact Registry, in three quick steps:

1. Rebuild your Docker image under the same name:
    ```bash
    docker build -t <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag> .
    ```

    Example:

    ```bash
    docker build -t us-docker.pkg.dev/city-scan/city-scan-data/csd:latest .
    ```

2. Push the new image to **Artifact Registry**:
    ```bash
    docker push <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag>
    ```

    Example:

    ```bash
    docker push us-docker.pkg.dev/city-scan/city-scan-data/csd:latest
    ```

3. You can then execute the job using:
    ```
    gcloud run jobs execute <your-job-name> --region <your-region>
    ```

    Example:

    ```
    gcloud run jobs execute csd --region us-east4
    ```

If you need support adapting the data processing pipeline, please contact Rui Su to discuss your needs and potential solutions.

## Simultaneous Data Processing for Multiple Cities

Each execution of the Cloud Run job can only process one city, but the job can have multiple simultaneous executions, which allows for simultaneous data processing for multiple cities. To do so, follow these steps:

1. Upload the user inputs for one city and execute the Cloud Run job (see [Execute the Cloud Run Job](#execute-the-cloud-run-job) for more details).

2. Once the job starts executing, check the Cloud Storage bucket (`config.yaml` > `cloud` > `bucket`) and make sure that the city directory has been created.

3. The creation of the city directory means that the user inputs have been read by the Cloud Run job and will no longer be needed. Therefore, the user can now upload a new set of user inputs for the next city, overwriting the existing files, and execute the Cloud Run job again. This will create a new execution running in parallel with the previous one(s). The same computational resources will be provisioned for each execution, so each new simultaneous execution will not slow down the other one(s).

## Environment Variables

No Cloud Run job-level environment variables are needed to run the Cloud Run job at this point. The environment variables are currently stored in `config.yaml`. If this changes in the future, the readme will be updated accordingly.

## Troubleshooting

- **Issues**: As the pipeline is still in the testing phase, unexpected issues may arise and cause the Cloud Run job to fail. In that case, please note the execution ID of the job and contact Rui Su, who will examine the logs, help resolve the issues, and improve the pipeline for the future.
- **Logs**: Logs for the Cloud Run job can be accessed via [Google Cloud Console > Logging](https://console.cloud.google.com/logs).