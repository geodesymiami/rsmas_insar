##! /bin/bash
#set -x
#trap read debug

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

if [[ $startstep == "ifgrams" ]]; then
    startstep=1
elif [[ $startstep == "timeseries" ]]; then
    startstep=17
elif [[ $startstep == "insarmaps" ]]; then
    startstep=18
fi

if [[ $stopstep == "ifgrams" ]]; then
    stopstep=16
elif [[ $stopstep == "timeseries" ]]; then
    stopstep=17
elif [[ $stopstep == "insarmaps" ]]; then
    stopstep=18
fi

for (( i=$startstep; i<=$stopstep; i++ )) do
    stepnum="$(printf "%02d" ${i})"
    if [[ $i -le 16 ]]; then
	fname="$RUNFILES_DIR/run_${stepnum}_*.job"
    elif [[ $i -eq 17 ]]; then
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
	active_jobs=($(squeue -u $USER | grep -oP "[0-9]{7,}"))
	num_active_jobs=${#active_jobs[@]}
	if [[ $num_active_jobs -lt 25 ]]; then
             jobnumline=$(sbatch $file | grep "Submitted batch job")
             jobnumber=$(grep -oE "[0-9]{7}" <<< $jobnumline)

             jobnumbers+=("$jobnumber")
        else
             echo "Couldnt submit job (${file}), because there are 25 active jobs right now. Waiting 5 minutes to submit next job."
             f=$((f-1))
             sleep 300 # sleep for 5 minutes
        fi
    done

    echo "Jobs submitted: ${jobnumbers[@]}"
    sleep 5
    # Wait for each job to complete
    for (( j=0; j < "${#jobnumbers[@]}"; j++)); do
        jobnumber=${jobnumbers[$j]}
        
        # Parse out the state of the job from the sacct function.
        # Format state to be all uppercase (PENDING, RUNNING, or COMPLETED)
        # and remove leading whitespace characters.
        state=$(sacct --format="State" -j $jobnumber | grep "\w[[:upper:]]\w")
        state="$(echo -e "${state}" | sed -e 's/^[[:space:]]*//')"

        # Keep checking the state while it is not "COMPLETED"
            secs=0
        while true; do
            
            # Only print every so often, not every 10 seconds
            if [[ $(( $secs % 10)) -eq 0 ]]; then
                echo "Job ${jobnumber} is not finished yet. Current state is '${state}'"
            fi

            state=$(sacct --format="State" -j $jobnumber | grep "\w[[:upper:]]\w")
            state="$(echo -e "${state}" | sed -e 's/^[[:space:]]*//')"

                # Check if "COMPLETED" is anywhere in the state string variables.
                # This gets rid of some strange special character issues.
            if [[ $state == *"COMPLETED"* ]] && [[ $state != "" ]]; then
                state="COMPLETED"
                echo "${jobnumber} is complete"
                break;

            elif [[ $state == *"TIMEOUT"* ]] && [[ $state != "" ]]; then
                jf=${files[$j]}
		init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)
		
		echo "${jobnumber} timedout due to too low a walltime (${init_walltime})."
                		
                # Compute a new walltime and update the job file
                update_walltime.py "$jf" &> /dev/null

		updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $jf)

		datetime=$(date +"%Y-%m-%d:%H-%M")
		echo "${datetime}: re-running: ${jf}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log

		echo "Resubmitting file (${jf}) with new walltime of ${updated_walltime}"

                # Resubmite a sa new job number
                jobnumline=$(sbatch $jf | grep "Submitted batch job")
                exit_status="$?"
                echo "exit status from resubmitting job: $exit_status"
                jn=$(grep -oE "[0-9]{7}" <<< $jobnumline)
                echo "${jf} resubmitted as jobumber: ${jn}"

                # Added newly submitted jobs and files to arrays
                jobnumbers+=("$jn")
                files+=("$jf")
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
done
