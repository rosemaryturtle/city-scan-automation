# Use the GDAL image with Python 3.9 and GDAL 3.7.2
# FROM ghcr.io/osgeo/gdal:ubuntu-small-3.7.2-py3.9
FROM python:3.8-slim

# For R & Docker primer, see http://jsta.github.io/r-docker-tutorial/

# Install R base image from Rocker (builds on Ubuntu 22.04 LTS)
# https://github.com/rocker-org/rocker-versioned2/blob/master/dockdockeerfiles/Dockerfile_r-ver_4.0.2 
# ARG R_VERSION=4.3.2
# FROM rocker/r-ver:${R_VERSION}
# LABEL name=nalgene \
#   authors="Ben Notkin" \
#   maintainer="bnotkin@worldbank.org" \
#   organization="World Bank Group" \
#   description="Renders City Resilience Program City Scans"

# RUN /rocker_scripts/install_geospatial.sh
# RUN /rocker_scripts/install_python.sh
# RUN /rocker_scripts/install_pandoc.sh
# RUN /rocker_scripts/install_jupyter.sh

# Set the working directory
WORKDIR /app

# RUN apt-get update &&\
#     apt-get install -y binutils libproj-dev gdal-bin

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Specify the command to run your application
CMD ["python", "main.py"]
