##! /bin/bash

function abbreviate {
    abb=$1
    if [[ "${#abb}" -gt $2 ]]; then
        abb=$(echo "$(echo $(basename $abb) | cut -c -$3)...$(echo $(basename $abb) | rev | cut -c -$4 | rev)")
    fi
    echo $abb
}

function remove_from_list {
    var=$1
    shift
    list=("$@")
    new_list=() # Not strictly necessary, but added for clarity
    
    #echo "VAR: $var"
    for item in ${list[@]}
    do
        #echo "$item"
        if [ "$item" != "$var" ]
        then
            new_list+=("$item")
        fi
    done
    list=("${new_list[@]}")
    unset new_list
    echo "${list[@]}"
}

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                         \n\
Job submission script
usage: submit_jobs.bash custom_template_file [--start] [--stop] [--dostep] [--help]\n\
                                                                                   \n\
  Examples:                                                                        \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template              \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start 2    \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep 4   \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --stop 8     \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start timeseries \n\
      submit_jobs.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep insarmaps \n\
                                                                                   \n\
 Processing steps (start/end/dostep): \n\
                                                                                 \n\
   ['1-16', 'timeseries', 'insarmaps' ]                                          \n\
                                                                                 \n\
   In order to use either --start or --dostep, it is necessary that a            \n\
   previous run was done using one of the steps options to process at least      \n\
   through the step immediately preceding the starting step of the current run.  \n\
                                                                                 \n\
   --start STEP          start processing at the named step [default: load_data].\n\
   --end STEP, --stop STEP                                                       \n\
                         end processing at the named step [default: upload]      \n\
   --dostep STEP         run processing at the named step only                   \n 
     "
    printf "$helptext"
    exit 0;
else
    PROJECT_NAME=$(basename "$1" | cut -d. -f1)
fi
WORKDIR=$SCRATCHDIR/$PROJECT_NAME
RUNFILES_DIR=$WORKDIR"/run_files"

cd $WORKDIR

randomorder=false
startstep=1
stopstep="insarmaps"

start_datetime=$(date +"%Y%m%d:%H-%m")
echo "${start_datetime} * submit_jobs.bash ${WORKDIR} ${@:2}" >> "${WORKDIR}"/log

while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        --start)
            startstep="$2"
            shift # past argument
            shift # past value
            ;;
        --stop)
                stopstep="$2"
                shift
                shift
                ;;
        --dostep)
            startstep="$2"
            stopstep="$2"
            shift
            shift
            ;;
        --random)
            randomorder=true
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

step_max_tasks_unit=500
total_max_tasks=1000
# IO load for each step. For step_io_load=1 the maximum tasks allowed is step_max_tasks_unit
# for step_io_load=2 the maximum tasks allowed is step_max_tasks_unit/2
declare -A  step_io_load_list
step_io_load_list=(
    [unpack_topo_reference]=1
    [unpack_secondary_slc]=1
    [average_baseline]=1
    [extract_burst_overlaps]=1
    [overlap_geo2rdr]=1
    [overlap_resample]=1
    [pairs_misreg]=1
    [timeseries_misreg]=1
    [fullBurst_geo2rdr]=1
    [fullBurst_resample]=1
    [extract_stack_valid_region]=1
    [merge_reference_secondary_slc]=1
    [generate_burst_igram]=1
    [merge_burst_igram]=1
    [filter_coherence]=1
    [unwrap]=1

    [smallbaseline_wrapper]=1
    [insarmaps]=1
)




#find the last job (11 for 'geometry' and 16 for 'NESD')
job_file_arr=(run_files/run_*_0.job)
last_job_file=${job_file_arr[-1]}
last_job_file_number=${last_job_file:14:2}

if [[ $startstep == "ifgrams" ]]; then
    startstep=1
elif [[ $startstep == "timeseries" ]]; then
    startstep=$((last_job_file_number+1))
elif [[ $startstep == "insarmaps" ]]; then
    startstep=$((last_job_file_number+2))
fi

if [[ $stopstep == "ifgrams" ]]; then
    stopstep=$last_job_file_number
elif [[ $stopstep == "timeseries" ]]; then
    stopstep=$((last_job_file_number+1))
elif [[ $stopstep == "insarmaps" ]]; then
    stopstep=$((last_job_file_number+2))
fi

