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

if [[ $1 == *".job"* ]]; then
    file_pattern=$1
else
    file_pattern="$1*.job"
fi

step_name=$file_pattern
step_max_tasks=1500
total_max_tasks=3000
max_time=604800
randomorder=false
wait_time=300

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
        --rapid)
            wait_time=60
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

printf "%0.s-" {1..153} >&2
printf "\n" >&2
#printf "| %-20s | %-11s | %-17s | %-18s | %-19s | %-11s | %-35s | %s \n" "File Name" "Extra Tasks" "Step Active Tasks" "Total Active Tasks" "Step Processed Jobs" "Active Jobs"  "Message" >&2
printf "| %-20s | %-5s | %-9s | %-9s | %-9s | %-7s | %-70s | %s \n" "" "" "Step" "Total" "Step" ""  "" >&2
printf "| %-20s | %-5s | %-9s | %-9s | %-9s | %-7s | %-70s | %s \n" "" "Extra" "active" "active" "processed" "Active"  "" >&2
printf "| %-20s | %-5s | %-9s | %-9s | %-9s | %-7s | %-70s | %s \n" "File Name" "tasks" "tasks" "tasks" "jobs" "jobs"  "Message" >&2
printf "%0.s-" {1..153} >&2
printf "\n" >&2

jns=()
files=( $(ls -1v $file_pattern) )
if $randomorder; then
    files=( $(echo "${files[@]}" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
fi
i=1
# for f in "${files[@]}"; do
for ((j=0; j < "${#files[@]}"; j++)); do
    f=${files[$j]}
    time_elapsed=0

    while [[ $time_elapsed -lt $max_time ]]; do

        fname=$(basename $f)
        abb_fname=$(abbreviate $fname 20 10 7)

        # Submit job using sbatch_minsar.bash, performing all necesarry resource checks.
        # Grep sbatch_minsar output for current resource statuses for logging.
        sbatch_minsar=$(sbatch_minsar.bash $f --step_max_tasks $step_max_tasks --total_max_tasks $total_max_tasks)
        sbatch_exit_status="$?"

        num_tasks_job=$(echo $sbatch_minsar | grep -oP "(\d{1,})(?= additional tasks)")
        resource_limits=$(echo $sbatch_minsar | grep -oP "(?<=\()(\d{1,}\/\d{1,})(?=\) -->)")
        num_jobs=$(echo $resource_limits | awk '{print $1}')
        num_step_tasks=$(echo $resource_limits | awk '{print $2}')
        num_total_tasks=$(echo $resource_limits | awk '{print $3}')


        printf "| %-20s | %-5s | %-9s | %-9s | %-9s | %-7s | %s" "$abb_fname" "$num_tasks_job" "$num_step_tasks" "$num_total_tasks" "$i/${#files[@]}" "$num_jobs" >&2

        # If there was a problem submitting the job, grep sbatch_minsar output for failure reason and wait.
        # If job submitted succesfully, grep sbatch_minsar output for job_number.
        if [[ $sbatch_exit_status -ne 0 ]]; then
            fail_reason=$(echo $sbatch_minsar | grep -oP "(?<= could not be submitted. )(.*)")
            printf "%-70s |\n" "Not submitted. $fail_reason Waiting $(($wait_time/60)) minutes." >&2
            #printf "| %-20s | %-11s | %-17s | %-18s | %-19s | %-11s | %-35s |\n" "" "" "" "" "" "" "$fail_reason" >&2
            #printf "| %-20s | %-11s | %-17s | %-18s | %-19s | %-11s | %-35s |\n" "" "" "" "" "" "" "Wait $(($wait_time/60))  minutes." >&2
            sleep $wait_time
            time_elapsed=$((time_elapsed+$wait_time))
        else
            job_number=$(echo $sbatch_minsar | grep -oP "\d{7,}")
            printf "%-70s |\n" "Submitted: $job_number" >&2

            jns+=($job_number)
            break;
        fi
    done

    i=$(($i+1))
    
done

printf "%0.s-" {1..153} >&2
printf "\n" >&2

if [[ $time_elapsed -ge $max_time ]]; then
    exit 1
else
    echo "${jns[@]}"
    exit 0
fi

