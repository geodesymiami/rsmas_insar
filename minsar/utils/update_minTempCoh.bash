#!/bin/bash

show_help() {
    echo "Usage: $0 [options] template_path [min_temp_coh]"
    echo ""
    echo "Options:"
    echo "  --help                Show this help message and exit"
    echo "  --dir DIR             Specify the directory"
    echo ""
    echo "Examples:"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template --dir mintpy"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template 0.9 --dir mintpy"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template --dir miaplpy/network_single_reference"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template 0.9 --dir miaplpy/network_single_reference"
    echo "  update_minTempCoh.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dir miaplpy_SN_201606_201608/network_delaunay_4"
}

get_project_dir() {
    local template_path="$1"
    echo "$(basename "$template_path" .template)"
}
replace_min_temp_coh() {
    local template_path="$1"
    local min_temp_coh="$2"

    sed -i.bak -E "s/(mintpy\.networkInversion\.minTempCoh\s*=\s*)([0-9.]+|auto)/\1${min_temp_coh}/" "$template_path"
    sed -i.bak -E "s/(miaplpy\.timeseries\.minTempCoh\s*=\s*)([0-9.]+|auto)/\1${min_temp_coh}/" "$template_path"
}

# display_job_status() {
#     local job1_id=$1
#     local job2_id=$2
#     while true; do
#         echo "Job status at $(date):"
#         squeue -j $job1_id,$job2_id
#         sleep 10
#     done
# }

display_job_status() {
    local job_ids=("$@")
    local job_ids_str=$(IFS=,; echo "${job_ids[*]}")
    while true; do
        echo "Job status at $(date):"
        squeue -j "$job_ids_str"
        sleep 10
    done
}
run_update() {
    local template_path="$1"
    local min_temp_coh="$2"
    local data_dir="$3"
    local project_dir

    project_dir=$(get_project_dir "$template_path")
    cd "${SCRATCHDIR}/${project_dir}" || { echo "Failed to change directory to $project_dir"; exit 1; }
    touch "${data_dir}/geo/geo_temporalCoherence.h5"
    if [[ -n "$min_temp_coh" ]]; then
        echo "Minimum temporal coherence: ${min_temp_coh}"
        replace_min_temp_coh "$template_path" "$min_temp_coh"
    fi

    if [[ "$data_dir" == *"mintpy"* ]]; then
        job1_output=$(sbatch -p $QUEUE_DEV smallbaseline_wrapper.job)
        job1_id=$(echo "$job1_output" | awk 'END {print $NF}')
        echo "First job submitted with ID: $job1_id"

        joblast_output=$(sbatch -p $QUEUE_DEV --dependency=afterok:$job1_id insarmaps.job)
        joblast_id=$(echo "$joblast_output" | awk 'END {print $NF}')
        echo "Second job submitted with ID: $joblast_id"
    else
        sed -i "s|SBATCH -t .:..:..|SBATCH -t 1:59:00|g" ${data_dir}/run_files/run_09_mintpy_timeseries_correction_0.job
        job1_output=$(sbatch -p $QUEUE_DEV ${data_dir}/run_files/run_09_mintpy_timeseries_correction_0.job)
        job1_id=$(echo "$job1_output" | awk 'END {print $NF}')
        echo "First job submitted with ID: $job1_id"

        job2_output=$(sbatch -p $QUEUE_DEV --dependency=afterok:$job1_id ${data_dir}/run_files/run_10_save_hdfeos5_radar_0.job)
        job2_id=$(echo "$job2_output" | awk 'END {print $NF}')
        echo "Second job submitted with ID: $job2_id"

        joblast_output=$(sbatch -p $QUEUE_DEV --dependency=afterok:$job2_id insarmaps.job)
        joblast_id=$(echo "$joblast_output" | awk 'END {print $NF}')
        echo "Third job submitted with ID: $joblast_id"       
    fi

    # display_job_status $job1_id $job2_id $joblast_id &
    display_job_status $job1_id $job2_id $joblast_id &


    echo "Waiting for job $joblast_id to complete..."
    while squeue -j $joblast_id | grep -q "$joblast_id"; do
        sleep 10
    done

    # Kill the background job status display
    kill %1
    tail -2 insarmaps.log
}

# Initialize variables
dir_option=""
template_path=""
min_temp_coh=""

# Parse command-line options
while [[ "$1" != "" ]]; do
    case $1 in
        --help )
            show_help
            exit 0
            ;;
        --dir )
            shift
            dir_option=$1
            ;;
        * )
            if [[ -z "$template_path" ]]; then
                template_path=$1
            elif [[ -z "$min_temp_coh" ]]; then
                min_temp_coh=$1
            fi
            ;;
    esac
    shift
done

# Check if template_path and dir_option are  provided
if [[ -z "$template_path" ]]; then
    echo "Error: template_path is required."
    show_help
    exit 1
fi

if [[ -z "$dir_option" ]]; then
    echo "Error: --dir option is required."
    show_help
    exit 1
fi

# Main script execution
run_update "$template_path" "$min_temp_coh" "$dir_option"
