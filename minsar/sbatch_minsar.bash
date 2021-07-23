##!/bin/bash

# Custom replacement for echo command that also
# appends to a logfile when --verbose is on.
function echot {
    if [[ $verbose == "true" ]]; then
        echo "$@" | tee -ai ${logfile_name}
    else
        echo "$@"
    fi
    
}

# Renames a file with the current execution date and time
# and movesit to the sbatch_minsar directory
function move_logfile {
    exec_date=$(date +"%Y%m%d.%H%M%S")
    if [[ $verbose == "true" ]]; then
         new_logfile="${WORKDIR}/sbatch_minsar/${step}.${exec_date}.log"
         mv $logfile_name $new_logfile
         echo "Logs at $new_logfile"
    fi
}

# Gets list of job_ids for running and pending jobs
function get_active_jobids {
    running_tasks=$(squeue -u $USER --format="%A" -rh)
    job_ids=($(echo $running_tasks | grep -oP "\d{4,}"))
    echo "${job_ids[@]}"
    return 0
}

# Parses the number of tasks from a job file.
# Number of tasks is equal to number of lines.
# insarmaps.job and smallbaseline.job have 1 task.
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

# Computes the number of tasks actively running
# or in a pending state on the submission queue.
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
    helptext="
    Custom sbatch job submission wrapper. Conditionally submits jobs to the sbatch scheduler                     
    if and only if all standard 'sbatch' elligibility tests pass as well as the following                        
    custom conditions are met:
        1) Total number of user submitted jobs is less than the queue support maxiumum.                           
        2) Total number of user submitted tasks is less than some maximum number.                                 
        3) Total number of user submitted tasks for the current processing step is less than some maximum number.   
                                                                                                                    
    usage: sbatch_minsar.bash job_file [--verbose] [--help]                                                      
                                                                                                                    
    --verbose           Log all output to files stored in \$WORKDIR/sbatch_minsar                                
                        Log files are named by date and time of execution.                                       
                        Should only be needed for advanced dubgging.                                             
                                                                                                                    
    Examples:                                                                                                    
        sbatch_minsar.bash run_01_unpack_topo_reference_0.job                                                    
        sbatch_minsar.bash run_01_unpack_topo_reference_0.job --verbose                                          
                                                                                                                    
                                                                                                                    
    ADDITIONAL NOTES:                                                                                            
                                                                                                                    
    Maximum values for custom conditions are set using the following variables:                                  
        1) \$SJOBS_MAX_JOBS_PER_QUEUE   (minsar/defaults/queues.cfg)                                             
        2) \$SJOBS_TOTAL_MAX_TASKS      (minsar/defaults/queues.cfg)                                             
        3) \$SJOBS_STEP_MAX_TASKS       (minsar/defaults/queues.cfg)                                             
                                                                                                                    
        Computation of \$SJOBS_STEP_MAX_TASKS also relies on a custom 'io_load' paramameter set in 
        minsar/defaults/job_defaults.cfg 

        \$SJOBS_MAX_JOBS_PER_QUEUE, \$SJOBS_TOTAL_MAX_TASKS, and \$SJOBS_STEP_MAX_TASKS can be set in
        the default queues.cfg file or be overwritten by an external environmental variable of the same
        name (export SJOBS_STEP_MAX_TASKS=1).
        "
        echo -e "$helptext"
        exit 0;
fi

#echo $$

job_file=$1
step_name=$(echo $job_file | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,}.job)")
if [ -z "$step_name" ]; then
    step_name=${job_file%.*}
fi
verbose="false"

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
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

# Sets up sbatch_minsar directory for log files if --verbose is on
if [[ $verbose == "true" ]]; then
    cd $(dirname $(readlink -job_file $job_file))
    WORKDIR=$(pwd)

    if [[ $WORKDIR == *"run_file"* ]]; then
        cd ..
    fi

    RUNFILES_DIR=$WORKDIR"/run_files"

    ##### For proper logging to both file and stdout #####
    exec_date=$(date +"%Y%m%d.%H%M%S")
    step=$(basename $job_file | cut -d. -f1)

    if [ ! -d "${WORKDIR}/sbatch_minsar/" ]
    then
        mkdir "${WORKDIR}/sbatch_minsar/"
    fi

    logfile_name="${WORKDIR}/sbatch_minsar/${step}.${exec_date}.log"
fi

echot "Jobfile: $(basename $job_file)"
echot "Step: $step_name"

# Get io_load for step from job_defaults.cfg file.
# io_load needs to remain as column 8 in the .cfg file.
defaults_file="${RSMASINSAR_HOME}/minsar/defaults/job_defaults.cfg"
step_io_load=$(grep $step_name $defaults_file | awk '{print $8}')

