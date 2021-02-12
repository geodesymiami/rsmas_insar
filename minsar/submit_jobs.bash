##! /bin/bash

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
	fname="$WORKDIR/smallbaseline_wrapper_*.job"
    else
	fname="$WORKDIR/insarmaps_*.job"
    fi
    globlist+=("$fname")
done


for g in "${globlist[@]}"; do
    files=($g)
    echo "Jobfiles to run: ${files[@]}"
    jobnumbers=()
    #echo "File 0: ${files[0]}"
    file_pattern=$(echo "${files[0]}" | grep -oP "(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")
    step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)|insarmaps|smallbaseline_wrapper")
    #echo "file_pattern: $file_pattern"
    #echo "step_name :$step_name"

    step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')
    jns=$(sbatch_conditional.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $total_max_tasks)
    exit_status="$?"
    if [[ $exit_status -eq 0 ]]; then
	jobnumbers=($jns)
    fi

    unset IFS
    echo "Jobs submitted: ${jobnumbers[@]}"
    sleep 5
    # Wait for each job to complete
    
    for (( j=0; j < "${#jobnumbers[@]}"; j++)); do
        jobnumber=${jobnumbers[$j]}

        # Parse out the state of the job from the sacct function (3rd line following ----- if there are multiple steps)
        # Format state to be all uppercase (PENDING, RUNNING, or COMPLETED)
        # and remove leading whitespace characters.
        state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' | head -3 | tail -1 )

        # Keep checking the state while it is not "COMPLETED"
        secs=0
        while true; do
            
            # Only print every so often, not every 30 seconds
            if [[ $(( $secs % 30)) -eq 0 ]]; then
                echo "$(basename $WORKDIR) $(basename "${files[$j]}"), ${jobnumber} is not finished yet. Current state is '${state}'"
            fi

            state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' | head -3 | tail -1 )

            # Check if "COMPLETED" is anywhere in the state string variables.
            # This gets rid of some strange special character issues.
            if [[ $state == *"TIMEOUT"* ]] && [[ $state != "" ]]; then
                jf=${files[$j]}
		file_pattern="${jf%.*}"

		step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
		step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')

        
                init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)
                
                echo "${jobnumber} timedout due to too low a walltime (${init_walltime})."
                                
                # Compute a new walltime and update the job file
                update_walltime.py "$jf" &> /dev/null

                updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)

                datetime=$(date +"%Y-%m-%d:%H-%M")
                echo "${datetime}: re-running: ${jf}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log

                echo "Resubmitting file (${jf}) with new walltime of ${updated_walltime}"
                # Resubmit as a new job number
                jobnumber=$(sbatch_conditional.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $total_max_tasks)
                exit_status="$?"
                if [[ $exit_status -eq 0 ]]; then
                    jobnumbers+=("$jobnumber")
                    files+=("$jf")
                    echo "${jf} resubmitted as jobumber: ${jobnumber}"
                else
                    echo "sbatch re-submit error message: $jobnumber"
                    echo "sbatch re-submit error: exit code $exit_status. Exiting."
                    exit 1
                fi

                break;

        elif [[ $state == *"COMPLETED"* ]] && [[ $state != "" ]]; then
                state="COMPLETED"
                echo "${jobnumber} is complete"
                break;

            elif [[ ( $state == *"FAILED"* ) &&  $state != "" ]]; then
                echo "${jobnumber} FAILED. Exiting with status code 1."
                exit 1; 
            elif [[ ( $state ==  *"CANCELLED"* ) &&  $state != "" ]]; then
                echo "${jobnumber} was CANCELLED. Exiting with status code 1."
                exit 1; 
            fi

            # Wait for 30 second before chcking again
            sleep 30
            ((secs=secs+30))
            
            done

        echo "Job ${jobnumber} is finished."

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
