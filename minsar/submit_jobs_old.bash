##! /bin/bash

function get_active_jobids {
    running_tasks=$(squeue -u $USER --format="%A" -rh)
    job_ids=($(echo $running_tasks | grep -oP "\d{4,}"))
    echo "${job_ids[@]}"
    return 0
}

function num_tasks_for_file {
    file=$1
    file="${file%.*}"
    if [[ "$file" == *"insarmaps"* || "$file" == *"smallbaseline_wrapper"* ]]; then
        num_tasks=1
    else
        num_tasks=$(cat $file | wc -l)
    fi
    echo $num_tasks
    return 0
}

function compute_num_tasks {
    stepname=$1

    job_ids=($(get_active_jobids))

    tasks=0
    for j in "${job_ids[@]}"; do
        task_file=$(scontrol show jobid -dd $j | grep -oP "(?<=Command=)(.*)(?=.job)")
        if [[ "$task_file" == *"$stepname"* ]]; then
            num_tasks=$(num_tasks_for_file $task_file)
            ((tasks=tasks+$num_tasks))
        fi
    done

    echo $tasks
    return 0
}

# function compute_tasks_for_step {
#     file=$1
#     stepname=$2

#     IFS=$'\n'
#     running_tasks=$(squeue -u $USER --format="%A" -rh)
#     job_ids=($(echo $running_tasks | grep -oP "\d{4,}"))

#     unset IFS

#     tasks=0
#     for j in "${job_ids[@]}"; do
# 	task_file=$(scontrol show jobid -dd $j | grep -oP "(?<=Command=)(.*)(?=.job)")
# 	if [[ "$task_file" == *"$stepname"* ]]; then
# 	    task_file=$(scontrol show jobid -dd $j | grep -oP "(?<=Command=)(.*)(?=.job)")
# 	    if [[ "$task_file" == *"insarmaps"* || "$task_file" == *"smallbaseline_wrapper"* ]]; then
# 		num_tasks=1
# 	    else
# 		num_tasks=$(cat $task_file | wc -l)
# 	    fi

# 	    ((tasks=tasks+$num_tasks))
# 	fi
#     done

#     echo $tasks
#     return 0
# }

