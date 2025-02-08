# For R & Docker primer, see http://jsta.github.io/r-docker-tutorial/

# Install R base image from Rocker (builds on Ubuntu 22.04 LTS)
# https://github.com/rocker-org/rocker-versioned2/blob/master/dockdockeerfiles/Dockerfile_r-ver_4.0.2 
ARG R_VERSION=4.3.2
FROM rocker/r-ver:${R_VERSION}
LABEL name=nalgene \
  authors="Ben Notkin" \
  maintainer="bnotkin@worldbank.org" \
  organization="World Bank Group" \
  description="Renders City Resilience Program City Scans"

# Install R-related tools
# While rocker has specific images for tidyverse and geospatial, they are not arm64 compatible
RUN set -e \
    && /rocker_scripts/install_tidyverse.sh \
    && /rocker_scripts/install_geospatial.sh \
    && /rocker_scripts/install_python.sh \
    && /rocker_scripts/install_pandoc.sh \
    && /rocker_scripts/install_jupyter.sh \
    && export QUARTO_VERSION=1.5.57 \
    && /rocker_scripts/install_quarto.sh

# Install dependencies
RUN set -e \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        apt-utils \
        curl \
        gnupg \
        lsb-release \
        tini \
        # X11 dependencies
        libx11-6 \
        libxss1 \
        libxt6 \
        libxext6 \
        libsm6 \
        libice6 \
        xdg-utils \
        # Vivliostyle/Chromium dependencies
        libdbus-1-3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxi6 \
        libxtst6 \
        libnss3 \
        libxrandr2 \
        libasound2 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libwayland-client0 \
        libwayland-cursor0 \
        libwayland-egl1 \
        libgbm1 \
        fonts-liberation \
        gconf-service \
        # libappindicator1 \
        libappindicator3-1 \
        wget  && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install gcloud
RUN set -e \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update \
    && apt-get install -y google-cloud-sdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Vivliostyle CLI and Chromium (Chromium adds ~1 GB), requires node
RUN set -e \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && node --version
RUN set -e \
    && npm install -g @playwright/test \
    && npx playwright install chromium \
    && npm install -g @vivliostyle/cli@8.17.1 --no-fund --no-audit

# Install remaining R packages
RUN set -e \
    && install2.r \
      librarian \
      tidyterra \ 
      cowplot \ 
      directlabels \ 
      ggspatial \
      ggh4x \ 
      ggnewscale \
      ggrepel \ 
      ggtext \
      plotly \
      prettymapr
# as.polygons() behaves differently in 1.7-71 and 1.7-78; ideally should raise R
# version to 4.4, but might have other consequences
RUN Rscript -e "remotes::install_version('terra', version = '1.7-78', repos = 'https://cran.r-project.org')"
      
# Set and create mount directory
# This depends on the user setting `-v host_dir:/home/mnt in docker run command
# Maybe explore making a shell script or docker compose file?
ENV MNT_DIR /home/mnt
RUN mkdir -p $MNT_DIR

# Copy local code to the container image.
# Consider both cloning from Github & moving this all to a mounted drive instead
WORKDIR /home
COPY R ./R
COPY scripts ./scripts
COPY source ./source
COPY run.sh index.qmd pdf.qmd ./

# Add /home to path to enable running run.sh instead of /home/run.sh
ENV PATH="/home:${PATH}"

# Ensure the scripts are executable
# For future entrypoint commands
# RUN chmod +x /home/scripts/entrypoint.sh
RUN chmod +x /home/run.sh

# Write $MNT_DIR to city-dir.txt
# Because only one city is run per docker run and the city's directory is set
# with the volume mount, the file path in city-dir.txt doesn't need to be or,
# alternatively, is inherently city-specific
RUN echo $MNT_DIR > city-dir.txt

# Use tini to manage zombie processes and signal forwarding
# https://github.com/krallin/tini
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to Tini
CMD ["/home/run.sh"]

#### Docker commands to build and run Docker image locally ####################

# For all, Docker must be running
# ***Add Docker instructions***

# Build the container
# docker build -t nalgene .
# Run the container without rendering the site ()
# docker run -it --rm -v "$(pwd)"/$CITY_DIR:/home/mnt nalgene bash
# Run the container with rendering the site
# docker run -it --rm -v "$(pwd)"/$CITY_DIR:/home/mnt nalgene scripts/local_run.sh
# where $CITY_DIR is the city-specific directory (e.g., mnt/2023-10-kenya-mombasa/)

# Alternatively, instead of building the container, you can run the version
# of the image hosted on Docker Hub by simply replacing `nalgene` with 
# `notkin/nalgene` in the command. !! This will not include any edits you've
# made to non-mounted files !!

# You can avail yourself of VS Code's functionality (instead of limiting
# yourself to the command line), with the Dev Containers extension (see tutorial
# at https://code.visualstudio.com/docs/devcontainers/containers
# 1. Install Dev Containers extension
# 2. Run the container: `docker run -it --rm -v "$(pwd)"/mnt:/home/mnt -e CITY_DIR=$CITY_DIR nalgene bash`
# 3. Attach VS Code to the container: CMD/CTRL + SHIFT + P, then type/select
#    "Dev Containers: Attach to Running Container..."; hit Enter again to select
#    oddly named container
# 4. Change directory to /home: cd ../home
# 5. In VS Code's Explorer, click Open Folder, type /home, and hit enter 