# Get queue that job_file is being submitted to from job_file definition
QUEUENAME=$(grep "#SBATCH -p" $job_file | awk -F'[ ]' '{print $3}')
queues_file="${RSMASINSAR_HOME}/minsar/defaults/queues.cfg"

# Parse custom resource allocation limits from queues.cfg
# If environment variable already exists, use that instead.
if [ -z "$SJOBS_MAX_JOBS_PER_QUEUE" ]; then
    SJOBS_MAX_JOBS_PER_QUEUE=$(grep $QUEUENAME $queues_file | awk '{print $7}')
else
    SJOBS_MAX_JOBS_PER_QUEUE="${SJOBS_MAX_JOBS_PER_QUEUE}"
fi

if [ -z "$SJOBS_STEP_MAX_TASKS" ]; then
    SJOBS_STEP_MAX_TASKS=$(grep $QUEUENAME $queues_file | awk '{print $9}')
else
    SJOBS_STEP_MAX_TASKS="${SJOBS_STEP_MAX_TASKS}"
fi

if [ -z "$SJOBS_TOTAL_MAX_TASKS" ]; then
    SJOBS_TOTAL_MAX_TASKS=$(grep $QUEUENAME $queues_file | awk '{print $10}')
else
    SJOBS_TOTAL_MAX_TASKS="${SJOBS_TOTAL_MAX_TASKS}"
fi

# Update SJOBS_STEP_MAX_TASKS based on io_load for step
SJOBS_STEP_MAX_TASKS=$(echo "$SJOBS_STEP_MAX_TASKS/$step_io_load" | bc | awk '{print int($1)}')

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
num_tasks_job=$(num_tasks_for_file $job_file)

# Compute new total number of tasks and tasks for current step
new_tasks_step=$(($num_active_tasks_step+$num_tasks_job))
new_tasks_total=$(($num_active_tasks_total+$num_tasks_job))

# Get active number of running jobs
num_active_jobs=$(squeue -u $USER -h -t running,pending -r -p $QUEUENAME | wc -l )
new_active_jobs=$(($num_active_jobs+1)) 

########### Release lockfile
flock -u 200
###########

# Let default sbatch test if job file is able to be submitted
sbatch_message=$(sbatch --test-only -Q $job_file)
echot -e "${sbatch_message[@]:1}"

# Check if submitting job_file will exceed custom resource limits
if [[ $new_active_jobs   -le $SJOBS_MAX_JOBS_PER_QUEUE  ]]; then job_count="OK";        else job_count="FAILED";        fi
if [[ $new_tasks_step    -le $SJOBS_STEP_MAX_TASKS      ]]; then steptask_count="OK";   else steptask_count="FAILED";   fi
if [[ $new_tasks_total   -le $SJOBS_TOTAL_MAX_TASKS     ]]; then task_count="OK";       else task_count="FAILED";       fi

if  [[ $job_count == "OK" ]] && [[ $steptask_count == "OK" ]] && [[ $task_count == "OK" ]]; then 
    resource_check="OK" 
else 
    resource_check="FAILED"
fi

echot -e "\n"
echot -e "--> Verifying job request is within custom resource limits...$resource_check"
echot -e "\t--> $num_tasks_job additional tasks."
echot -e "\t[*] Job count \t\t($num_active_jobs/$SJOBS_MAX_JOBS_PER_QUEUE) --> ($new_active_jobs/$SJOBS_MAX_JOBS_PER_QUEUE)...$job_count"
echot -e "\t[*] Step task count \t($num_active_tasks_step/$SJOBS_STEP_MAX_TASKS) --> ($new_tasks_step/$SJOBS_STEP_MAX_TASKS)...$steptask_count"
echot -e "\t[*] Total task count \t($num_active_tasks_total/$SJOBS_TOTAL_MAX_TASKS) --> ($new_tasks_total/$SJOBS_TOTAL_MAX_TASKS)...$task_count"
echot -e "\n"

if  [[ $resource_check == "OK" ]] && 
    [[ $sbatch_message != *"FAILED"* ]];  then

    sbatch_submit=$(sbatch --parsable $job_file)
    exit_status="$?"

    if [[ $exit_status -ne 0 ]]; then
        reason="'sbatch' submission error"
        echot "$job_file could not be submitted. $reason."
        move_logfile

        exit 1
    fi

    job_number=$(echo $sbatch_submit | grep -oE "[0-9]{7,}")
    
    echot "$job_file submitted as job $job_number at $(date +"%T") on $(date +"%Y-%m-%d")."

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
    echot "$job_file could not be submitted. $reason."

    move_logfile

    exit 1
fi
