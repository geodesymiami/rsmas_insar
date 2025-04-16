#!/bin/bash

# Function to print usage
usage() {
    echo "Usage: $0 --subset-lalo=lat_min:lat_max,lon_min:lon_max"
    exit 1
}

# Parse input arguments
for arg in "$@"; do
    if [[ $arg == --subset-lalo=* ]]; then
        lalo="${arg#*=}"
        IFS=',' read -r lat_range lon_range <<< "$lalo"
        IFS=':' read -r lat_min lat_max <<< "$lat_range"
        IFS=':' read -r lon_min lon_max <<< "$lon_range"
        echo "--sub-lat $lat_min $lat_max --sub-lon $lon_min $lon_max"
        exit 0
    fi
done

# If no valid argument is found, print usage
usage
