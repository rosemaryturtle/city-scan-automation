#!/bin/bash

# Parse arguments --------------------------------------------------------------
if [ $# -lt 1 ] || [[ "$1" == -* ]]; then
  read -p "Enter the name of the city directory as it appears on Google Cloud (e.g., 2025-04-colombia-cartagena): " GCS_CITY_DIR
  if [ -z "$GCS_CITY_DIR" ]; then
    echo "City directory is required. Exiting."
    exit 1
  fi
else
  GCS_CITY_DIR="$1"
  shift
fi

# Check for --docker, --native, and --no-gcs flags, and remove from arguments
RUN_DOCKER=0
RUN_NATIVE=0
DOWNLOAD_GCS=1
DOCKER_FLAGS=()
for arg in "$@"; do
  case "$arg" in
    --docker)
      RUN_DOCKER=1
      ;;
    --native)
      RUN_NATIVE=1
      ;;
    --no-gcs)
      DOWNLOAD_GCS=0
      ;;
    *)
      DOCKER_FLAGS+=("$arg")
      ;;
  esac
done

# Local directory for the city (will be created if it doesn't exist)
CITY_DIR="$(pwd)/mnt/${GCS_CITY_DIR}"

# Repository for City Scan code
REPO="https://github.com/rosemaryturtle/city-scan-automation.git"
BRANCH="phl-atlas"

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

if [[ ${DOWNLOAD_GCS:-1} -eq 1 ]]; then
  # Download the city data from Google Cloud Storage
  if ! gcloud storage ls "gs://crp-city-scan/$GCS_CITY_DIR" > /dev/null 2>&1; then
    echo "Error: gs://crp-city-scan/$GCS_CITY_DIR does not exist or you do not have permission. (Try \`gcloud auth login\`?) Exiting."
    exit 1
  fi
  gcloud storage ls gs://crp-city-scan/$GCS_CITY_DIR | grep '^gs://' | grep -v '/00-reproduction-code/' | xargs -I {} gcloud storage cp -R {} "$CITY_DIR"
fi

# Write city-dir.txt to tell the R scripts where to work from ------------------
echo "." > "$CITY_DIR/city-dir.txt"

# Create maps ------------------------------------------------------------------

if [[ $RUN_DOCKER -eq 1 && $RUN_NATIVE -eq 1 ]]; then
  echo "Warning: Both --docker and --native flags are set. Please choose one."
  select choice in "Docker" "Native"; do
    case $choice in
      Docker)
        RUN_NATIVE=0
        break
        ;;
      Native)
        RUN_DOCKER=0
        break
        ;;
      *)
        echo "Please select 1 (Docker) or 2 (Native)."
        ;;
    esac
  done
fi

if [[ $RUN_NATIVE -eq 1 ]]; then
  ORIGINAL_DIR=$(pwd)
  cd "$CITY_DIR"
  trap 'cd "$ORIGINAL_DIR"' EXIT
  Rscript R/maps-static.R || {
    echo "Error: Failed to run R script for static maps."
    exit 1
  }
  echo "Static maps generated successfully."
  # trap - EXIT
fi

if [[ $RUN_DOCKER -eq 1 ]]; then
# Open Docker if it's not running
  if ! pgrep -x "docker" > /dev/null; then
    open -a docker
    sleep 4
  fi

  # Run the Docker container with the city directory mounted
  echo "Running Docker container..."
  docker run -it --rm \
    -v "$CITY_DIR:/home/mnt" \
    -e GCS_CITY_DIR="$GCS_CITY_DIR" \
    notkin/nalgene run.sh --no-code-copy ${DOCKER_FLAGS:---no-pdf --no-html}
fi
