#!/bin/bash
#set -x

# insert ' into intersectsWith string that is chopped off by bash
copy=( "$@" )
for i in "${!copy[@]}"; do
    if [[ ${copy[$i]} == *intersectsWith=* ]]; then
        tmp1=${copy[$i]:0:17}
        tmp2=${copy[$i]:17:${#copy[$i]}}
        copy[$i]="$tmp1'$tmp2'"
    elif [[ ${copy[$i]} == *collectionName=* ]]; then
        tmp1=${copy[$i]:0:17}
        tmp2=${copy[$i]:17:${#copy[$i]}}
        copy[$i]="$tmp1'$tmp2'"
    elif [[ ${copy[$i]} == --parallel* ]]; then
        parallel=$(echo ${copy[$i]} | cut -d= -f2)
    fi
    echo element $i: ${copy[$i]}
done

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` "${copy[@]}" " >> log

argv=( "$@" )


if  [[ -z "$parallel" ]] ; then 
   parallel=5 
fi

timeout=400

echo "parallel=${parallel}"

# select password according to satellite
echo ${copy[0]}
if [[ ${copy[0]} == *SENTINEL* ]]; then
   user=`grep asfuser $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep asfpass $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
elif [[ ${copy[0]} == *COSMO-SKYMED* ]] || [[ ${copy[0]} == *ALOS-2* ]]; then
   user=`grep unavuser $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   passwd=`grep unavpass $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
   regex="https:\/\/imaging\.unavco\.\.org\/[a-zA-Z\/0-9\_]+\.tar\.gz"
   regex="https:\/\/imaging\.unavco\.\.org\/*\.gz"
fi

echo "Running (with\`s inserted) ... ssara_federated_query.py ${argv[@]:0:$#-1} --maxResults=20000 > ssara_listing.txt"
ssara_federated_query.py "${argv[@]:0:$#-1}" --maxResults=20000 > ssara_listing.txt


urls_list=$(cut -s -d ',' -f 14 ssara_listing.txt)
unset IFS
urls=($urls_list)

num_urls=${#urls[@]}
#num_urls=$(echo $(($num_urls+$parallel)))

echo "URLs to download: ${urls[@]}"
echo "Datafiles to download: $num_urls"

echo ${urls[@]} | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd
exit_code=$?

runs=1
while [ $exit_code -ne 0 ] && [ $runs -lt 3 ]; do
    echo "Something went wrong. Exit code was ${exit_code}. Trying again with ${t} second timeout."
    echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_code}. Trying again with ${t} second timeout" >> log
    echo ${urls[@]} | xargs -n 1 -P $parallel timeout $timeout wget --continue --user $user --password $passwd
    exit_code=$?
    runs=$((runs+1))
    sleep 60
done

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

exit 0

