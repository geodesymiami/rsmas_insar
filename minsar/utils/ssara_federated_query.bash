#!/bin/bash
#set -x

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` "$@" " >> log

argv=( "$@" )
trap "exit" INT TERM    # Convert INT and TERM to EXIT
trap "kill 0" EXIT      # Kill all children if we receive EXIT

PARALLEL=24

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

echo "PARALLEL=${PARALLEL}"
user=`grep asfuser /scratch/05861/tg851601/code/rsmas_insar/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`
passwd=`grep asfpass /scratch/05861/tg851601/code/rsmas_insar/3rdparty/SSARA/password_config.py | sed 's/\"//g''' | cut -d '=' -f 2`

cmd="ssara_federated_query.py "${argv[@]:0:$#-1}" > ssara_listing.txt"
#echo Running ... $cmd
ssara_federated_query.py "$@" > ssara_listing.txt

regex="https:\/\/datapool\.asf\.alaska\.edu\/[a-zA-Z\/0-9\_]+\.zip"

urls=$(grep -oP $regex ssara_listing.txt)

echo $urls | xargs -n 1 -P $PARALLEL wget -Nc --user $user --password $passwd

#for f in $urls; do
#    echo $f
#    wget --user famelung --password Falk@1234: $f > test.txt &
#done
#exit 0
