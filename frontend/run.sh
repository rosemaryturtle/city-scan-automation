#!/usr/bin/env -S bash -euo pipefail
# run.sh

# When running the docker container, choose what to render and whether or not to
# download from and upload to Google Cloud Storage. By default, everything is 
# rendered but there is no connection to Google Cloud.

# For fully local runs,
# $ docker run -it --rm -v "$(pwd)"/path/to/:/home/mnt nalgene run.sh

# For local runs, with downloading from and uploading to Google Cloud Storage
    # CITY_DIR="$(pwd)/mnt/pathToLocalCityDirectory" && \
    # GCS_CRED_FILE="$(pwd)/pathToServiceAccount.json" && \
    # GCS_CITY_DIR="cityObjectNameonGoogleCloudStorage" && \
    # mkdir -p "$CITY_DIR" && \
    # docker run -it --rm \
    # -v "$CITY_DIR:/home/mnt" \
    # -v "${GCS_CRED_FILE}:/home/service-account.json" \
    # -e GCS_CITY_DIR="$GCS_CITY_DIR" \
    # nalgene run.sh --download --upload

# Default values - rendering is on by default
STATICMAPS=true
CHARTS=true
PDF=true
HTML=true
COPYCODE=true
# Additional operations default to off
DOWNLOAD=false
UPLOAD=false
STREAM=false

# Function for verbose logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a directory is mounted
check_mount() {
    local mountpoint="$1"
    if ! mountpoint -q "$mountpoint"; then
        echo "Error: $mountpoint is not mounted. Please ensure you have mounted the required directories using:"
        echo "docker run -v \"\$(pwd)\"/path/to/directory:$mountpoint your-image [options]"
        exit 1
    fi
}

# Function to check for GCS object environment variable
check_gcs_object_variable() {
    if [ -z "${GCS_CITY_DIR:-}" ]; then
        # Check if the shell session is interactive
        if [[ $- == *i* ]]; then
            # Prompt the user for input
            read -p "GCS_CITY_DIR is not set. Please provide city's GCS object name: " value
            export GCS_CITY_DIR="$value"
        else
            echo "Error: GCS_CITY_DIR environment variable must be set for --download or --upload operations."
            echo "Run with: docker run -e GCS_CITY_DIR=city-object-name your-image [options]"
            exit 1
        fi
    fi
}

# Check if running on Google Cloud Run
# If so, enable download and upload by default
if [ -n "${CLOUD_RUN_EXECUTION:-}" ]; then
    log "Running on Google Cloud Run. Location: ${GCS_CITY_DIR:-}; Job: ${CLOUD_RUN_JOB:-}; Execution: ${CLOUD_RUN_EXECUTION:-}"
    DOWNLOAD=true
    UPLOAD=true
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        # Individual disable flags
        --no-static-maps)
            STATICMAPS=false
            shift
            ;;
        --no-charts)
            CHARTS=false
            shift
            ;;
        --no-pdf)
            PDF=false
            shift
            ;;
        --no-html)
            HTML=false
            shift
            ;;
        # Individual operation flags
        --download)
            DOWNLOAD=true
            shift
            ;;
        --stream)
            STREAM=true
            shift
            ;;
        --upload)
            UPLOAD=true
            shift
            ;;
        # Collective operation flags
        --download-only)
            STATICMAPS=false
            CHARTS=false
            PDF=false
            HTML=false
            DOWNLOAD=true
            UPLOAD=false
            shift
            ;;
        --upload-only)
            STATICMAPS=false
            CHARTS=false
            PDF=false
            HTML=false
            DOWNLOAD=false
            UPLOAD=true
            shift
            ;;
        --render-only)
            STATICMAPS=true
            CHARTS=true
            PDF=true
            HTML=true
            DOWNLOAD=false
            UPLOAD=false
            shift
            ;;
        --no-render)
            STATICMAPS=false
            CHARTS=false
            PDF=false
            HTML=false
            shift
            ;;
        --no-code-copy)
            COPYCODE=false
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo
            echo "Default behavior: Generates static maps, charts, PDF, and HTML"
            echo
            echo "Requirements:"
            echo "  - When not using --download, must mount volume:"
            echo "    -v \"\$(pwd)\"/path/to/directory:/home/mnt"
            echo "  - When using --download or --upload, must set city's object:"
            echo "    -e GCS_CITY_DIR=city-object-name"
            echo
            echo "Disable specific rendering:"
            echo "  --no-static-maps Skip static map generation"
            echo "  --no-charts      Skip chart generation"
            echo "  --no-html        Skip HTML generation"
            echo "  --no-pdf         Skip PDF generation"
            echo
            echo "Additional operations:"
            echo "  --download       Download required data"
            echo "  --upload         Upload generated files"
            echo "  --no-code-copy   Don't copy reproduction code to mount or GCS"
            echo
            echo "Operation modes:"
            echo "  --download-only  Only download data"
            echo "  --upload-only    Only upload existing files"
            echo "  --render-only    Only render (default behavior)"
            echo "  --no-render      Skip all rendering"
            echo
            echo "Examples:"
            echo "  $0                    # Generate everything"
            echo "  $0 --download         # Download and generate"
            echo "  $0 --no-pdf --no-html # Generate only maps and charts"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run '$0 --help' for usage information"
            exit 1
            ;;
    esac