function submit_job_conditional {

    declare -A  step_io_load_list

    step_max_tasks_unit=1500
    total_max_tasks=3000

    # IO load for each step. For step_io_load=1 the maximum tasks allowed is step_max_tasks_unit
    # for step_io_load=2 the maximum tasks allowed is step_max_tasks_unit/2
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
        [merge_burst_igram]=3
        [filter_coherence]=1
        [unwrap]=1

        [smallbaseline_wrapper]=1
        [insarmaps]=1
    )

    file=$1

    # Isolate stepname from file name. Could be an ISCE runfile (run_00_*.job), insarmaps.job, or smallbaseline_wrapper.job
    step_name=$(echo $file | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")

    # Compute maximum allowable tasks for this step
    step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')
    
    time_elapsed=0
    
    while [[ $time_elapsed -lt 604800 ]]; do
	# Compute number of total active tasks and number of active tasks for curent step
	num_active_tasks_total=$(compute_num_tasks)
	num_active_tasks_step=$(compute_num_tasks $step_name)

	# Get number of tasks associated with current jobfile
	# insarmaps.job and smallbaseline_wrapper.job always have 1 task.
	# ISCE runfiles have number of tasks equal to number of lines in associated launcher script
	# Launcher script: "run_01_unpack_topo_reference_0.job" -> "run_01_unpack_topo_reference_0"    
	num_tasks_job=$(num_tasks_for_file $file)
	
	# Compute new total number of tasks and tasks for current step
	new_tasks_step=$(($num_active_tasks_step+$num_tasks_job))
	new_tasks_total=$(($num_active_tasks+$num_tasks_job))
	
	# Get active number of running jobs
	num_active_jobs=$(squeue -u $USER -h -t running,pending -r | wc -l )
	
	echo "Number of running/pending jobs: $num_active_jobs" >&2 
	echo "$num_active_tasks_total running/pending tasks across all jobs (maximum $total_max_tasks)" >&2
	echo "step $step_name: $num_active_tasks_step running/pending tasks (maximum $step_max_tasks)" >&2
	echo "$(basename $file): $num_tasks_job additional tasks" >&2
	
	if [[ $num_active_jobs -lt $MAX_JOBS_PER_QUEUE ]] && [[ $new_tasks_step -lt $step_max_tasks ]] && [[ $new_tasks_total -lt $total_max_tasks ]]; then
            job_submit_message=$(sbatch $file | grep "Submitted batch job")
            exit_status="$?"
            if [[ $exit_status -ne 0 ]]; then
		echo "sbatch message: $job_submit_message" >&2
		echo "sbatch submit error: exit code $exit_status. Sleep 60 seconds and try again" >&2
		sleep 30
		job_submit_message=$(sbatch $file | grep "Submitted batch job")
		exit_status="$?"
		if [[ $exit_status -ne 0 ]]; then
                    echo "sbatch message: $job_submit_message" >&2
                    echo "sbatch submit error: exit code $exit_status. Exiting with status code 1." >&2
		    sleep 60
		fi
            fi

            jobnumber=$(grep -oE "[0-9]{7}" <<< $job_submit_message)

            echo $jobnumber
            return 0
	else
            if [[ $num_active_jobs -ge $MAX_JOBS_PER_QUEUE ]]; then
		echo "Couldnt submit job (${file}), because there are $num_active_jobs active jobs right now (max: $MAX_JOBS_PER_QUEUE). Waiting 5 minutes to try again." >&2
            elif [[ $new_tasks_step -ge $step_max_tasks ]]; then
		echo "Couldnt submit job (${file}), because there would be $new_tasks_step active tasks for this step right now (max: $step_max_tasks). Waiting 5 minutes to try again." >&2
            elif [[ $new_tasks_total -ge $total_max_tasks ]]; then
		echo "Couldnt submit job (${file}), because there would be $new_tasks_total total active tasks right now (max: $total_max_tasks). Waiting 5 minutes to try again." >&2
            fi
	    
            sleep 30
	    time_elapsed=$((time_elapsed+300))
	    echo "Time Elapsed: $time_elapsed of 604800s (7 days)" >&2
	fi
    done
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
	fname="$WORKDIR/smallbaseline_wrapper*.job"
    else
	fname="$WORKDIR/insarmaps*.job"
    fi
    globlist+=("$fname")
done


for g in "${globlist[@]}"; do
    files=($g)
    echo "Jobfiles to run: ${files[@]}"
    
    # Submit all of the jobs and record all of their job numbers
    jobnumbers=()
    for (( f=0; f < "${#files[@]}"; f++ )); do
	file=${files[$f]}

        jobnumber=$(submit_job_conditional $file)
        exit_status="$?"
        if [[ $exit_status -eq 0 ]]; then
            jobnumbers+=("$jobnumber")
        else
            f=$((f-1))
            sleep 300 # sleep for 5 minutes
        fi

    done
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
                echo "$(basename $WORKDIR) $(basename "$file"), ${jobnumber} is not finished yet. Current state is '${state}'"
            fi

            state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' | head -3 | tail -1 )

                # Check if "COMPLETED" is anywhere in the state string variables.
                # This gets rid of some strange special character issues.
            if [[ $state == *"TIMEOUT"* ]] && [[ $state != "" ]]; then
                jf=${files[$j]}
                init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)
                
                echo "${jobnumber} timedout due to too low a walltime (${init_walltime})."
                                
                # Compute a new walltime and update the job file
                update_walltime.py "$jf" &> /dev/null

                updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)

                datetime=$(date +"%Y-%m-%d:%H-%M")
                echo "${datetime}: re-running: ${jf}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log

                echo "Resubmitting file (${jf}) with new walltime of ${updated_walltime}"

                # Resubmit as a new job number
                jobnumber=$(submit_job_conditional $jf)
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

        echo Job"${jobnumber} is finished."

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
