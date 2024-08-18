##! /bin/bash

function abbreviate {
    abb=$1
    if [[ "${#abb}" -gt $2 ]]; then
        abb=$(echo "$(echo $(basename $abb) | cut -c -$3)...$(echo $(basename $abb) | rev | cut -c -$4 | rev)")
    fi
    echo $abb
}

function convert_array_to_comma_separated_string() {
    joined_string=""
    for item in "$@"; do
        joined_string+="${item},"
    done
    # Remove the trailing comma at the end
    joined_string="${joined_string%,}"

    echo $joined_string
}

function get_comma_separated_list {
    abb=$1
    if [[ "${#abb}" -gt $2 ]]; then
        abb=$(echo "$(echo $(basename $abb) | cut -c -$3)...$(echo $(basename $abb) | rev | cut -c -$4 | rev)")
    fi
    echo $abb
}

function remove_from_list {
    var=$1
    shift
    list=("$@")
    new_list=() # Not strictly necessary, but added for clarity
    
    #echo "VAR: $var"
    for item in ${list[@]}
    do
        #echo "$item"
        if [ "$item" != "$var" ]
        then
            new_list+=("$item")
        fi
    done
    list=("${new_list[@]}")
    unset new_list
    echo "${list[@]}"
}

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                         \n\
Job submission script
usage: run_workflow.bash custom_template_file [--start] [--stop] [--dostep] [--help]\n\
       run_workflow.bash \$PWD --jobfile insarmaps_miaplpy_geo.job                  \n\
                                                                                    \n\
  Examples:                                                                        \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template              \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start 2    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep 4   \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --stop 8     \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --start mintpy \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep insarmaps \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dostep miaplpy    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --miaplpy    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dir miaplpy_2015_2021  \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dir miaplpy_2015_2021 --start 9 \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --dir miaplpy_2015_2021 --start timeseries_correction \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --miaplpy --start load_ifgram    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --miaplpy --dostep generate_ifgram    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --jobfile insarmaps.job    \n\
      run_workflow.bash \$SAMPLESDIR/unittestGalapagosSenDT128.template --append    \n\
                                                                                   \n\
 Processing steps (start/end/dostep): \n\
                                                                                 \n\
   ['1-16', 'mintpy', 'miaplpy', 'insarmaps' ]                                          \n\
                                                                                 \n\
   In order to use either --start or --dostep, it is necessary that a            \n\
   previous run was done using one of the steps options to process at least      \n\
   through the step immediately preceding the starting step of the current run.  \n\
                                                                                 \n\
   --start STEP          start processing at the named step [default: load_data].\n\
   --end STEP, --stop STEP                                                       \n\
                         end processing at the named step [default: upload]      \n\
   --dostep STEP         run processing at the named step only                   \n\
                                                                                 \n\
   --miaplpy:  the run_files directory is determined by the *template file       \n\
   --dir:      for --miaplpy only (see  miaplpyApp.py --help)                    \n\
   --miaplpy --start --end options:                                               \n\
              'load_data', 'phase_linking', 'concatenate_patches', 'generate_ifgram', 'unwrap_ifgram'       \n\
              'load_ifgram', 'ifgram_correction', 'invert_network', 'timeseries_correction'  [1-9] \n\
                                                                                 \n\
   --jobfile filename.job: run individual job and wait for completion            \n
   "
    printf "$helptext"
    exit 0;
else
    PROJECT_NAME=$(basename "$1" | cut -d. -f1)
    PROJECT_NAME=$(basename "$1" | awk -F ".template" '{print $1}')
    template_file=$1
fi
WORKDIR=$SCRATCHDIR/$PROJECT_NAME
cd $WORKDIR

randomorder=false
rapid=false
append=false
dir_miaplpy="miaplpy"
wait_time=30

tmp=true
tmp_flag_str="--tmp"
run_files_name="run_files_tmp"
#always use --no-tmp on stampede3   FA 4/2023: need to change to use copy_to_tmp as in minsarApp.bash
if [[ $HOSTNAME == *"stampede3"* ]] && [[ $tmp_flag_str == "--tmp" ]]; then
   tmp_flag_str="--no-tmp"
   run_files_name="run_files"
   echo "Running on stampede3: switched from --tmp to --no-tmp "
