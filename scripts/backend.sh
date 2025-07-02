#!/usr/bin/env -S bash -euo pipefail
# Execute City Scan backend (which triggers frontend)

# Create template directory and copy templates
mkdir -p gcs-user-input
mkdir -p gcs-user-input/AOI
if [[ ! -f gcs-user-input/city_inputs.yml ]]; then
  cp templates/city_inputs.yml gcs-user-input/city_inputs.yml
fi
if [[ ! -f gcs-user-input/menu.yml ]]; then
  cp templates/menu.yml gcs-user-input/menu.yml
fi

read -p "Do you want to update the template city_inputs.yml and menu.yml with the most recently used versions? (y/n): " update_files
if [[ "$update_files" == "y" ]]; then
  gcloud storage cp gs://crp-city-scan/01-user-input/city_inputs.yml \
    gs://crp-city-scan/01-user-input/menu.yml gcs-user-input
fi
echo ""
echo "Please modify city_inputs.yml and menu.yml for your city and add shapefile AOI/."
echo "(All are located in gcs-user-input/)"
read -p "When finished press [Enter] to continue..." 

# Read city name
city_name=$(grep 'city_name:' gcs-user-input/city_inputs.yml | awk '{print $2}' | tr -d '\r' | tr -d '"' | tr -d "'")
echo ""
echo "City name is set to '$city_name'."

# Read gcs-user-input/menu.yml and print a 2-column table of true/false values
echo "menu.yml has turned on and off the following values:"

true_values=()
false_values=()

while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([^:#]+):[[:space:]]*(True|False)[[:space:]]*$ ]]; then
    key="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    if [[ "$value" == "True" ]]; then
      true_values+=("+ $key")
    elif [[ "$value" == "False" ]]; then
      false_values+=("- $key")
    fi
  fi
done < gcs-user-input/menu.yml

printf "%-30s | %-30s\n" "Will run" "Won't run"
printf "%-30s-+-%-30s\n" "$(printf -- '-%.0s' {1..30})" "$(printf -- '-%.0s' {1..30})"

for i in $(seq 0 $(( ${#true_values[@]} > ${#false_values[@]} ? ${#true_values[@]} - 1 : ${#false_values[@]} - 1 ))); do
  printf "%-30s | %-30s\n" "${true_values[i]:-}" "${false_values[i]:-}"
done

# Read the value for AOI_shp_name from city_inputs.yml
AOI_shp_name=$(grep 'AOI_shp_name:' gcs-user-input/city_inputs.yml | awk '{print $2}' | tr -d '\r' | tr -d '"' | tr -d "'")

if [[ -n "$AOI_shp_name" ]]; then
  if ls "gcs-user-input/AOI/${AOI_shp_name}"* 1> /dev/null 2>&1; then
    echo "AOI file $AOI_shp_name was found."
    read -p "Do you want to upload the '$AOI_shp_name' AOI files to Google (y/n)?: " upload_aoi
    if [[ "$upload_aoi" == "y" ]]; then
      if ! gcloud storage cp "gcs-user-input/AOI/${AOI_shp_name}"* gs://crp-city-scan/01-user-input/AOI; then
        echo "Error: Failed to upload AOI files."
        exit 1
      fi
    fi
  else
    echo "No files matching 'gcs-user-input/AOI/${AOI_shp_name}*' were found."
    echo "You can add the missing files to the 'gcs-user-input/AOI' directory and rerun"
    echo "the script, or proceed without uploading AOI files if they're already uploaded."
    read -p "Do you want to proceed without uploading AOI files? (y/n): " proceed_without_aoi
    if [[ "$proceed_without_aoi" == "n" ]]; then
      exit 1
    else 
      echo "Proceeding without uploading AOI files."
    fi
  fi
else
  echo "Error: AOI_shp_name is not set."
  exit 1
fi

# # List all active job executions for the job 'csb'
# active_executions=$(gcloud run jobs executions list --job=csb --filter="status.state=ACTIVE" --format="value(name)")

# if [[ -n "$active_executions" ]]; then
#   echo "Active job executions for 'csb':"
#   echo "$active_executions"
# else
#   echo "No active job executions found for 'csb'."
# fi

gcloud storage cp gcs-user-input/menu.yml gcs-user-input/city_inputs.yml \
  gs://crp-city-scan/01-user-input

gcloud run jobs execute csb
