#!/usr/bin/env bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                                                           \n\
   Downloads data.  It first run ssara_federated_query.py to create ssara_listing.txt and ssara_search*.kml files.   \n\
   Then it reads file URLs from ssara_listing.txt  and downloads using wget                                          \n\
                                                                                                                     \n\
   Example:                                                                                                         \n\
      ssara_federated_quey.bash --relativeOrbit=15 --intersectsWith='Polygon((4 49, 4 51, 10 51, 10 49, 4 49))' --platform=SENTINEL-1A,SENTINEL-1B --parallel=6 --maxResults=20000 \n\
                                                                                                                     \n\
"
   printf "$helptext"
   exit 0;
fi

cmd=""
for arg in "$@"; do
  if [[ "$arg" == --intersectsWith=* ]]; then
    # Extract the value right after '=' and wrap it with single quotes
    value="${arg#--intersectsWith=}"
    arg="--intersectsWith='$value'"
  fi
  if [[ "$arg" == --parallel* ]]; then
    parallel="${arg#--parallel=}"
  fi
  # Append each argument to the command
  cmd+=" $arg"
done

# writing command to logfile including '' for intersectsWith
echo "$(date +"%Y%m%d-%H:%m") * `basename "$0"` $cmd " >> log

asfResponseTimeout_opt="--asfResponseTimeout=300"
if [[ $string_for_display == *TSX* ]] || [[ $string_for_display == *CSK* ]]; then
   asfResponseTimeout_opt=""
fi

# run ssara_federated_query.py to create ssara_listing.txt
rm -f ssara_listing.txt
cmd="ssara_federated_query.py $cmd $asfResponseTimeout_opt --kml --print > ssara_listing.txt 2> ssara.e"

echo "$(date +"%Y%m%d-%H:%m") * $cmd " >> log
echo "Running.... $cmd"
eval "$cmd"
grep -q "urllib.error.HTTPError: HTTP Error 502: Proxy Error" ssara.e && { echo "Download problem: urllib.error.HTTPError: HTTP Error 502: Proxy Error"; exit 1; }

# select password according to satellite
if [[ $cmd == *SENTINEL* ]]; then
   user=`grep asfuser $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep asfpass $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
elif [[ $cmd == *COSMO-SKYMED* ]] || [[ $cmd == *ALOS-2* ]] || [[ $cmd == *TSX* ]]; then
   user=`grep unavuser $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep unavpass $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   regex="https:\/\/imaging\.unavco\.\.org\/[a-zA-Z\/0-9\_]+\.tar\.gz"
   regex="https:\/\/imaging\.unavco\.\.org\/*\.gz"
fi

downloads_num=$(grep Found ssara_listing.txt | cut -d " " -f 2)
echo "Number of granules in ssara_listing.txt : $downloads_num"

urls_list=$(cut -s -d ',' -f 14 ssara_listing.txt)
unset IFS
urls=($urls_list)

num_urls=${#urls[@]}

echo "URLs to download: ${urls[@]}"
echo "$(date +"%Y%m%d:%H-%m") * Datafiles to download: $num_urls" | tee -a log

if  [[ -z "$parallel" ]] ; then
   parallel=5
fi

timeout=500

echo "downloading using: echo URLs | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd" | tee -a log
echo ${urls[@]} | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd
exit_code=$?

echo "$(date +"%Y%m%d-%H:%m") check_download: `check_download.py $PWD --delete`"  | tee -a log
granules_num=$(ls *.{zip,tar.gz} 2> /dev/null | wc -l)
echo "$(date +"%Y%m%d:%H-%m") * Downloaded scenes after check_download: $granules_num" | tee -a log

runs=1
while [ $exit_code -ne 0 ] && [ $runs -lt 3 ]; do
    new_timeout=$(echo "$timeout * $runs" | bc)
    echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_code}. Trying again with $new_timeout second timeout" | tee -a log

    echo ${urls[@]} | xargs -n 1 -P $parallel timeout $new_timeout wget --continue --user $user --password $passwd
    exit_code=$?

    echo "$(date +"%Y%m%d:%H-%m") check_download: `check_download.py $PWD --delete`"  | tee -a log
    granules_num=$(ls *.{zip,tar.gz} 2> /dev/null | wc -l)
    echo "$(date +"%Y%m%d:%H-%m") * Downloaded scenes after check_download: $granules_num" | tee -a log

    runs=$((runs+1))
    sleep 1
done

echo "Running.... $cmd" 
echo "$(date +"%Y%m%d:%H-%m") $cmd"  | tee -a log

echo "$(date +"%Y%m%d:%H-%m") check_download: `check_download.py $PWD --delete`"  | tee -a log
granules_num=$(ls *.{zip,tar.gz} 2> /dev/null | wc -l)
echo "$(date +"%Y%m%d:%H-%m") * Downloaded scenes after check_download: $granules_num" | tee -a log

if [[ $granules_num -ge $num_urls ]]; then
   echo "Download was successful, downloaded scenes: $granules_num" | tee -a log
   exit 0;
else
  echo "Not all scenes downloaded, downloaded scenes: $granules_num" | tee -a log
  exit 1;
fi