for (( i=$startstep; i<=$stopstep; i++ )) do
    stepnum="$(printf "%02d" ${i})"
    if [[ $i -le $last_job_file_number ]]; then
        fname="$RUNFILES_DIR/run_${stepnum}_*.job"
    elif [[ $i -eq $((last_job_file_number+1)) ]]; then
        fname="$WORKDIR/smallbaseline_wrapper.job"
    else
        fname="$WORKDIR/insarmaps.job"
    fi
    globlist+=("$fname")
done


for g in "${globlist[@]}"; do
    files=($(ls -1v $g ))
    if $randomorder; then
        files=( $(echo "${files[@]}" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
    fi

    echo "Jobfiles to run:"
    printf "%s\n" "${files[@]}"

    jobnumbers=()
    file_pattern=$(echo "${files[0]}" | grep -oP "(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")
    step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)|insarmaps|smallbaseline_wrapper")

    step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')

    sbc_command="sbatch_conditional.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $total_max_tasks"
    if $randomorder; then
        sbc_command="$sbc_command --random"
        echo "Jobs are being submitted in random order. Submission order is likely different from the order above."
    fi
    jns=$($sbc_command)

    exit_status="$?"
    if [[ $exit_status -eq 0 ]]; then
        jobnumbers=($jns)
    fi

    unset IFS
    echo "Jobs submitted: ${jobnumbers[@]}"
    sleep 5

    # Wait for each job to complete
    num_jobs=${#jobnumbers[@]}
    num_complete=0
    num_running=0
    num_pending=0
    num_timeout=0
    num_waiting=0

    while [[ $num_complete -lt $num_jobs ]]; do
        num_complete=0
        num_running=0
        num_pending=0
        num_waiting=0
        sleep 30
        for (( j=0; j < "${#jobnumbers[@]}"; j++)); do
            file=${files[$j]}
            file_pattern="${file%.*}"
            step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            step_name_long=$(echo $file_pattern | grep -oP "(?<=run_files\/)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            jobnumber=${jobnumbers[$j]}
            state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -3 | tail -1 )

            if [[ $state == *"COMPLETED"* ]]; then
                num_complete=$(($num_complete+1))
            elif [[ $state == *"RUNNING"* ]]; then
                num_running=$(($num_running+1))
            elif [[ $state == *"PENDING"* ]]; then
                num_pending=$(($num_pending+1))
            elif [[ $state == *"TIMEOUT"* ]]; then
                num_timeout=$(($num_timeout+1))
                step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')
        
                init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)
                echo "Timedout with walltime of ${init_walltime}."
                                
                # Compute a new walltime and update the job file
                update_walltime.py "$file" &> /dev/null
                updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)

                datetime=$(date +"%Y-%m-%d:%H-%M")
                echo "${datetime}: re-running: ${file}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log
                echo "Resubmitting file (${file}) with new walltime of ${updated_walltime}"

                jobnumbers=($(remove_from_list $jobnumber "${jobnumbers[@]}"))
                files=($(remove_from_list $jf "${files[@]}"))

                # Resubmit as a new job number
                jobnumber=$(sbatch_conditional.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $total_max_tasks 2> /dev/null) 

                exit_status="$?"
                if [[ $exit_status -eq 0 ]]; then
                    jobnumbers+=("$jobnumber")
                    files+=("$file")
                    j=$(($j-1))
                    echo "Resubmitted as jobumber: ${jobnumber}."
                else
                    echo "Error on resubmit for $jobnumber. Exiting."
                    exit 1
                fi
            elif [[ ( $state == *"FAILED"* || $state ==  *"CANCELLED"* ) ]]; then
                echo "Job failed. Exiting."
                exit 1; 
            else
                continue;
            fi

        done

        num_waiting=$(($num_jobs-$num_complete-$num_running-$num_pending))

        printf "%s, %s, %-7s: %-12s, %-10s, %-10s, %-12s.\n" "$PROJECT_NAME" "$step_name_long" "$num_jobs jobs" "$num_complete COMPLETED" "$num_running RUNNING" "$num_pending PENDING" "$num_waiting WAITING"
    done


    # Run check_job_output.py on all files
    cmd="check_job_outputs.py  ${files[@]}"
    echo "$cmd"
    $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
            echo "Error in submit_jobs.bash: check_job_outputs.py exited with code ($exit_status)."
            exit 1
       fi
    echo
done

