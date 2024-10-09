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
5. [Modify the Container](#modify-the-container)
6. [Simultaneous Data Processing for Multiple Cities](#simultaneous-data-processing)
7. [Environment Variables](#environment-variables)
8. [Troubleshooting](#troubleshooting)

## Overview

This directory contains the containerized data processing pipeline used for executing jobs on **Google Cloud Run**. The pipeline automates the download, ingestion, transformation, and output of data for the City Scan. It is designed to run efficiently in a serverless environment, leveraging **Docker** for containerization.

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

If you don’t already have a repository set up, create one with the following command:

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

1. Configure **Docker** to authenticate with **Artifact Registry**:
    ```bash
    gcloud auth configure-docker <region>-docker.pkg.dev
    ```

    Example:

    ```bash
    gcloud auth configure-docker us-docker.pkg.dev
    ```

2. Build your Docker image:
    ```bash
    docker build -t <region>-docker.pkg.dev/<your-project-id>/<repository-name>/<image-name>:<tag> .
    ```

    Example:

    ```bash
    docker build -t us-docker.pkg.dev/city-scan/city-scan-data/csd:latest .
    ```

3. Push the image to **Artifact Registry**:
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
    --command <your-command> \
    --max-retries 1 \
    --timeout 1d
    ```

    Example:

    ```bash
    gcloud run jobs create csd \
    --image us-docker.pkg.dev/city-scan/city-scan-data/csd:latest \
    --region us-east4 \
    --max-retries 1 \
    --timeout 1d
    ```

2. You can then execute the job using:
    ```
    gcloud run jobs execute <your-job-name> --region <your-region>
    ```

    Example:

    ```
    gcloud run jobs execute csd --region us-east4
    ```

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

## Simultaneous Data Processing for Multiple Cities



## Environment Variables

No Cloud Run job-level environment variables are needed to run the Cloud Run job at this point. The environment variables are currently stored in `config.yml`. If this changes in the future, the readme will be updated accordingly.

## Troubleshooting

- **Issues**: As the pipeline is still in the testing phase, unexpected issues may arise and cause the Cloud Run job to fail. In that case, please note the execution ID of the job and contact Rui Su, who will examine the logs, help resolve the issues, and improve the pipeline for the future.
- **Logs**: Logs for the Cloud Run service can be accessed via [Google Cloud Console > Logging](https://console.cloud.google.com/logs).