done

# Check requirements based on selected operations
if [ "$DOWNLOAD" = true ] || [ "$UPLOAD" = true ] || [ "$STREAM" = true ]; then
    check_gcs_object_variable
fi

# If not a Google Cloud Run, need mount and, if using cloud storage, authorization
if [ -z "${CLOUD_RUN_EXECUTION:-}" ]; then
    if [ "$DOWNLOAD" = true ] || [ "$UPLOAD" = true ]; then
        check_mount /home/service-account.json
        log "Not running in Google Cloud Run. Authenticating with gcloud..."
        gcloud auth activate-service-account --key-file=/home/service-account.json
        gcloud config set project city-scan-gee-test
    fi

# If not uploading and not streaming, definitely need mountpoint. If uploading, check if user wants one.
    if [ "$UPLOAD" = false ] && [ "$STREAM" = false ]; then
        check_mount /home/mnt
    elif [ "$UPLOAD" = true ] && [[ $- == *i* ]]; then
        if ! mountpoint -q /home/mnt; then
            read -p "/home/mnt is not mounted. Do you want to proceed anyway? (y/n): " proceed
            if [ "$proceed" != "y" ]; then
                echo "Exiting as per user request."
                exit 1
            fi
        fi
    fi
fi

# Set MNT_DIR default if not already set (Dockerfile sets it to /home/mnt)
if [ -z "${MNT_DIR:-}" ]; then
    if [ -n "${CLOUD_RUN_EXECUTION:-}" ]; then
        # Running in Cloud Run
        MNT_DIR="mnt"
    elif [ -f "run.sh" ] && [ -n "${GCS_CITY_DIR:-}" ]; then
        # Running from frontend/ directory locally
        MNT_DIR="../mnt/${GCS_CITY_DIR}"
    else
        # Fallback to current directory
        MNT_DIR="."
    fi
fi

# Show what we're about to do
log "Operations to perform:"
[ "$DOWNLOAD" = true ] && log "- Downloading data"
[ "$STATICMAPS" = true ] && log "- Generating static maps"
[ "$CHARTS" = true ] && log "- Generating charts"
[ "$PDF" = true ] && log "- Generating PDF"
[ "$HTML" = true ] && log "- Generating HTML"
[ "$COPYCODE" = true ] && log "- Copying reproduction code"
[ "$UPLOAD" = true ] && log "- Uploading results to Google Cloud Storage: "

# Execute operations
if [ "$DOWNLOAD" = true ]; then
    log "Starting download..."
    gcloud storage ls gs://crp-city-scan/$GCS_CITY_DIR | grep '^gs://' | xargs -I {} gcloud storage cp -R {} mnt
elif [ "$STREAM" = true ]; then
    log "Streaming mode: Downloading config files (01-user-input/)..."
    gcloud storage cp -R gs://crp-city-scan/$GCS_CITY_DIR/01-user-input mnt/ 2>/dev/null || log "Warning: Could not download 01-user-input directory"