fi

startstep=1
stopstep=11

# FA 4/23: need function to get  stopstep depending on ToPS verus stripmap
dir_flag=false

template_file_dir=$(dirname "$1")          # create name including $TE for concise log file
if  [[ $template_file_dir == $TE ]]; then
    template_print_name="\$TE/$(basename $template_file)"
elif [[ $template_file_dir == $SAMPLESDIR ]]; then
    template_print_name="\$SAMPLESDIR/$(basename $template_file)"
else
    template_print_name="$template_file"
fi
echo "$(date +"%Y%m%d:%H-%M") * run_workflow.bash $template_print_name ${@:2}" >> "${WORKDIR}"/log

jobfile_flag=0
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
        --random)
            randomorder=true
            shift
            ;;
        --rapid)
            rapid=true
            wait_time=10
            shift
            ;;
        --append)
            append=true
            shift
            ;;
        --miaplpy)
            miaplpy_flag=true
            shift
            ;;
        --jobfile)
            jobfile_flag=true
            jobfile="$2"
            shift
            ;;
        --dir)
            miaplpy_flag=true
            dir_flag=true
            dir_miaplpy="$2"
            shift
            shift
            ;;
        --tmp)
            tmp=true
            tmp_flag_str="--tmp"
            run_files_name="run_files_tmp"
            shift
            ;;
        --no-tmp)
            tmp=false
            tmp_flag_str="--no-tmp"
            run_files_name="run_files"
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ $startstep == "miaplpy" ]]; then
   miaplpy_flag=true
fi

# set startstep, stopstep if miaplpy options are given
echo "startstep, stopstep:<$startstep> <$stopstep>"
if [[ $miaplpy_flag == "true" ]]; then 
    if [[ $startstep == "load_data" ]]; then               startstep=1
    elif [[ $startstep == "phase_linking" ]]; then         startstep=2
    elif [[ $startstep == "concatenate_patches" ]]; then   startstep=3
    elif [[ $startstep == "generate_ifgram" ]]; then       startstep=4
    elif [[ $startstep == "unwrap_ifgram" ]]; then         startstep=5
    elif [[ $startstep == "load_ifgram" ]]; then           startstep=6
    elif [[ $startstep == "ifgram_correction" ]]; then     startstep=7
    elif [[ $startstep == "invert_network" ]]; then        startstep=8
    elif [[ $startstep == "timeseries_correction" ]]; then startstep=9
    #elif [[ $startstep != "1" ]] && [[ $startstep != "mintpy" ]] && [[ $startstep != "miaplpy" ]]; then 
    elif [[ $startstep != *[1-9]* ]] && [[ $startstep != "mintpy" ]] && [[ $startstep != "miaplpy" ]]; then 
        echo "ERROR: $startstep -- not a valid startstep. Exiting."
        exit 1
    fi

    if [[ $stopstep == "load_data" ]]; then               stopstep=1
    elif [[ $stopstep == "phase_linking" ]]; then         stopstep=2
    elif [[ $stopstep == "concatenate_patches" ]]; then   stopstep=3
    elif [[ $stopstep == "generate_ifgram" ]]; then       stopstep=4
    elif [[ $stopstep == "unwrap_ifgram" ]]; then         stopstep=5
    elif [[ $stopstep == "load_ifgram" ]]; then           stopstep=6
    elif [[ $stopstep == "ifgram_correction" ]]; then     stopstep=7
    elif [[ $stopstep == "invert_network" ]]; then        stopstep=8
    elif [[ $stopstep == "timeseries_correction" ]]; then stopstep=9
    elif [[ $startstep != *[1-9]* ]] && [[ $stopstep != "mintpy" ]] && [[ $stopstep != "miaplpy" ]]; then 
        echo "ERROR: $stopstep -- not a valid stopstep. Exiting."
        exit 1
    fi
fi
#echo "startstep, stopstep:<$startstep> <$stopstep>"

# IO load for each step. For step_io_load=1 the maximum tasks allowed is step_max_tasks_unit
# for step_io_load=2 the maximum tasks allowed is step_max_tasks_unit/2

