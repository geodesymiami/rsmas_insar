##!/bin/bash

function echot {
    if [[ $verbose == "true" ]]; then
        echo "$@" | tee -ai ${logfile_name}
    else
        echo "$@"
    fi
    
}

function move_logfile {
    exec_date=$(date +"%Y%m%d.%H%M%S")
    if [[ $verbose == "true" ]]; then
         new_logfile="${WORKDIR}/sbatch_minsar/${step}.${exec_date}.log"
         mv $logfile_name $new_logfile
         echo "Logs at $new_logfile"
    fi
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

echo $$

f=$1
step_name=$(echo $f | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,}.job)")
if [ -z "$step_name" ]; then
    step_name=${f%.*}
fi
step_max_tasks=1500
total_max_tasks=3000
verbose="false"

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
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
        --verbose)
            verbose="true"
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ $verbose == "true" ]]; then
    cd $(dirname $(readlink -f $f))
    WORKDIR=$(pwd)

    if [[ $WORKDIR == *"run_file"* ]]; then
        cd ..
    fi

    RUNFILES_DIR=$WORKDIR"/run_files"

    ##### For proper logging to both file and stdout #####
    exec_date=$(date +"%Y%m%d.%H%M%S")
    step=$(basename $1 | cut -d. -f1)

    if [ ! -d "${WORKDIR}/sbatch_minsar/" ]
    then
        mkdir "${WORKDIR}/sbatch_minsar/"
    fi

    logfile_name="${WORKDIR}/sbatch_minsar/${step}.${exec_date}.log"
    # printf '' > $logfile_name
    # tail -f $logfile_name & 
    # trap "pkill -P $$" EXIT
    # exec 1>>$logfile_name 2>>$logfile_name
    ######################################################
fi

echot "Jobfile: $(basename $f)"
echot "Step: $step_name"

# Get queue to submit to and identify job submission limits for that queue
#echo $1
QUEUENAME=$(grep "#SBATCH -p" $f | awk -F'[ ]' '{print $3}')
if [ -z "$MAX_JOBS_PER_QUEUE" ]; then
    MAX_JOBS_PER_QUEUE=$(qlimits | grep $QUEUENAME | awk '{print $4}')
else
    MAX_JOBS_PER_QUEUE="${MAX_JOBS_PER_QUEUE}"
fi

################ Set up lockfile
lockfile="$SCRATCH/sbatch_minsar.lock"
exec 200>$lockfile
flock 200
echo "PID: $$" 1>&200
################

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
new_tasks_total=$(($num_active_tasks_total+$num_tasks_job))

# Get active number of running jobs
num_active_jobs=$(squeue -u $USER -h -t running,pending -r -p $QUEUENAME | wc -l )
new_active_jobs=$(($num_active_jobs+1)) 

########### Release lockfile
flock -u 200
###########

sbatch_message=$(sbatch --test-only -Q $f)
echot -e "${sbatch_message[@]:1}"

#rand=$(echo $(($(shuf -i 25-300 -n 1))))
#rand=$(echo "scale=2; ${rand}/100" | bc -l)
#sleep $rand
#echo "slept for $rand seconds".

#echo "Sleeping 5 seconds"
#sleep 5

if [[ $new_active_jobs   -le $MAX_JOBS_PER_QUEUE ]]; then job_count="OK";        else job_count="FAILED";        fi
if [[ $new_tasks_step    -le $step_max_tasks     ]]; then steptask_count="OK";   else steptask_count="FAILED";   fi
if [[ $new_tasks_total   -le $total_max_tasks    ]]; then task_count="OK";       else task_count="FAILED";       fi

if  [[ $job_count == "OK" ]] && [[ $steptask_count == "OK" ]] && [[ $task_count == "OK" ]]; then 
    resource_check="OK" 
else 
    resource_check="FAILED"
fi

echot -e "\n"
echot -e "--> Verifying job request is within custom resource limits...$resource_check"
echot -e "\t--> $num_tasks_job additional tasks."
echot -e "\t[*] Job count \t\t($num_active_jobs/$MAX_JOBS_PER_QUEUE) --> ($new_active_jobs/$MAX_JOBS_PER_QUEUE)...$job_count"
echot -e "\t[*] Step task count \t($num_active_tasks_step/$step_max_tasks) --> ($new_tasks_step/$step_max_tasks)...$steptask_count"
echot -e "\t[*] Total task count \t($num_active_tasks_total/$total_max_tasks) --> ($new_tasks_total/$total_max_tasks)...$task_count"
echot -e "\n"

if  [[ $resource_check == "OK" ]] && 
    [[ $sbatch_message != *"FAILED"* ]];  then

    sbatch_submit=$(sbatch --parsable $f)
    exit_status="$?"

    if [[ $exit_status -ne 0 ]]; then
        reason="'sbatch' submission error"
        echot "$f could not be submitted. $reason."
        move_logfile

        exit 1
    fi

    job_number=$(echo $sbatch_submit | grep -oE "[0-9]{7,}")
    
    echot "$f submitted as job $job_number at $(date +"%T") on $(date +"%Y-%m-%d")."

    move_logfile

    exit 0

else

    if [[ $job_count != "OK" ]]; then 
        reason="Max job count exceeded"
    elif [[ $steptask_count != "OK" ]]; then 
        reason="Max task count for step exceeded"
    elif [[ $task_count != "OK" ]]; then 
        reason="Total task count exceeded"
    else 
        echot "sbatch submission error."
        reason="'sbatch' submission error"
    fi
    echot "$f could not be submitted. $reason."

    move_logfile

    exit 1
fi