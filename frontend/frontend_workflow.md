# Frontned Workflow Overview

This document explains the three different ways to run the frontend code for generating city scan outputs, including the new streaming mode implementation.

**The frontend workflow from upstream (rosemaryturtle/city-scan-automation) is as follows:**

  1. NATIVE (frontend.sh --native)
```
 Where code runs: Your local machine

 Flow:
  frontend.sh $SCAN_ID --native
    ├─ Clone repo → mnt/$SCAN_ID/
    ├─ Download data from GCS → mnt/$SCAN_ID/
    └─ cd mnt/$SCAN_ID/
       └─ Rscript R/maps-static.R  ← Runs directly on your
  
  Mac/Linux
  Pros: Fast, easy debugging
  Cons: Need R + all packages installed locally

```
2. DOCKER (frontend.sh --docker)
```
  Where code runs: Docker container on your local machine

  Flow:
  frontend.sh $SCAN_ID --docker
    ├─ Clone repo → mnt/$SCAN_ID/
    ├─ Download data from GCS → mnt/$SCAN_ID/
    └─ docker run -v mnt/$SCAN_ID:/home/mnt ...
         └─ run.sh (inside container)
              └─ Rscript R/maps-static.R  ← Runs in isolated container
  
  Pros: Consistent environment, no local R setup needed
  Cons: Slower than native
```

3. DIRECT RUN in frontend (only for Docker (?)) (direct run.sh, no frontend.sh)
```
  Where code runs: Google Cloud (serverless container) / LOCAL

  Flow:
  Cloud Run triggers pre-built container
    └─ run.sh --download --upload
         ├─ Download from GCS (inside cloud container)
         ├─ Process
         └─ Upload back to GCS

  cd frontend/
    ./run.sh --download --upload
        ├─ Downloads data
        ├─ Processes
        └─ Uploads results
```
  <!-- Pros: No local machine needed, scalable
  Cons: Costs money, harder to debug -->



---
## Running with --stream

The new streaming mode implementation modifies the NATIVE and DIRECT RUN methods to allow for data streaming from GCS, reducing local storage needs and enabling easier local development with uncommitted changes.


Using --stream will generate **maps** and **charts + referece HTML report** in the 03-render-output/ output directory **without downloading all data locally**.

There are two main ways to run it

**1. Native streaming (via frontend.sh):**
```bash
./scripts/frontend.sh 2025-11-mauritania-nouakchott --native --stream
```

This will trigger the following flow:
```
 Flow:
  frontend.sh $SCAN_ID --native --stream
    ├─ Clone repo → mnt/$SCAN_ID/
    ├─ Only download 01-User-Input from GCS → mnt/$SCAN_ID/
    └─ cd mnt/$SCAN_ID/
       ├─ Rscript R/maps-static.R 
       └─ Rscript -e "rmarkdown::render('scan-calculations.Rmd', output_file='03-render-output/scan-calculations.html')
```

And all the outputs will be save locally in the 03-render-output/ directory.


**2. Direct run.sh - All outputs:**
```bash
cd frontend
env GCS_CITY_DIR=2025-11-mauritania-nouakchott ./run.sh --stream --no-pdf --no-html
```

This will trigger the

```
  DIRECT RUN + STREAM (direct run.sh --stream)
  
  Flow:
    cd frontend/
      ./run.sh --stream --no-pdf --no-html
          ├─ Does NOT download anything from GCS
          ├─ Process with streaming from GCS
          └─ add result to output directory locally
  
```

---

### For Further Discussion: 

**Where does the code come from?** This latest implementation is more designed to work with data stored on GCS and code stored locally in your `frontend/` directory. The `--stream` flag modifies the behavior of the `--native` mode to prioritize local code

#### `--native` (without --stream):
- **Clones from GitHub** (rosemaryturtle/city-scan-automation main branch)
- Downloads **ALL data** from GCS to local disk
- rosemaryturtle/city-scan-automation main branch does not inlcude scan-calculations.Rmd yet so it will fail. 


#### `--native --stream`:
- **Copies from LOCAL** `frontend/` directory (your working code)
- Falls back to GitHub clone if `frontend/` directory not found
- Downloads **only** 01-user-input/ (config files, ~MBs)
- Streams large data from GCS (avoids downloading GBs)


Need tor further discuss on this to make sure that native will work, or merge to include scan-calculations.Rmd in the main upstream branch.


**Benchmark Cities** The code is setup that manual benchmark cities and countries are set from city-inputs.yml. As of now, these variables are not available in the most if not all city-inputs.yml in GCS. So when running with --stream, the benchmark cities will not be generated unless added to city-inputs.yml in local 01-user-input/ directory to include benchmark cities and rerun scan-calculation.Rmd. 

The fallback user-inputs.R is available in R/ folder but only triggered when run in a non a Scan directory. 

---
