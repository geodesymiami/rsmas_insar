#!/bin/bash
#set -x

# insert ' into intersectsWith string that is chopped off by bash
copy=( "$@" )
for i in "${!copy[@]}"; do
    if [[ ${copy[$i]} == *intersectsWith=* ]]; then
        tmp1=${copy[$i]:0:17}
        tmp2=${copy[$i]:17:${#copy[$i]}}
        copy[$i]="$tmp1'$tmp2'"
    fi
    echo element: $i ${copy[$i]}
done

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` "${copy[@]}" " >> log

argv=( "$@" )
#trap "exit" INT TERM    # Convert INT and TERM to EXIT
#trap "kill 0" EXIT      # Kill all children if we receive EXIT

PARALLEL=4

## start option processing
while [[ $# -gt 0 ]] 
do
    key="$1"

    case $key in
        --parallel)
            PARALLEL="$2"
            shift # past argument
            shift # past value
            ;;
        *)    # unknown option
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo "${POSITIONAL[@]}"

echo "PARALLEL=${PARALLEL}"
user=`grep asfuser $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
passwd=`grep asfpass $RSMASINSAR_HOME/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`

echo "Running ... ssara_federated_query.py ${POSITIONAL[@]} > ssara_listing.txt"
ssara_federated_query.py "${POSITIONAL[@]}" > ssara_listing.txt

regex="https:\/\/datapool\.asf\.alaska\.edu\/[a-zA-Z\/0-9\_]+\.zip"

urls=$(grep -oP $regex ssara_listing.txt)

echo $urls | xargs -n 1 -P $PARALLEL wget -nc --user $user --password $passwd 2>/dev/null

exit "$?"

#for f in $urls; do
#    echo $f
#    wget --user famelung --password Falk@1234: $f > test.txt &
#done
#exit 0
