#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 <directory>"
    echo "Create tar.gz archive of selected SARvey files."
    echo "Includes: inputs/, inverted/, config.json, subset.log"
    echo "Example:  $0 milleniumtower"
    exit 1
fi

base_dir="$1"

# Check existence of required files and folders
for item in inputs inverted config.json subset.log; do
    if [[ ! -e "${base_dir}/${item}" ]]; then
        echo "Error: ${base_dir}/${item} does not exist."
        exit 1
    fi
done

# Create tar.gz archive with correct relative paths
tar -czf "${base_dir}.tar.gz" -C "$(dirname "$base_dir")" \
    "$(basename "$base_dir")/inputs" \
    "$(basename "$base_dir")/inverted" \
    "$(basename "$base_dir")/config.json" \
    "$(basename "$base_dir")/subset.log"

echo "Created archive: ${base_dir}.tar.gz"
