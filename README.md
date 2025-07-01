# City Scan

A City Scan is a rapid geospatial assessment of a city's demographic, socioeconomic, climate, and risk conditions. It is a collection of maps and charts made from global and publicly available datasets that provide quick high-level insights into resilience-related topics for a city. These scans are especialy useful for grounding early-stage conversations in geospatial data.

This repository contains the code for two separate processes:
- **Data gathering and processing**: `backend/` hosts Python code that reads global datasets from a variety of sources, cleans them, and clips them to the city boundaries specified by the user. This code is set up to run on Google Cloud Platform as a Cloud Run Job.
- **Visualization and reporting**: `frontend/` hosts R code that reads the processed data from the backend, generates visualizations, and compiles them into a Quarto report. This code is set up to run locally or on Google Cloud Platform as a Cloud Run Job.

To run these processes, you do not need to download this repository. See [docs/backend.md] and [docs/frontend.md] for instructions on how to run.  

If you do want to download the code to contribute or repurpose it, you can clone this repository of both processes using the following command: 

```bash
git clone --filter=blob:none https://github.com/rosemaryturtle/city-scan-automation.git
```

If git is not installed, see the GitHub's [git installation guide](https://github.com/git-guides/install-git). The flag `--filter=blob:none` reduces download size by excluding unnecessary historical items until they are needed.

For more information on how to use, modify, and repurpose the City Scan process, see the docs for each half:
- [Data gathering and processing](docs/backend.md)
- [Visualization and reporting](docs/frontend.md)