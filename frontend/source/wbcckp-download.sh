#!/bin/bash
# No longer using this. Using download.R instead
#
# Download precipitation index change factors from World Bank Climate Change Knowledge Portal
#
# 2024-06-13
# Found URL from https://climateknowledgeportal.worldbank.org/country/bangladesh/extremes
# Copied bash from https://github.com/oi-analytics/caribbean-ccdr/blob/acb3e26cf958d177bed14a621a171844f216d256/scripts/preprocess/wbcckp-download.sh

rm -f get_all.sh
touch get_all.sh

# clear any empty files
# find ./scraped -empty -delete

for var in "rx5day"
do
  for stat in "median"
  do
    # for iso in "DMA" "GRD" "LCA" "VCT"
    # do
      for yrs in "2010-2039" "2035-2064" "2060-2089" "2070-2099"
      do
        for ssp in "ssp119" "ssp126" "ssp245" "ssp370" "ssp585"
        do
          for calc in "changefactorfaep5yr" "changefactorfaep10yr" "changefactorfaep20yr" "frp5yr" "frp10yr" "frp20yr"
          do
            echo "wget -x -nc \"https://climatedata.worldbank.org/thredds/fileServer/CRM/cmip6/all-regridded-bct-${ssp}-climatology/${var}/${stat}/period/${calc}-${var}-period-mean/${yrs}/${calc}-${var}-period-mean_cmip6_period_all-regridded-bct-${ssp}-climatology_${stat}_${yrs}.nc\" \
              -O \"source-data/rx5day-extremes/${calc}-${var}-period-mean_cmip6_period_all-regridded-bct-${ssp}-climatology_${stat}_${yrs}.nc\"" >> get_all.sh
            # echo "wget -x -nH -nc \"https://climatedata.worldbank.org/thredds/fileServer/CRM/cmip6/all-regridded-bct-${ssp}-climatology/${var}/${stat}/period/${calc}-${var}-period-mean/${yrs}/${calc}-${var}-period-mean_cmip6_period_all-regridded-bct-${ssp}-climatology_${stat}_${yrs}.nc\"" >> get_all.sh 
          done
        done
      done
    # done
  done
done

# the loop above generates the temporary get_all.sh, which can then be piped to
# make requests in parallel
# cat get_all.sh #| parallel -j 8
bash get_all.sh
rm get_all.sh