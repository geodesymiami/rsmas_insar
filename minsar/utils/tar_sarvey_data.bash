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
archive="${base_dir}.tar.gz"
parent_dir="$(dirname "$base_dir")"
subpath="$(basename "$base_dir")"

# List of target files/directories
targets=("inputs" "inverted" "config.json" "subset.log")

# Build the list of existing paths
include_args=()
for target in "${targets[@]}"; do
    full_path="${base_dir}/${target}"
    if [ -e "$full_path" ]; then
        include_args+=("${subpath}/${target}")
    else
        echo "Warning: ${full_path} does not exist, skipping."
    fi
done

# Only proceed if at least one file/dir exists
if [ "${#include_args[@]}" -eq 0 ]; then
    echo "Error: No files or directories found to archive."
    exit 1
fi

# Create the archive
tar -czf "$archive" -C "$parent_dir" "${include_args[@]}"

echo "Created archive: ${base_dir}.tar.gz"
