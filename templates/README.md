# Templates

This folder contains templates to be used in various parts of the City Scan process. These specific files should not be read directly, but instead should be copied to the appropriate location and modified for the specific cities. These template files will be updated as the City Scan process evolves.

- `city_inputs.yml` 
  - **what it is:** contains all city-specific information, including the city name and the path to the optionally provided shapefile; it also includes other options such as which OSM features to include, such as the parameters for the flood analysis
  - **how to use it:** upload it to Google Cloud to define the city-specific parameters for a City Scan job
  - **where it belongs:** if using `scripts/backend.sh`, this file will be copied to the `gcs-01-user-input` directory
- `menu.yml`
  - **what it is:** defines which components to run in the Job. (Multiple jobs can be run for the same city, with different components turned on or off, though some components are interdependent.)
  - **how to use it:** upload it to Google Cloud to define which components of the City Scan process to run
  - **where it belongs:** if using `scripts/backend.sh`, this file will be copied to the `gcs-01-user-input` directory
- `manual-text.md`
  - **what it is:** the city-specific text used in all City Scans, such as takeaway bullets and desk research
  - **how to use it:** after initially running the frontend process, write a version of this file (taking care to follow it's structure and keeping all of the headings that use `//`); it will be used to generate the text in the final report.
  - **where it belongs:** save or upload (depending on if running frontend locally or on cloud) to 01-user-input/text-files/manual-text.md in the relevant city directory, e.g. `2024-09-zambia-lusaka/01-user-input/text-files/manual-text.md`