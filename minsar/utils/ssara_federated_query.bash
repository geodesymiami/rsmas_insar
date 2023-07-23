#!/bin/bash
#set -x

# insert ' into intersectsWith string that is chopped off by bash
copy=( "$@" )
for i in "${!copy[@]}"; do
    if [[ ${copy[$i]} == *intersectsWith=* ]]; then
        tmp1=${copy[$i]:0:17}
        tmp2=${copy[$i]:17:${#copy[$i]}}
        copy[$i]="$tmp1'$tmp2'"
        #copy[$i]="$tmp1\"$tmp2\""
    elif [[ ${copy[$i]} == *collectionName=* ]]; then
        tmp1=${copy[$i]:0:17}
        tmp2=${copy[$i]:17:${#copy[$i]}}
        copy[$i]="$tmp1'$tmp2'"
    elif [[ ${copy[$i]} == --parallel* ]]; then
        parallel=$(echo ${copy[$i]} | cut -d= -f2)
    fi
    #echo element $i: ${copy[$i]}
done

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` "${copy[@]}" " >> log

if  [[ -z "$parallel" ]] ; then 
   parallel=5 
fi

timeout=500

#echo "parallel=${parallel}"

# select password according to satellite
if [[ ${copy[@]} == *SENTINEL* ]]; then
   user=`grep asfuser $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep asfpass $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
elif [[ ${copy[@]} == *COSMO-SKYMED* ]] || [[ ${copy[@]} == *ALOS-2* ]] || [[ ${copy[@]} == *TSX* ]]; then
   user=`grep unavuser $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep unavpass $RSMASINSAR_HOME/tools/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   regex="https:\/\/imaging\.unavco\.\.org\/[a-zA-Z\/0-9\_]+\.tar\.gz"
   regex="https:\/\/imaging\.unavco\.\.org\/*\.gz"
fi

rm -f ssara_listing.txt
argv=( "$@" )
string_for_display=$(printf " %s" "${copy[@]}")
string_for_display=${string_for_display:1}
#echo $string_for_display

asfResponseTimeout_opt="--asfResponseTimeout=60"
if [[ $string_for_display == *TSX* ]] || [[ $string_for_display == *CSK* ]]; then
   asfResponseTimeout_opt=""
fi

cmd_display="ssara_federated_query.py $string_for_display --maxResults=20000 $asfResponseTimeout_opt  > ssara_listing.txt"
echo "Running ... $cmd_display"

ssara_federated_query.py "${argv[@]:0:$#}" --maxResults=20000 $asfResponseTimeout_opt  > ssara_listing.txt

downloads_num=$(grep Found ssara_listing.txt | cut -d " " -f 2)
echo "Number of granules: $downloads_num"

urls_list=$(cut -s -d ',' -f 14 ssara_listing.txt)
unset IFS
urls=($urls_list)

num_urls=${#urls[@]}

echo "URLs to download: ${urls[@]}"
echo "$(date +"%Y%m%d:%H-%m") * Datafiles to download: $num_urls" | tee -a log

echo "downloading using:: xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd"
echo ${urls[@]} | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd
exit_code=$?

echo "$(date +"%Y%m%d:%H-%m") check_download: `check_download.py $PWD --delete`"  | tee -a log
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

#echo "Running.... $cmd_display" | tee -a log
echo "Running.... $cmd_display" 
echo "$(date +"%Y%m%d:%H-%m") $cmd_display"  | tee -a log

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

# start=0
# stop=$(($start+$parallel))
# while [ $start -le $num_urls ]; do
#     us="${urls[@]:$start:$parallel}"
#     echo "URLs to download: ${us[@]}"
#     echo $us | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd -nv
#     exit_code=$?
#     runs=1
#     while [ $exit_code -eq 123 -o $exit_code -eq 127 ] && [ $runs -lt 3 ]; do
#         echo "Something went wrong. Exit code was ${exit_code}. Trying again with ${t} second timeout."
#         echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_code}. Trying again with ${t} second timeout" >> log
#         echo $us | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd -nv
#         exit_code=$?
#         runs=$((runs+1))
#         sleep 60
#     done
#     echo "Finished downloading files $stop/$num_urls succesfully."
#     start=$(($stop+1))
#     stop=$(($start+$parallel))
# done


