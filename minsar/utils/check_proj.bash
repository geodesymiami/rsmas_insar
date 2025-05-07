#!/bin/bash

# check_vertical_transform.sh
# Tests whether gdaltransform supports geoid-to-ellipsoid vertical transformations

# --- Help message ---
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    cat << EOF
Usage: ./check_vertical_transform.sh

This script checks whether your GDAL/PROJ installation supports vertical datum
transformations using gdaltransform.

Specifically, it tries to convert:
  - From: EPSG:4326+5773 (WGS84 horizontal + EGM96 geoid height)
  - To:   EPSG:4326+4979 (WGS84 horizontal + ellipsoidal height)

A test coordinate (-80.125, 25.9, 0m geoid) is used.

Expected result: an ellipsoidal height of about -28 meters in South Florida.

Options:
  -h, --help    Show this help message
EOF
    exit 0
fi

# --- Test transform ---
echo "Checking if gdaltransform supports vertical transformations..."

RESULT=$(echo "-80.125 25.9 0" | gdaltransform -s_srs EPSG:4326+5773 -t_srs EPSG:4326+4979 2>&1)

if echo "$RESULT" | grep -Eq '^[+-]?[0-9]+\.[0-9]+ +[+-]?[0-9]+\.[0-9]+ +[+-]?[0-9]+\.[0-9]+'; then
    HEIGHT=$(echo "$RESULT" | awk '{print $3}')
    ROUNDED=$(printf "%.1f\n" "$HEIGHT")
    echo "Success: Vertical transformation is supported."
else
    echo "ERROR: geoid-to-ellipsoid transformation fails inside GDAL. PROJ not properly install or missing grid file (e.g., egm96_15.gtx)."
    echo "Raw output:"
    echo "$RESULT"
fi