# declare -A  step_io_load_list
# step_io_load_list=(
#     [unpack_topo_reference]=1
#     [unpack_secondary_slc]=1
#     [average_baseline]=1
#     [extract_burst_overlaps]=1
#     [overlap_geo2rdr]=1
#     [overlap_resample]=1
#     [pairs_misreg]=1
#     [timeseries_misreg]=1
#     [fullBurst_geo2rdr]=1
#     [fullBurst_resample]=1
#     [extract_stack_valid_region]=1
#     [merge_reference_secondary_slc]=1
#     [generate_burst_igram]=1
#     [merge_burst_igram]=1
#     [filter_coherence]=1
#     [unwrap]=1

#     [smallbaseline_wrapper]=1
#     [insarmaps]=1

#     [miaplpy_crop]=1
#     [miaplpy_inversion]=1
#     [miaplpy_ifgram]=1
#     [miaplpy_unwrap]=1
#     [miaplpy_un-wrap]=1
#     [miaplpy_mintpy_corrections]=1

    
# )

##### For proper logging to both file and stdout #####
num_logfiles=$(ls $WORKDIR/workflow.*.log | wc -l)
test -f $WORKDIR/workflow.0.log  || touch workflow.0.log
if $append; then num_logfiles=$(($num_logfiles-1)); fi
logfile_name="${WORKDIR}/workflow.${num_logfiles}.log"
#printf '' > $logfile_name
#tail -f $logfile_name & 
#trap "pkill -P $$" EXIT
#exec 1>>$logfile_name 2>>$logfile_name
# FA 12/22  for debugging comment previous line out so that STDOUT goes to STDOUT
######################################################

RUNFILES_DIR=$WORKDIR"/"$run_files_name

