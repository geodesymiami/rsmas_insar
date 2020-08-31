#! /bin/bash

WORKDIR="$(readlink -f $1)"
WORKDIR=$WORKDIR"/run_files/"
#echo $WORKDIR

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
        *)    # unknown option
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

#for i in {$startstep..$stopstep}; do
for (( i=$startstep; i<=$stopstep; i++)) do
    stepnum="$(printf "%02d" ${i})"
    echo "Starting step #${stepnum} of ${stopstep}"
    files="$(find $WORKDIR -name "*${stepnum}*.job")"
    echo $files

    # Submit all of the jobs and record all of their job numbers
    jobnumbers=()
    for f in $files; do
	#sbatch $f
	jobnumline=$(sbatch $f | grep "Submitted batch job")
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
	entry="${f%.*}"
        check_job_outputs.py "$entry"
    done

    echo "Step ${i}/${stopstep} complete."

done
