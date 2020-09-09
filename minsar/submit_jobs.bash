#! /bin/bash
#set -v -e

WORKDIR="$(readlink -f $1)"
WORKDIR=$WORKDIR"/run_files/"

numsteps=16
startstep=1
stopstep=$numsteps

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

#for i in {$startstep..$stopstep}; do
for (( i=$startstep; i<=$stopstep; i++ )) do
    stepnum="$(printf "%02d" ${i})"

    echo "Starting step #${i} of ${stopstep}"
    files=($(find $WORKDIR -name "run_${stepnum}_*.job"))
    echo "Jobfiles to run: ${files[@]}"
    
    # Submit all of the jobs and record all of their job numbers
    jobnumbers=()
    for f in "${files[@]}"; do
	#sbatch $f
	jobnumline=$(sbatch $f | grep "Submitted batch job")
	jobnumber=$(grep -oE "[0-9]{7}" <<< $jobnumline)

	jobnumbers+=("$jobnumber")
    done

    echo "Jobs submitted: ${jobnumbers[@]}"
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
		echo "${jobnumber} is not finished yet. Current state is '${state}'"
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
		echo "${jobnumber} timedout due to too low a walltime."
		jf=${files[$j]}
		echo "Resubmitting file (${jf})"

		# Compute a new walltime and update the job file
		update_walltime.py "$jf" &> /dev/null

		# Resubmite a sa new job number
		jobnumline=$(sbatch $f | grep "Submitted batch job")
		jn=$(grep -oE "[0-9]{7}" <<< $jobnumline)
		echo "${jf} resubmitted as jobumber: ${jn}"

		# Added newly submitted jobs and files to arrays
		jobnumbers+=("$jn")
		files+=("$jf")
		break;
	 
	    elif [[ ( $state == *"FAILED"* || $state == *"CANCELLED"* ) &&  $state != "" ]]; then
		echo "${jobnumber} was CANCLLED or FAILED. Exiting with status code 1."
		exit 1; 
	    fi

	    # Wait for 10 second before chcking again
	    sleep 10
	    ((secs=secs+10))
	    
     	done

	echo "${jobnumber} is finished."

    done

    # Run check_job_output.py on each file
    for f in "${files[@]}"; do
	entry="${f%.*}.job"
	echo "Jobfile to check: $entry"
        check_job_outputs.py "$entry"
	exit_status="$?"
	if [[ $exit_status -ne 0 ]]; then
	    echo "check_job_outputs.py $entry exited with a non-zero exit code ($exit_status). Exiting."
	    exit 1;
	fi
        #check_job_outputs.py "$entry" > /dev/null
    done

    echo "Step ${i}/${stopstep} complete."

done