if [[ $miaplpy_flag == "true" ]]; then
   # get miaplpy run_files directory name
   if [[ ! -z $(grep "^miaplpy.interferograms.networkType" $template_file) ]];  then
      network_type=$(grep -E "^miaplpy.interferograms.networkType" $template_file | awk -F= '{print $2}' |  awk -F# '{print $1}' | tail -1 | xargs  )
      if [[ $network_type == "auto" ]];  then
         network_type=single_reference                  # default of MiaplPy
      fi
   else
      network_type=single_reference                     # default of MiaplPy
   fi

   if [[ $network_type == "sequential" ]];  then
      if [[ ! -z $(grep "^miaplpy.interferograms.connNum" $template_file) ]];  then
         connection_number=$(grep -E "^miaplpy.interferograms.connNum" $template_file | awk -F= '{print $2}' |  awk -F# '{print $1}' | xargs  )
      else
         connection_number=3                            # default of MiaplPy
      fi
      network_type=${network_type}_${connection_number}
   fi
   if [[ $network_type == "delaunay" ]];  then
      if [ ! -z $(grep "^miaplpy.interferograms.delaunayBaselineRatio" $template_file) ] &&  [ ! ${template[miaplpy.interferograms.delaunayBaselineRatio]} == "auto" ]; then
         delaunay_baseline_ratio=$(grep -E "^miaplpy.interferograms.delaunayBaselineRatio" $template_file | awk -F= '{print $2}' |  awk -F# '{print $1}' | xargs  )
      else
         delaunay_baseline_ratio=4                            # default of MiaplPy
      fi
      network_type=${network_type}_${delaunay_baseline_ratio}
   fi

   RUNFILES_DIR=$WORKDIR"/${dir_miaplpy}/network_${network_type}/run_files"
   echo "RUNFILES_DIR: $RUNFILES_DIR"

   if [ ! -d $RUNFILES_DIR ]; then
       echo "run_files directory $RUNFILES_DIR does not exist -- exiting."
       exit 1;
   fi
      
   echo "Running miaplpy jobs in ${RUNFILES_DIR}"
fi

#set -xv
#find the last job (11 for 'geometry' and 16 for 'NESD', 9 for stripmap) and remove leading zero
jobfile_arr=(ls $RUNFILES_DIR/run_*_0.job)
last_jobfile=${jobfile_arr[-1]}
last_jobfile=${last_jobfile##*/}
last_jobfile_number=${last_jobfile:4:2}
last_jobfile_number=$(echo $((10#${last_jobfile_number})))
echo last_jobfile_number: $last_jobfile_number


if [[ $startstep == "ifgram" || $startstep == "miaplpy" ]]; then
    startstep=1
elif [[ $startstep == "mintpy" ]]; then
    startstep=$((last_jobfile_number+1))
elif [[ $startstep == "insarmaps" ]]; then
    startstep=$((last_jobfile_number+2))
fi

if [[ $stopstep == "ifgram" || $stopstep == "miaplpy" || -z ${stopstep+x}  ]]; then
    stopstep=$last_jobfile_number
elif [[ $stopstep == "mintpy" ]]; then
    stopstep=$((last_jobfile_number+1))
elif [[ $stopstep == "insarmaps" ]]; then
    stopstep=$((last_jobfile_number+2))
fi

echo "last_jobfile_number: $last_jobfile_number, startstep: $startstep, stopstep: $stopstep"
for (( i=$startstep; i<=$stopstep; i++ )) do
    stepnum="$(printf "%02d" ${i})"
    if [[ $i -le $last_jobfile_number ]]; then
        fname="$RUNFILES_DIR/run_${stepnum}_*.job"
    elif [[ $i -eq $((last_jobfile_number+1)) ]]; then
        fname="$WORKDIR/smallbaseline_wrapper.job"
    else
        fname="$WORKDIR/insarmaps.job"
    fi
    globlist+=("$fname")
done

# If joblist contains run_0* files remove smallbaseline_wrapper.job and insarmaps.job 
# 5/24 FA removing smallbaseline_wrapper.job and insarmaps.job above did not work
if [[ "${globlist[*]}" == *"run_"* ]]; then
    globlist=("${globlist[@]/$WORKDIR\/smallbaseline_wrapper.job/}")
    globlist=("${globlist[@]/$WORKDIR\/insarmaps.job/}")
    # Remove any empty elements
    globlist=("${globlist[@]//}")
fi

echo "Full list of jobfiles to submit: ${globlist[@]}"

defaults_file="${RSMASINSAR_HOME}/minsar/defaults/job_defaults.cfg"

echo "Started at: $(date +"%Y-%m-%d %H:%M:%S")"

# 5/2024 hack to be able to run one jobfile
if [[ $jobfile_flag == "true" ]]; then
     globlist=("$jobfile")
     echo "--jobfile hack applies: replaced full list by jobfile $jobfile"
fi

#globlist=("${globlist[@]/%/}") # Remove potential trailing spaces
#globlist=($(printf "%s\n" "${globlist[@]}" | grep -v '^$'))

echo "globlist (shown with declare -p):"
declare -p globlist

for g in "${globlist[@]}"; do
    if [[ -n $g ]]; then
        files=($(ls -1v $g))
    fi

    if $randomorder; then
        files=( $(echo "${files[@]}" | sed -r 's/(.[^;]*;)/ \1 /g' | tr " " "\n" | shuf | tr -d " " ) )
    fi

    echo "Jobfiles to submit:"
    printf "%s\n" "${files[@]}"

    jobnumbers=()
    file_pattern=$(echo "${files[0]}" | grep -oP "(.*)(?=_\d{1,}.job)|insarmaps|smallbaseline_wrapper")
    
    sbc_command="submit_jobs.bash $file_pattern"
    
    if [[ $jobfile_flag == "true" ]]; then
        sbc_command="submit_jobs.bash $jobfile"
    fi

    if $randomorder; then
        sbc_command="$sbc_command --random"
        echo "Jobs are being submitted in random order. Submission order is likely different from the order above."
    fi
    if $rapid; then
        sbc_command="$sbc_command --rapid"
        echo "Rapid job submission enabled."
    fi

    ###############################
    # Here the jobs are submitted #
    ###############################
    echo "Job submission command:"
    echo "$sbc_command"

    jns=$($sbc_command)

    exit_status="$?"
    if [[ $exit_status -eq 0 ]]; then
        jobnumbers=($jns)
    fi

    #echo "Jobs submitted: ${jobnumbers[@]}"      #       FA 8/23 : switch to print comma-separated
    echo "Jobs submitted: $(convert_array_to_comma_separated_string "${jobnumbers[@]}")"
    sleep 5

    # Wait for each job to complete
    num_jobs=${#jobnumbers[@]}
    num_complete=0
    num_running=0
    num_pending=0
    num_timeout=0
    num_waiting=0

    while [[ $num_complete -lt $num_jobs ]]; do
        num_complete=0
        num_running=0
        num_pending=0
        num_waiting=0
        sleep $wait_time

        for (( j=0; j < "${#jobnumbers[@]}"; j++)); do
            file=${files[$j]}
            file_pattern="${file%.*}"
            step_name=$(echo $file_pattern | grep -oP "(?<=run_\d{2}_)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            step_name_long=$(echo $file_pattern | grep -oP "(?<=$run_files_name\/)(.*)(?=_\d{1,})|insarmaps|smallbaseline_wrapper")
            jobnumber=${jobnumbers[$j]}
            state=$(sacct --format="State" -j $jobnumber | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -3 | tail -1 )
            if [[ $state == *"COMPLETED"* ]]; then
                num_complete=$(($num_complete+1))
            elif [[ $state == *"RUNNING"* ]]; then
                num_running=$(($num_running+1))
            elif [[ $state == *"PENDING"* ]]; then
                num_pending=$(($num_pending+1))
            elif [[ $state == *"TIMEOUT"* || $state == *"NODE_FAIL"* ]]; then
                num_timeout=$(($num_timeout+1))
                #step_max_tasks=$(echo "$SJOBS_STEP_MAX_TASKS/${step_io_load_list[$step_name]}" | bc | awk '{print int($1)}')
        
                if [[ $state == *"TIMEOUT"* ]]; then
                    init_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)
                    echo "${file} timedout with walltime of ${init_walltime}."
                                    
                    # Compute a new walltime and update the job file
                    update_walltime.py "$file" &> /dev/null
                    updated_walltime=$(grep -oP '(?<=#SBATCH -t )[0-9]+:[0-9]+:[0-9]+' $file)

                    datetime=$(date +"%Y-%m-%d:%H-%M")
                    echo "${datetime}: re-running: ${file}: ${init_walltime} --> ${updated_walltime}" >> "${RUNFILES_DIR}"/rerun.log
                    echo "Resubmitting file (${file}) with new walltime of ${updated_walltime}"
                fi

                jobnumbers=($(remove_from_list $jobnumber "${jobnumbers[@]}"))
                files=($(remove_from_list $file "${files[@]}"))

                # Resubmit as a new job number
                #jobnumber=$(submit_jobs.bash $file_pattern --step_name $step_name --step_max_tasks $step_max_tasks --total_max_tasks $SJOBS_TOTAL_MAX_TASKS 2> /dev/null) 
                jobnumber=$(submit_jobs.bash $file_pattern 2> /dev/null)
                exit_status="$?"
                if [[ $exit_status -eq 0 ]]; then
                    jobnumbers+=("$jobnumber")
                    files+=("$file")
                    j=$(($j-1))
                    echo "Resubmitted as jobumber: ${jobnumber}."
                else
                    echo "Error on resubmit for $jobnumber. Exiting."
                    exit 1
                fi
            elif [[ ( $state == *"FAILED"* || $state ==  *"CANCELLED"* ) ]]; then
                echo "Job $file, $j: state FAILED or CANCELLED. Exiting."
                echo "There could be other problem jobs. Need to change  run_workflow so that it exits after loop over all jobs completed"
                echo "Need to modify code  to resubmit cancelled, failed jobs once (unclear how to count)"
                exit 1; 
            else
                echo "Strange job state: $state, encountered."
                continue;
            fi

        done

        num_waiting=$(($num_jobs-$num_complete-$num_running-$num_pending))

        printf "%s, %s, %-7s: %-12s, %-10s, %-10s, %-12s.\n" "$PROJECT_NAME" "$step_name_long" "$num_jobs jobs" "$num_complete COMPLETED" "$num_running RUNNING" "$num_pending PENDING" "$num_waiting WAITING"
    done

    # Run check_job_output.py on all files
    cmd="check_job_outputs.py  ${files[@]} $tmp_flag_str"
    echo "$cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
        echo "Error in run_workflow.bash: check_job_outputs.py exited with code ($exit_status)."
        exit 1
    fi
    echo
done

