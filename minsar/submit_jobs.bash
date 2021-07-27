##!/bin/bash

function abbreviate {
    abb=$1
    if [[ "${#abb}" -gt $2 ]]; then
        abb=$(echo "$(echo $(basename $abb) | cut -c -$3)...$(echo $(basename $abb) | rev | cut -c -$4 | rev)")
    fi
    echo $abb
}

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    helptext="
    Conditional batch job submission wrapper. Attempts to submit a batch of job files using sbatch_conditional.bash
    and waits for succesful submission of each job file prior to exiting.

    usage: sbatch_conditional.bash job_file_pattern [--max_time] [--random] [--rapid] [--help]                                                            
        
    job_file_pattern        A file pattern describing the set of job files names to be submitted.
                            Can also be a single file name.
    --max_time              The maximum amount of time to attempt to submit a job before exiting.
                            Default value is 604800 seconds (7 days).
    --random                Flag to induce random job submission order. If not provided, jobs are submitted
                            in alphanumeric order.
    --rapid                 Attempts to resubmit a failed job after 60 seconds (1 minute) rather then the
                            default 300 seconds (5 minutes). Useful for rapid testing and debugging on small
                            datasets.

    Examples:                                                                                              
        sbatch_conditional.bash run_01
        sbatch_conditional.bash run_01 --rapid
        sbatch_conditional.bash run_01 --max_time 86400
        sbatch_conditional.bash run_01 --random --rapid
"
    echo -e "$helptext"
    exit 0;
fi

if [[ $1 == *".job"* ]]; then
    file_pattern=$1
else
    file_pattern="$1*.job"
fi

step_name=$file_pattern
max_time=604800
randomorder=false
wait_time=300

while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
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

for ((j=0; j < "${#files[@]}"; j++)); do
    job_file=${files[$j]}
    time_elapsed=0
    while [[ $time_elapsed -lt $max_time ]]; do

        fname=$(basename $job_file)

        # Abbreivates the file name to 20 characters long. 
        # First 10 characters, followed by '...', followed by final 7 characters.
        abb_fname=$(abbreviate $fname 20 10 7)

        # Submit job using sbatch_conditional.bash, performing all necesarry resource checks.
        # Grep sbatch_conditional output for current resource statuses for logging.
        sbatch_conditional=$(sbatch_conditional.bash $job_file)
        sbatch_exit_status="$?"

        # Parse custom resource checks from sbatch_conditional output
        num_tasks_job=$(echo $sbatch_conditional | grep -oP "(\d{1,})(?= additional tasks)")
        resource_limits=$(echo $sbatch_conditional | grep -oP "(?<=\()(\d{1,}\/\d{1,})(?=\) -->)")
        num_jobs=$(echo $resource_limits | awk '{print $1}')
        num_step_tasks=$(echo $resource_limits | awk '{print $2}')
        num_total_tasks=$(echo $resource_limits | awk '{print $3}')

        # (?<=\()(\d{1,}\/\d{1,})(?=\) -->) regex matches all sets of two number seaparated by a '/'
        # contained with parenetheses '()' prior to '-->'.
        #
        # Example:
        # [*] Job count           (0/3) --> (1/3)...OK
        # [*] Step task count     (0/400) --> (1/400)...OK
        # [*] Total task count    (0/10) --> (1/10)...OK
        #
        # Matches 0/3, 0/400, and 0/10


        printf "| %-20s | %-5s | %-9s | %-9s | %-9s | %-7s | %s" "$abb_fname" "$num_tasks_job" "$num_step_tasks" "$num_total_tasks" "$i/${#files[@]}" "$num_jobs" >&2

        # If there was a problem submitting the job, grep sbatch_conditional output for failure reason and wait.
        # If job submitted succesfully, grep sbatch_conditional output for job_number.
        if [[ $sbatch_exit_status -ne 0 ]]; then
            fail_reason=$(echo $sbatch_conditional | grep -oP "(?<= could not be submitted. )(.*)(?=\.)")
            printf "%-70s |\n" "Not submitted. $fail_reason. Waiting $(($wait_time/60)) minutes." >&2
            sleep $wait_time
            time_elapsed=$((time_elapsed+$wait_time))
        else
            # Parse job number (7+ digit number) from sbatch_conditional output
            job_number=$(echo $sbatch_conditional | grep -oP "\d{7,}(?= )")
            printf "%-70s |\n" "Submitted: $job_number" >&2

            # Add job nunmber to running list of succesfully submitted job numbers
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

