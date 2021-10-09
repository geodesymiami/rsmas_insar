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
usage: run_workflow.bash custom_template_file [--start] [--stop] [--dostep] [--help]\n\
                                                                                   \n\
  Examples:                                                                        \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template              \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start 2    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep 4   \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --stop 8     \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start mintpy \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep insarmaps \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep minopy    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --minopy    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --append    \n\
                                                                                   \n\
 Processing steps (start/end/dostep): \n\
                                                                                 \n\
   ['1-16', 'mintpy', 'minopy', 'insarmaps' ]                                          \n\
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
    PROJECT_NAME=$(basename "$1" | awk -F ".template" '{print $1}')
fi
WORKDIR=$SCRATCHDIR/$PROJECT_NAME
cd $WORKDIR

randomorder=false
rapid=false
append=false
tmp=true
tmp_flag_str="--tmp"
run_files_name="run_files_tmp"
wait_time=30

startstep=1
stopstep="insarmaps"

start_datetime=$(date +"%Y%m%d:%H-%m")
echo "${start_datetime} * run_workflow.bash ${WORKDIR} ${@:2}" >> "${WORKDIR}"/log

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
        --rapid)
            rapid=true
            wait_time=10
            shift
            ;;
        --append)
            append=true
            shift
            ;;
        --minopy)
            minopy_flag=true
            shift
            ;;
        --tmp)
            tmp=true
            tmp_flag_str="--tmp"
            run_files_name="run_files_tmp"
            shift
            ;;
        --no_tmp)
            tmp=false
            tmp_flag_str="--no_tmp"
            run_files_name="run_files"
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ $startstep == "minopy" ]]; then
   minopy_flag=true
fi

# IO load for each step. For step_io_load=1 the maximum tasks allowed is step_max_tasks_unit
# for step_io_load=2 the maximum tasks allowed is step_max_tasks_unit/2

# declare -A  step_io_load_list
# step_io_load_list=(
#     [unpack_topo_reference]=1
#     [unpack_secondary_slc]=1
#     [average_baseline]=1
#     [extract_burst_overlaps]=1
#     [overlap_geo2rdr]=1
#     [overlap_resample]=1
#     [pairs_misreg]=1
#     [timeseries_misreg]=1
#     [fullBurst_geo2rdr]=1
#     [fullBurst_resample]=1
#     [extract_stack_valid_region]=1
#     [merge_reference_secondary_slc]=1
#     [generate_burst_igram]=1
#     [merge_burst_igram]=1
#     [filter_coherence]=1
#     [unwrap]=1

#     [smallbaseline_wrapper]=1
#     [insarmaps]=1

#     [minopy_crop]=1
#     [minopy_inversion]=1
#     [minopy_ifgrams]=1
#     [minopy_unwrap]=1
#     [minopy_un-wrap]=1
#     [minopy_mintpy_corrections]=1

    
# )

##### For proper logging to both file and stdout #####
num_logfiles=$(ls $WORKDIR/workflow.*.log | wc -l)
test -f $WORKDIR/workflow.0.log  || touch workflow.0.log
if $append; then num_logfiles=$(($num_logfiles-1)); fi
logfile_name="${WORKDIR}/workflow.${num_logfiles}.log"
#printf '' > $logfile_name
tail -f $logfile_name & 
trap "pkill -P $$" EXIT
exec 1>>$logfile_name 2>>$logfile_name
######################################################

RUNFILES_DIR=$WORKDIR"/"$run_files_name

if [[ $minopy_flag == "true" ]]; then
   RUNFILES_DIR=$WORKDIR"/minopy/run_files"
fi

