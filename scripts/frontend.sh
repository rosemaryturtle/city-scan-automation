#!/bin/bash

# Set variables ----------------------------------------------------------------
# Path to service account key file -- CHANGE TO USE YOUR SERVICE ACCOUNT KEY
# It's necessary that this is a full path, not a relative path, thus the `$(pwd)`
# which adds the current working directory to the path
GCS_CRED_FILE="$(pwd)/.access/<service-account-key.json>"

# Name of the city directory in the Google Cloud Storage Bucket
# e.g., GCS_CITY_DIR="2025-07-philippines-taytay-rizal"
GCS_CITY_DIR="2025-07-philippines-kalibo-aklan"

# Local directory for the city (will be created if it doesn't exist)
CITY_DIR="$(pwd)/mnt/${GCS_CITY_DIR}"

# Repository for City Scan code
REPO="https://github.com/rosemaryturtle/city-scan-automation.git"
BRANCH="main"

# Shallow clone the repository and download city data --------------------------

# # If directory does not exist, clone the repository
shopt -s dotglob nullglob
if [ ! -d "$CITY_DIR" ]; then
  mkdir -p "$CITY_DIR"
  git clone -b "$BRANCH" --filter=blob:none "$REPO" "$CITY_DIR/temp-repo"
  echo "Copying files from the cloned repository to the city directory..."
  for item in R scripts source index.qmd pdf.qmd; do
    cp -r "$CITY_DIR/temp-repo/frontend/$item" "$CITY_DIR"
  done
else 
# If the directory exists, ask if the user wants to overwrite it with a new clone
  echo "City directory already exists: $CITY_DIR"
  read -p "Folder may or may not have code files. Do you want to clone and possibly overwrite the repository contents with a new clone? (y/n): " overwrite_choice
  if [[ "$overwrite_choice" = "y" ]]; then
    rm -rf "$CITY_DIR/temp-repo"
    git clone -b "$BRANCH" --filter=blob:none "$REPO" "$CITY_DIR/temp-repo"
    echo "Copying files from the cloned repository to the city directory..."
    for item in R scripts source index.qmd pdf.qmd; do
      cp -r "$CITY_DIR/temp-repo/frontend/$item" "$CITY_DIR"
    done
  else
    echo "Not overwriting the existing city directory code files. Continuing to download city data..."
  fi
fi
shopt -u dotglob nullglob
rm -rf $CITY_DIR/temp-repo

# Download the city data from Google Cloud Storage
gcloud storage ls gs://crp-city-scan/$GCS_CITY_DIR | grep '^gs://' | xargs -I {} gcloud storage cp -R {} "$CITY_DIR"

# Run the Docker container to create maps --------------------------------------
if ! pgrep -x "docker" > /dev/null; then
  open -a docker
  sleep 4
fi
docker run -it --rm \
  -v "$CITY_DIR:/home/mnt" \
  -e GCS_CITY_DIR="$GCS_CITY_DIR" \
  notkin/nalgene run.sh --no-pdf --no-html --no-code-copy