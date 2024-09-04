#!/bin/bash

show_help() {
    echo "Usage: update_minTempCoh.bash template_path [min_temp_coh] data_dir"
    echo ""
    echo "Options:"
    echo "  --help                Show this help message and exit"
    echo ""
    echo "Examples:"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template mintpy"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template 0.9 mintpy"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template miaplpy/network_single_reference"
    echo "  update_minTempCoh.bash \$TE/unittestGalapagosSenDT128.template 0.9 miaplpy/network_single_reference"
}
###################################################################################
function create_template_array() {
mapfile -t array < <(grep -e ^minsar -e ^mintpy -e ^miaplpy $1)
declare -gA template
for item in "${array[@]}"; do
  #echo "item: <$item>"
  IFS='=' ; read -a arr1 <<< "$item"
  item="${arr1[1]}"
  IFS='#' ; read -a arr2 <<< "$item"
  key="${arr1[0]}"
  key=$(echo $key | tr -d ' ')
  value="${arr2[0]}"
  shopt -s extglob
  value="${value##*( )}"          # Trim leading whitespaces
  value="${value%%*( )}"          # Trim trailing whitespaces
  shopt -u extglob
  #echo "key, value: <$key> <$value>"
  if [ ! -z "$key"  ]; then
     template[$key]="$value"
  fi
unset IFS
done
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

    create_template_array $template_path

    project_dir=$(get_project_dir "$template_path")
    cd "${SCRATCHDIR}/${project_dir}" || { echo "Failed to change directory to $project_dir"; exit 1; }
    touch "${data_dir}/temporalCoherence.h5"
    touch "${data_dir}/geo/geo_temporalCoherence.h5"
    if [[ -n "$min_temp_coh" ]]; then
        echo "Updating $project_name using minimum temporal coherence (mintpy.timeseries.minTempCoh) of  ${min_temp_coh}"
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

        # FA 8/24  This need to be in jobfile
        cmd="generate_mask.py ${data_dir}/temporalCoherence.h5 -m ${template[mintpy.networkInversion.minTempCoh]}  --nonzero -o ${data_dir}/maskTempCoh.h5"
        eval "$cmd"

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
template_path=""
min_temp_coh=""
data_dir=""

# Parse command-line options
while [[ "$1" != "" ]]; do
    case $1 in
        --help )
            show_help
            exit 0
            ;;
        * )
            if [[ -z "$template_path" ]]; then
                template_path=$1
            elif [[ -z "$min_temp_coh" && "$1" =~ ^[0-9]*\.?[0-9]+$ ]]; then
                min_temp_coh=$1
            elif [[ -z "$data_dir" ]]; then
                data_dir=$1
            fi
            ;;
    esac
    shift
done

# Check if template_path and data_dir are provided
if [[ -z "$template_path" ]]; then
    echo "Error: template_path is required."
    show_help
    exit 1
fi

if [[ -z "$data_dir" ]]; then
    echo "Error: data_dir is required."
    show_help
    exit 1
fi

# Main script execution
run_update "$template_path" "$min_temp_coh" "$data_dir"