#find the last job (11 for 'geometry' and 16 for 'NESD', 9 for stripmap) and remove leading zero
job_file_arr=( $RUNFILES_DIR/run_*_0.job )
last_job_file="${job_file_arr[-1]}"
last_job_file=${last_job_file##*/}
last_job_file_number=${last_job_file:4:2}
#last_job_file_number=$( echo $last_job_file_number | sed 's/^0*// ')     # FA 9/21 sed command did not always work well
last_job_file_number=$(echo $((10#${last_job_file_number})))

if [[ $startstep == "ifgrams" || $startstep == "minopy" ]]; then
    startstep=1
elif [[ $startstep == "mintpy" ]]; then
    startstep=$((last_job_file_number+1))
elif [[ $startstep == "insarmaps" ]]; then
    startstep=$((last_job_file_number+2))
fi

if [[ $stopstep == "ifgrams" || $stopstep == "minopy" ]]; then
    stopstep=$last_job_file_number
elif [[ $stopstep == "mintpy" ]]; then
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

defaults_file="${RSMASINSAR_HOME}/minsar/defaults/job_defaults.cfg"

echo "Started at: $(date +"%Y-%m-%d %H:%M:%S")"
for g in "${globlist[@]}"; do
    files=($(ls -1v $g ))
    if $randomorder; then
        files=( $(echo "${files[@]}" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
    fi

    echo "Jobfiles to run:"
    printf "%s\n" "${files[@]}"

    jobnumbers=()
    file_pattern=$(echo "${files[0]}" | grep -oP "(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")
    #step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)|insarmaps|smallbaseline_wrapper")
    
    #step_io_load=$(cat $defaults_file | grep $step_name | awk '{print $7}')
    #step_max_tasks=$(echo "$SJOBS_STEP_MAX_TASKS/$step_io_load" | bc | awk '{print int($1)}')

    #sbc_command="submit_jobs.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $SJOBS_TOTAL_MAX_TASKS"

    sbc_command="submit_jobs.bash $file_pattern"

    if $randomorder; then
        sbc_command="$sbc_command --random"
        echo "Jobs are being submitted in random order. Submission order is likely different from the order above."
    fi
    if $rapid; then
        sbc_command="$sbc_command --rapid"
        echo "Rapid job submission enabled."
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
        sleep $wait_time

        for (( j=0; j < "${#jobnumbers[@]}"; j++)); do
            file=${files[$j]}
            file_pattern="${file%.*}"
            step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            step_name_long=$(echo $file_pattern | grep -oP "(?<=$run_files_name\/)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            jobnumber=${jobnumbers[$j]}
            state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -3 | tail -1 )

            if [[ $state == *"COMPLETED"* ]]; then
                num_complete=$(($num_complete+1))
            elif [[ $state == *"RUNNING"* ]]; then
                num_running=$(($num_running+1))
            elif [[ $state == *"PENDING"* ]]; then
                num_pending=$(($num_pending+1))
            elif [[ $state == *"TIMEOUT"* || $state == *"NODE_FAIL"* ]]; then
                num_timeout=$(($num_timeout+1))
                #step_max_tasks=$(echo "$SJOBS_STEP_MAX_TASKS/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')
        
                if [[ $state == *"TIMEOUT"* ]]; then
                    init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)
                    echo "${file} timedout with walltime of ${init_walltime}."
                                    
                    # Compute a new walltime and update the job file
                    update_walltime.py "$file" &> /dev/null
                    updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)

                    datetime=$(date +"%Y-%m-%d:%H-%M")
                    echo "${datetime}: re-running: ${file}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log
                    echo "Resubmitting file (${file}) with new walltime of ${updated_walltime}"
                fi

                jobnumbers=($(remove_from_list $jobnumber "${jobnumbers[@]}"))
                files=($(remove_from_list $file "${files[@]}"))

                # Resubmit as a new job number
                #jobnumber=$(submit_jobs.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $SJOBS_TOTAL_MAX_TASKS 2> /dev/null) 
                jobnumber=$(submit_jobs.bash $file_pattern 2> /dev/null)
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
                echo "Strange job state: $state, encountered."
                continue;
            fi

        done

        num_waiting=$(($num_jobs-$num_complete-$num_running-$num_pending))

        printf "%s, %s, %-7s: %-12s, %-10s, %-10s, %-12s.\n" "$PROJECT_NAME" "$step_name_long" "$num_jobs jobs" "$num_complete COMPLETED" "$num_running RUNNING" "$num_pending PENDING" "$num_waiting WAITING"
    done


    # Run check_job_output.py on all files
    cmd="check_job_outputs.py  ${files[@]} $tmp_flag_str"
    echo "$cmd"
    $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
            echo "Error in run_workflow.bash: check_job_outputs.py exited with code ($exit_status)."
            exit 1
       fi
    echo
done

