#! /bin/bash
set -v -e
WORKDIR="$(readlink -f $1)"
WORKDIR=$WORKDIR"/run_files/"
#echo $WORKDIR

numsteps=16

for i in {1..16}; do
    stepnum="$(printf "%02d" ${i})"
    echo "Starting step #${stepnum} of ${numsteps}"
    files="$(find $WORKDIR -name "run_${stepnum}*.job")"
    echo jobfiles to run: $files

    # Submit all of the jobs and record all of their job numbers
    jobnumbers=()
    for f in $files; do
	#sbatch $f
	jobnumline=$(sbatch $f | grep "Submitted batch job")
        sleep 5
	jobnumber=$(grep -oE "[0-9]{7}" <<< $jobnumline)

	jobnumbers+=("$jobnumber")
    done

    echo "${jobnumbers[@]}"
    # Wait for each job to complete
    for jobnumber in "${jobnumbers[@]}"; do

	# Parse out the state of the job from the sacct function.
	# Format state to be all uppercase (PENDING, RUNNING, or COMPLETED)
	# and remove leading whitespace characters.
	state=$(sacct --format="State" -j $jobnumber | grep "\w[[:upper:]]\w")
	state="$(echo -e "${state}" | sed -e 's/^[[:space:]]*//')"

	# Keep checking the state while it is not "COMPLETED"
      	while true; do
	    echo "${jobnumber} is not finished yet. Current state is '${state}'"
	    state=$(sacct --format="State" -j $jobnumber | grep "\w[[:upper:]]\w")
	    state="$(echo -e "${state}" | sed -e 's/^[[:space:]]*//')"

            # Check if "COMPLETED" is anywhere in the state string variables.
            # This gets rid of some strange special character issues.
            if [[ $state == *"COMPLETED"* ]] && [[ $state != "" ]]; then
                state="COMPLETED"
		echo "${jobnumber} is complete"
		break;
            fi

	    # Wait for 10 second before chcking again
	    sleep 10
	    
     	done

	echo "${jobnumber} is finished."
	
    done

    # Run check_job_output.py on each file
    for f in $files; do
	entry="${f%.*}*.job"
        echo jobfile to check: $entry 
        check_job_outputs.py "$entry"
    done

    echo "Step ${i}/${numsteps} complete."

done
