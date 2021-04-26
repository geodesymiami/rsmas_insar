##!/bin/bash

function abbreviate {
    abb=$1
    if [[ "${#abb}" -gt $2 ]]; then
        abb=$(echo "$(echo $(basename $abb) | cut -c -$3)...$(echo $(basename $abb) | rev | cut -c -$4 | rev)")
    fi
    echo $abb
}

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

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    helptext="                                                                         \n\
Job submission script that handles conditional job submission based on io load.
usage: sbatch_conditional.bash job_file_pattern [--step_name] [--step_max_tasks] [--total_max_tasks] [--max_time] [--help]\n\
                                                                                                         \n\
  Examples:                                                                                              \n\
      sbatch_conditional.bash run_01                                                                     \n\
      sbatch_conditional.bash run_01 --step_name unpack_topo_reference                                   \n\
      sbatch_conditional.bash run_01 --step_name unpack_topo_reference --step_max_tasks 100              \n\
      
 Default option values (step_max_tasks/total_max_tasks/max_time):                        \n\
                                                                                         \n\
   --step_max_tasks  NUM         1500                                                    \n\
   --total_max_tasks NUM         3000                                                    \n\
   --max_time        NUM         604800                                                  \n\
                                                                                         \n\
   --step_name       STR         same as job_file_pattern

"
    printf "$helptext"
    exit 0;
fi

file_pattern=$1
step_name=$file_pattern
step_max_tasks=1500
total_max_tasks=3000
max_time=604800
randomorder=false

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

printf "%0.s-" {1..146} >&2
printf "\n" >&2
printf "| %-20s | %-16s | %-17s | %-18s | %-19s | %-14s | %-20s | %s \n" "File Name" "Additional Tasks" "Step Active Tasks" "Total Active Tasks" "Step Processed Jobs" "Active Jobs"  "Message" >&2
printf "%0.s-" {1..146} >&2
printf "\n" >&2


jns=()
files=( $(ls -1v $file_pattern*.job) )
if $randomorder; then
    files=( $(echo "${files[@]}" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
fi
i=0
for f in "${files[@]}"; do
    time_elapsed=0
    i=$((i+1))
    #echo "Submitting file: $f" >&2
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
        
        #echo "Number of running/pending jobs: $num_active_jobs" >&2  
        #echo "$num_active_tasks_total running/pending tasks across all jobs (maximum $total_max_tasks)" >&2 
        #echo "step $step_name: $num_active_tasks_step running/pending tasks (maximum $step_max_tasks)" >&2
        #echo "$(basename $f): $num_tasks_job additional tasks" >&2
        fname=$(basename $f)
        abb_fname=$(abbreviate $fname 20 10 7)

        printf "| %-20s | %-16s | %-17s | %-18s | %-19s | %-14s | %s" "$abb_fname" "$num_tasks_job" "$num_active_tasks_step/$step_max_tasks" "$num_active_tasks_total/$total_max_tasks" "$i/${#files[@]}" "$num_active_jobs/$MAX_JOBS_PER_QUEUE" >&2

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
            printf "%-20s |\n" "Submitted: $jobnumber" >&2
            jns+=($jobnumber)
            break
        else
            printf "%-20s |\n" "Wait 5 min" >&2
        fi

        sleep 300
        time_elapsed=$((time_elapsed+300))
        #echo "Time Elapsed: $time_elapsed of $max_time (7 days)" >&2 
    done
done

printf "%0.s-" {1..146} >&2
printf "\n" >&2

if [[ $time_elapsed -ge $max_time ]]; then
    exit 1
else
    echo "${jns[@]}"
    exit 0
fi

