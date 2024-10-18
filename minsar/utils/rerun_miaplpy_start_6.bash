#!/bin/bash

# Function to display help message
show_help() {
    echo "Usage: rerun_miaplpy_start_6.bash template_file miaplpy_dir"
    echo
    echo "This script cleans up the specified miaplpy directory and reruns the workflow with the given template."
    echo
    echo "Arguments:"
    echo "  template_file    The workflow template file (e.g., \$TE/SangaySenD142.template)"
    echo "  miaplpy_dir      The directory to clean (e.g., miaplpy_202101_202301)"
    echo
    echo "Example:"
    echo "  rerun_miaplpy_start_6.bash \$TE/SangaySenD142.template miaplpy_202101_202301"
    echo "  rerun_miaplpy_start_6.bash \$TE/SangaySenD142.template miaplpy_202101_202301"
    echo
    echo "Commands that will be executed:"
    echo "  rm -r miaplpy_dir/network_delaunay_4/*"
    echo "  rm -r miaplpy_dir/network_delaunay_4/inputs, geo and pic directories"
    echo "  rm -r miaplpy_dir/network_delaunay_4/JSON*"
    echo "  run_workflow.bash "$template_file" --dir "${miaplpy_dir}" --start 6"
    echo "  run_workflow.bash "$template_file" --jobfile insarmaps.job"
}

# Check for --help option
if [[ "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Check if the correct number of arguments are provided
if [[ $# -ne 2 ]]; then
    echo "Error: Incorrect number of arguments"
    show_help
    exit 1
fi

template_file=$1
miaplpy_dir=$2

# create name including $TE for concise log file
template_file_dir=$(dirname "$template_file")          # create name including $TE for concise log file
if   [[ $template_file_dir == $TEMPLATES ]]; then
    template_print_name="\$TE/$(basename $template_file)"
elif [[ $template_file_dir == $SAMPLESDIR ]]; then
    template_print_name="\$SAMPLESDIR/$(basename $template_file)"
else
    template_print_name="$template_file"
fi  
echo "$(date +"%Y%m%d:%H-%M") * rerun_miaplpy_start_6.bash $template_print_name ${@:2}" | tee -a log

echo "Cleaning up directory: $miaplpy_dir"
#rm -f "$miaplpy_dir"/network_*/*
find "$miaplpy_dir"/network_*/ -maxdepth 1 -type f -exec rm -f {} +
rm -f "$miaplpy_dir"/network_*/run_files/*.{e,o}
rm -r "$miaplpy_dir"/network_*/inputs
rm -r "$miaplpy_dir"/network_*/geo
rm -r "$miaplpy_dir"/nework_*/pic
rm -r "$miaplpy_dir"/network_*/JSON*

echo "Running workflow: run_workflow.bash $template_file --dir $miaplpy_dir --start 6"
run_workflow.bash "$template_file" --dir "${miaplpy_dir}" --start 6
run_workflow.bash "$template_file" --jobfile ${PWD}/insarmaps.job

echo "Clean and rerun completed successfully."