fi

if [ "$DOWNLOAD" = true ] || [ "$UPLOAD" = true ] || [ "$STREAM" = true ]; then
    export USE_GCS="true"
    export SCAN_ID="$GCS_CITY_DIR"
fi

# Moving into mnt/ directory for ease of file paths... silly?
# Also for access in interactive local runs
# Create working directory if it doesn't exist
mkdir -p "$MNT_DIR"

if [ "$COPYCODE" = true ]; then
    cp -r R scripts source run.sh index.qmd pdf.qmd scan-calculations.Rmd _pre-render.R _post-render.R "$MNT_DIR"
fi
cd "$MNT_DIR"
echo "." > city-dir.txt
mkdir -p 01-user-input 02-process-output 03-render-output 

if [ "$COPYCODE" = true ]; then
    log "Copying reproduction code..."
    mkdir -p 00-reproduction-code
    rm -rf 00-reproduction-code/R 00-reproduction-code/scripts \
        00-reproduction-code/source 00-reproduction-code/index.qmd \
        00-reproduction-code/pdf.qmd 00-reproduction-code/scan-calculations.Rmd \
        00-reproduction-code/_pre-render.R 00-reproduction-code/_post-render.R
    cp -r R scripts source index.qmd pdf.qmd scan-calculations.Rmd _pre-render.R _post-render.R 00-reproduction-code
    echo ".." > 00-reproduction-code/city-dir.txt
    if [ "$UPLOAD" = true ]; then
        log "Uploading reproduction code..."
        gcloud storage cp -R 00-reproduction-code gs://crp-city-scan/$GCS_CITY_DIR
    fi
fi

if [ "$STATICMAPS" = true ]; then
    log "Generating maps..."
    Rscript R/maps-static.R
    if [ "$UPLOAD" = true ]; then
        log "Uploading static maps..."
        gcloud storage cp -R 03-render-output/maps/** gs://crp-city-scan/$GCS_CITY_DIR/03-render-output/maps/
    fi
fi

if [ "$CHARTS" = true ]; then
    log "Generating charts..."
    echo "FUTURELOG: Currently no code to generate charts."

    Rscript -e "rmarkdown::render('scan-calculations.Rmd', output_file ='03-render-output/scan-calculations.html')"
    if [ "$UPLOAD" = true ]; then
          gcloud storage cp 03-render-output/scan-calculations.html gs://crp-city-scan/$GCS_CITY_DIR/03-render-output/
    fi
    # if [ "$UPLOAD" = true ]; then
        # gcloud storage cp -R 03-render-output/charts gs://crp-city-scan/$GCS_CITY_DIR/03-render-output
    # fi
fi

if [ "$PDF" = true ]; then
    log "Generating PDF..."
    quarto render pdf.qmd --cache-refresh
    # Ideally, we'd convert SASS to CSS before build, but this seems safer
    # # Doesn't work on Google Cloud Run
    # /opt/quarto/bin/tools/aarch64/dart-sass/sass source/custom.scss source/custom.css
    Rscript R/pdf-prep.R pdf.html pdf.html source/custom.css
    vivliostyle build pdf.html -o 03-render-output/print.pdf
    # Do I want to copy pdf.html to a folder too?
    if [ "$UPLOAD" = true ]; then
        gcloud storage cp -R 03-render-output/print.pdf gs://crp-city-scan/$GCS_CITY_DIR/03-render-output/print.pdf
    fi
fi

if [ "$HTML" = true ]; then
    log "Generating HTML..."
    quarto render index.qmd --cache-refresh
    # Do I actually want to keep cache?
    # Don't/can't move index.html, etc., to $MNT_DIR if $MNT_DIR is working dir
    ## Wait why wasn't this possible?
    ## Perhaps because any other files that are used don't also get moved
    rm -rf 03-render-output/index_files
    rm -rf 03-render-output/index_cache
    mv -f index.html index_files index_cache 03-render-output/
    if [ "$UPLOAD" = true ]; then
        gcloud storage cp -R 03-render-output/index.html 03-render-output/index_files gs://crp-city-scan/$GCS_CITY_DIR/03-render-output/
    fi
fi
