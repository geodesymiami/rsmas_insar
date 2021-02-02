##!/bin/bash

function get_active_jobids {
    running_tasks=$(squeue -u $USER --format="%A" -rh)
    job_ids=($(echo $running_tasks | grep -oP "\d{4,}"))
    echo "${job_ids[@]}"
    return 0
}

function num_tasks_for_file {
    file=$1
    file="${file%.*}"
    if [[ ! -f $file ]]; then
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

file_pattern=$1
step_name=$file_pattern
step_max_tasks=1500
total_max_tasks=3000
max_time=604800

while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        --step_name)
            step_name="$2"
            shift # past argument
            shift # past value
            ;;
        --step_max_tasks)
                step_max_tasks="$2"
                shift
                shift
                ;;
        --total_max_tasks)
            total_max_tasks="$2"
            shift
            shift
            ;;
        --max_time)
            max_time="$2"
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

files=($file_pattern*.job)
for f in "${files[@]}"; do
    time_elapsed=0
    echo "Submitting file: $f" >&2
    while [[ $time_elapsed -lt $max_time ]]; do
        # Compute number of total active tasks and number of active tasks for curent step
        num_active_tasks_total=$(compute_num_tasks)
        num_active_tasks_step=$(compute_num_tasks $step_name)

        # Get number of tasks associated with current jobfile
        # insarmaps.job and smallbaseline_wrapper.job always have 1 task.
        # ISCE runfiles have number of tasks equal to number of lines in associated launcher script
        # Launcher script: "run_01_unpack_topo_reference_0.job" -> "run_01_unpack_topo_reference_0"    
        num_tasks_job=$(num_tasks_for_file $f)
        
        # Compute new total number of tasks and tasks for current step
        new_tasks_step=$(($num_active_tasks_step+$num_tasks_job))
        new_tasks_total=$(($num_active_tasks+$num_tasks_job))
        
        # Get active number of running jobs
        num_active_jobs=$(squeue -u $USER -h -t running,pending -r | wc -l )
        
        echo "Number of running/pending jobs: $num_active_jobs" >&2  
        echo "$num_active_tasks_total running/pending tasks across all jobs (maximum $total_max_tasks)" >&2 
        echo "step $step_name: $num_active_tasks_step running/pending tasks (maximum $step_max_tasks)" >&2
        echo "$(basename $f): $num_tasks_job additional tasks" >&2
        
        if [[ $num_active_jobs -lt $MAX_JOBS_PER_QUEUE ]] && [[ $new_tasks_step -lt $step_max_tasks ]] && [[ $new_tasks_total -lt $total_max_tasks ]]; then
            job_submit_message=$(sbatch $f | grep "Submitted batch job")
            exit_status="$?"
            if [[ $exit_status -ne 0 ]]; then
                echo "sbatch message: $job_submit_message" >&2 
                echo "sbatch submit error: exit code $exit_status. Sleep 60 seconds and try again" >&2 
                sleep 30
                job_submit_message=$(sbatch $f | grep "Submitted batch job")
                exit_status="$?"
                if [[ $exit_status -ne 0 ]]; then
                    echo "sbatch message: $job_submit_message" >&2 
                    echo "sbatch submit error: exit code $exit_status. Exiting with status code 1." >&2 
                    sleep 60
                fi
            fi

            jobnumber=$(grep -oE "[0-9]{7}" <<< $job_submit_message)

            echo $jobnumber
            break
        else
            if [[ $num_active_jobs -ge $MAX_JOBS_PER_QUEUE ]]; then
                echo "Couldnt submit job (${f}), because there are $num_active_jobs active jobs right now (max: $MAX_JOBS_PER_QUEUE). Waiting 5 minutes to try again." >&2 
            elif [[ $new_tasks_step -ge $step_max_tasks ]]; then
                echo "Couldnt submit job (${f}), because there would be $new_tasks_step active tasks for this step right now (max: $step_max_tasks). Waiting 5 minutes to try again." >&2 
            elif [[ $new_tasks_total -ge $total_max_tasks ]]; then
                echo "Couldnt submit job (${f}), because there would be $new_tasks_total total active tasks right now (max: $total_max_tasks). Waiting 5 minutes to try again." >&2 
            fi
        fi

        sleep 300
        time_elapsed=$((time_elapsed+300))
        echo "Time Elapsed: $time_elapsed of $max_time (7 days)" >&2 
    done
done

# Isolate stepname from file name. Could be an ISCE runfile (run_00_*.job), insarmaps.job, or smallbaseline_wrapper.job
#step_name=$(echo $file | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")

# Compute maximum allowable tasks for this step
#step_max_tasks=$(echo "$step_max_tasks_unit/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')

if [[ $time_elapsed -ge $max_time ]]; then
    exit 1
else
    exit 0
fi
