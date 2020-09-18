#! /bin/bash
#set -v -e

WORKDIR="$(readlink -f $1)"
RUNFILES_DIR=$WORKDIR"/run_files"
#WORKDIR=$WORKDIR"/run_files/"

startstep=1
stopstep="ingest_insarmaps"

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

if [[ $startstep == "timeseries" ]]; then
    startstep=17
elif [[ $startstep == "ingest_insarmaps" ]]; then
    startstep=18
fi

if [[ $stopstep == "timeseries" ]]; then
    stopstep=17
elif [[ $stopstep == "ingest_insarmaps" ]]; then
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
    for f in "${files[@]}"; do
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
            let "exit_status_sum++"
        fi
     done
     if [[ $exit_status_sum -ne 0 ]]; then
         echo "check_job_outputs.py $exit_status_sum jobfiles exited. Last file: $entry. Exiting."
         exit 1;
     fi

    echo "Step ${i}/${stopstep} complete."
done
