##################################################################################
source $RSMASINSAR_HOME/minsar/utils/minsar_functions.bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                       \n\
  Examples:                                                                      \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep dem                \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --start  ifgrams            \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep upload             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --start jobfiles --mintpy --minopy\n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
                                                                                 \n\
  Processing steps (start/end/dostep): \n\
   Command line options for steps processing with names are chosen from the following list: \n\
                                                                                 \n\
   ['download', 'dem', 'jobfiles', 'ifgrams', 'mintpy', 'minopy', 'insarmaps', 'upload']             \n\
                                                                                 \n\
   In order to use either --start or --dostep, it is necessary that a            \n\
   previous run was done using one of the steps options to process at least      \n\
   through the step immediately preceding the starting step of the current run.  \n\
                                                                                 \n\
   --start STEP     start processing at the named step [default: download].      \n\
   --end STEP, --stop STEP                                                       \n\
                    end processing at the named step [default: upload]           \n\
   --dostep STEP    run processing at the named step only                        \n\
                                                                                 \n\
   --mintpy         use smallbaselineApp.py for time series [default]            \n\
   --minopy         use minopyApp.py                                             \n\
   --mintpy --minopy    both                                                     \n\
                                                                                 \n\
   --sleep SECS     sleep seconds before running                                 \n\
   --select_reference     select reference date [default].                       \n\
   --no_select_reference  don't select reference date.                           \n\
   --download_ECMWF       download from ECMWF during ISCE processing             \n\
   --no_download_ECMWF    don't download while processing                        \n\
   --chunks         process in form of multiple chunks.                          \n\
   --tmp            copy code and data to local /tmp [default].                  \n\
   --no_tmp         no copying to local /tmp. This can be                        \n 
     "
    printf "$helptext"
    exit 0;
else
    PROJECT_NAME=$(basename "$1" | awk -F ".template" '{print $1}')
    exit_status="$?"
    if [[ $PROJECT_NAME == "" ]]; then
       echo "Could not compute basename for that file. Exiting. Make sure you have specified an input file as the first argument."
       exit 1;
    fi
fi

#set -xv
template_file=$1
if [[ $1 == $PWD ]]; then
   template_file=$TEMPLATES/$PROJECT_NAME.template
fi

WORK_DIR=$SCRATCHDIR/$PROJECT_NAME

mkdir -p $WORK_DIR
cd $WORK_DIR

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` $@ " | tee -a "${WORK_DIR}"/log

#Switches
chunks_flag=0
jobfiles_flag=1
select_reference_flag=1
new_reference_flag=0
download_ECMWF_flag=1
download_ECMWF_before_mintpy_flag=1

#Steps
download_flag=1
dem_flag=1
ifgrams_flag=1
upload_flag=1
insarmaps_flag=1
finishup_flag=1

copy_to_tmp="--tmp"
runfiles_dir="run_files_tmp"
configs_dir="configs_tmp"

##################################
# adjust some switches according to template options
str_insarmaps_flag=($(grep ^insarmaps $template_file | cut -d "=" -f 2 | xargs))
length_str_insarmaps_flag=$(wc -w <<< $str_insarmaps_flag)
[[ $length_str_insarmaps_flag == '0' ]] && str_insarmaps_flag=False 
str_insarmaps_flag=${str_insarmaps_flag[-1]}
if [[ $str_insarmaps_flag == "False" ]]; then
   insarmaps_flag=0
fi
#if [[ ! -z $(grep "^topsStack.referenceDate" $template_file) ]];  then
#   select_reference_flag=0
#fi
if [[ ! -z $(grep "^mintpy.troposphericDelay.method" $template_file) ]];  then
   tropo_correction_method=$(grep -E "^mintpy.troposphericDelay.method" $template_file | awk -F = '{printf "%s\n",$2}' | sed 's/ //' | awk -F ' '  '{print $1}')
   if [[ $tropo_correction_method == "height_correlation" || $tropo_correction_method == "no" ]]; then
      download_ECMWF_flag=0
      download_ECMWF_before_mintpy_flag=0
   fi
fi
##################################

args=( "$@" )    # copy of command line arguments

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
        --mintpy)
            mintpy_flag=1
            shift
            ;;
        --minopy)
            minopy_flag=1
            shift
            ;;
	--sleep)
            sleep_time="$2"
            shift
            shift
            ;;
        --tmp)
            copy_to_tmp="--tmp"
            runfiles_dir="run_files_tmp"
            configs_dir="configs_tmp"
            shift
            ;;
        --no_tmp)
            copy_to_tmp="--no_tmp"
            runfiles_dir="run_files"
            configs_dir="configs"
            shift
            ;;
        --select_reference)
            select_reference_flag=1
            shift
            ;;
        --no_select_reference)
            select_reference_flag=0
            shift
            ;;
        --download_ECMWF)
            download_ECMWF_flag=1
            shift
            ;;
        --no_download_ECMWF)
            download_ECMWF_flag=0
            shift
            ;;
        --chunks)
            chunks_flag=1
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ ${#POSITIONAL[@]} -gt 1 ]]; then
    echo "Unknown parameters provided."
    exit 1;
fi

if [ ! -z ${sleep_time+x} ]; then
  echo "sleeping $sleep_time secs before starting ..."
  sleep $sleep_time
fi

if [[ -v mintpy_flag ]]; then lock_mintpy_flag=1; fi
mintpy_flag=1
if [[ -v minopy_flag ]]; then  
    minopy_flag=1;
   if [[ -v lock_mintpy_flag ]]; then
      mintpy_flag=1; 
   else
      mintpy_flag=0; 
   fi
else
    minopy_flag=0;
fi

if [[ $startstep == "download" ]]; then
    download_flag=1
elif [[ $startstep == "dem" ]]; then
    download_flag=0
    dem_flag=1
elif [[ $startstep == "jobfiles" ]]; then
    download_flag=0
    dem_flag=0
elif [[ $startstep == "ifgrams" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
elif [[ $startstep == "mintpy" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
elif [[ $startstep == "minopy" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=1
elif [[ $startstep == "upload" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=0
elif [[ $startstep == "insarmaps" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=0
    upload_flag=0
elif [[ $startstep == "finishup" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $startstep != "" ]]; then
    echo "startstep received value of "${startstep}". Exiting."
    exit 1
fi

if [[ $stopstep == "download" ]]; then
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minooy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "dem" ]]; then
    jobfiles_flag=0
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "jobfiles" ]]; then
    ifgrams_flag=0
    mintpy_flag=0
    minopy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "ifgrams" ]]; then
    mintpy_flag=0
    minopy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "mintpy" ]]; then
    minopy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "minopy" ]]; then
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "upload" ]]; then
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "insarmaps" ]]; then
    finishup_flag=0
elif [[ $stopstep != "" ]]; then
    echo "stopstep received value of "${stopstep}". Exiting."
    exit 1
fi

if [[ $copy_to_tmp == "--tmp" ]]; then
    echo "copy_to_tmp  is ON"
else
    echo "copy_to_tmp is OFF"
fi
echo "Switches: select_reference: $select_reference_flag   download_ECMWF: $download_ECMWF_flag  chunks: $chunks_flag"
echo "Flags for processing steps:"
echo "download dem jobfiles ifgrams mintpy minopy upload insarmaps"
echo "    $download_flag     $dem_flag      $jobfiles_flag       $ifgrams_flag       $mintpy_flag      $minopy_flag      $upload_flag       $insarmaps_flag"

#############################################################
# check weather python can load matplotlib.pyplot which occasionaly does not work for unknown reasons

echo Testing ... python -c \"import matplotlib.pyplot\" using check_matplotlib_pyplot
check_matplotlib_pyplot;
exit_status="$?"
if [[ $exit_status -ne 0 ]]; then
   echo "Exit code ($exit_status). Exiting."
   exit 1;
fi
#############################################################
# check weather newest miniconda3.tar, minsar.tar,  S1orbits.tar and S1orbits exist on $SCRATCHDIR (might be purged) (partly only needed for --tmp)
# code_dir from RSMASINSAR_HOME directory is prepended to distingiush different minsar.tar versions

code_dir=$(echo $(basename $(dirname $RSMASINSAR_HOME)))
if  ! test -f "$SCRATCHDIR/${code_dir}_miniconda3.tar" || [[ "$RSMASINSAR_HOME/3rdparty/miniconda3.tar" -nt "$SCRATCHDIR/${code_dir}_miniconda3.tar" ]]; then
    echo "Copying $RSMASINSAR_HOME/3rdparty/miniconda3.tar to $SCRATCHDIR/${code_dir}_miniconda3.tar ..."
    cp $RSMASINSAR_HOME/3rdparty/miniconda3.tar $SCRATCHDIR/${code_dir}_miniconda3.tar
fi
if  ! test -f "$SCRATCHDIR/${code_dir}_minsar.tar" || [[ "$RSMASINSAR_HOME/minsar.tar" -nt "$SCRATCHDIR/${code_dir}_minsar.tar" ]]; then
    echo "Copying $RSMASINSAR_HOME/minsar.tar to $SCRATCHDIR/${code_dir}_minsar.tar ..."
    cp $RSMASINSAR_HOME/minsar.tar $SCRATCHDIR/${code_dir}_minsar.tar
fi

#if  ! test -f "$SCRATCHDIR/S1orbits.tar" ; then
#    echo "Copying S1orbits.tar to $SCRATCHDIR ..."
#    cp $WORKDIR/S1orbits.tar $SCRATCHDIR
#fi
#if [ ! "$(ls -A $SCRATCHDIR/S1orbits)" ]; then
#     echo "SCRATCHDIR/S1orbits is empty. Untarring S1orbits.tar ..."
#     tar xf $SCRATCHDIR/S1orbits.tar -C $SCRATCHDIR
#fi
####################################
download_dir=$WORK_DIR/SLC

platform_str=$(grep platform $template_file | cut -d'=' -f2)
if [[ $platform_str == *"COSMO-SKYMED"* ]]; then
   download_dir=$WORK_DIR/RAW_data
fi
####################################
srun_cmd="srun -n1 -N1 -A $JOBSHEDULER_PROJECTNAME -p $QUEUENAME  -t 00:07:00 "
####################################
###       Processing Steps       ###
####################################
if [[ $download_flag == "1" ]]; then

    echo "Running.... download_data.py $template_file"
    download_data.py $template_file
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "download_data.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    cd $download_dir
    cat ../ssara_command.txt
    echo "Running.... 'cat ../ssara_command.txt'"
    bash ../ssara_command.txt
    exit_status="$?"
   
    runs=1
    while [ $exit_status -ne 0 ] && [ $runs -le 4 ]; do
        echo "ssara_federated_query.bash exited with a non-zero exit code ($exit_status). Trying again in 2 hours."
        echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_status}. Trying again in 2 hours" | tee -a log | tee -a ../log

        sleep 7200 # sleep for 2 hours
        bash ../ssara_command.txt
        exit_status="$?"
        runs=$((runs+1))
    done

    if [[ $runs -gt 4 ]]; then
       echo "ssara_federated_query.bash failed after 20 hours. Exiting."
       cd ..
       exit 1;
    fi
    cd ..

    # remove excluded dates
    if [[ ! -z $(grep "^minsar.excludeDates" $template_file) ]];  then
      date_string=$(grep ^minsar.excludeDates $template_file | awk -F = '{printf "%s\n",$2}')
      date_array=($(echo $date_string | tr ',' "\n"))
      echo "${date_array[@]}"
      
       for date in "${date_array[@]}"; do
           echo "Remove $date if exist"
           files="RAW_data/*$date*"
           echo "Removing: $files"
           rm $files
       done
    fi
fi

if [[ $dem_flag == "1" ]]; then
    if [[ ! -z $(grep -E "^stripmapStack.demDir|^topsStack.demDir" $template_file) ]];  then
       # copy DEM if given
       demDir=$(grep -E "^stripmapStack.demDir|^topsStack.demDir" $template_file | awk -F = '{printf "%s\n",$2}' | sed 's/ //')
       rm -rf DEM; eval "cp -r $demDir DEM"
    else   
       # download DEM
       delta_lat=$(grep -E "^topsStack.boundingBox" $template_file | tail -1 | awk '{ printf "%f\n",$4-$3}')
       job_minutes=$(echo $delta_lat  | awk '{ printf "%d\n",int($1 + 1)*4.5}')
       echo "delta_lat, job_minutes: $delta_lat, $job_minutes"
       cmd="$srun_cmd -t 00:$job_minutes:00 dem_rsmas.py $template_file --ssara_kml"
       echo "Running... $cmd >out_dem_rsmas.e 1>out_dem_rsmas.o"
       $cmd 2>out_dem_rsmas.e 1>out_dem_rsmas.o
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "dem_rsmas.py exited with a non-zero exit code ($exit_status). Exiting."
          exit 1;
       fi
    fi
fi

if [[ $chunks_flag == "1" ]]; then
    # create string with minsar command options (could save options at beginning)
    set -- "${args[@]}"
    options=""
    while [[ $# -gt 0 ]]
    do
        key="$1"

        case $key in
            --start)
                options="$options --start $2"
                shift # past argument
                shift # past value
                ;;
            --stop)
                options="$options --stop $2"
                shift
                shift
                ;;
            --dostep)
                options="$options --dostep $2"
                shift
                shift
                ;;
            --mintpy)
                options="$options --mintpy"
                shift
                ;;
            --minopy)
                options="$options --minopy"
                shift
                ;;
            *)
                #POSITIONAL+=("$1") # save it in an array for later
                shift # past argument
                ;;
    esac
    done

    # generate chunk template files
    cmd="generate_chunk_template_files.py $template_file $options"
    echo "Running... $cmd >out_generate_chunk_template_files.e 1>out_generate_chunk_template_files.o"
    $cmd 2>out_generate_chunk_template_files.e 1>out_generate_chunk_template_files.o
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "generate_chunk_template_files.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    echo "Submitting chunk minsar jobs:" | tee -a log
    cat $WORK_DIR/minsar_commands.txt | tee -a log
    bash $WORK_DIR/minsar_commands.txt
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "bash $WORK_DIR/minsar_commands.txt exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    echo "Successfully submitted minsarApp.bash chunk jobs"
    exit 0
fi

if [[ $jobfiles_flag == "1" ]]; then
    
    # clean directory for processing
    cmd="clean_dir.bash $PWD --runfiles --ifgrams --mintpy --minopy"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "clean_dir.bash exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    cmd="create_runfiles.py $template_file --jobfiles --queue $QUEUENAME $copy_to_tmp"
    echo "Running.... $cmd >create_jobfiles.e 1>out_create_jobfiles.o"
    $srun_cmd $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

#    if [[ "$template_file" == *"SenAT"* || "$template_file" == *"SenDT"* ]]; then
#        # need to use differnt date_list file for CSK
#        download_ERA5_cmd=`which download_ERA5_data.py`
#        cmd="$download_ERA5_cmd --date_list SAFE_files.txt $template_file --weather_dir $WEATHER_DIR "
#        echo " Running.... python $cmd >& out_download_ERA5_data.e &"
#        python $cmd >& out_download_ERA5_data.e &
#        echo "$(date +"%Y%m%d:%H-%m") * download_ERA5_data.py --date_list SAFE_files.txt $template_file --weather_dir $WEATHER_DIR " >> "${WORK_DIR}"/log
#    fi

fi
 
if [[ $ifgrams_flag == "1" ]]; then
    # possibly set local WEATHER_DIR if WORK is slow
    #timeout 2 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #timeout 0.1 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #cmd_try="download_ERA5_data.py --date_list SAFE_files.txt $template_file"

#############################################################
# download latest orbits from ASF mirror
    if [[ $template_file == *"Sen"*  ]]; then 
       echo "Downloading latest orbits from ASF..."
       cd $WORKDIR/S1orbits
       curl --ftp-ssl --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_poeorb/ > ASF_poeorb.txt
       curl --ftp-ssl --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_resorb/ > ASF_resorb.txt
       cat ASF_poeorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_poeorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep 20210[4-9] > ASF_poeorb_latest.txt
       cat ASF_resorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep 20210[4-9] > ASF_resorb_latest.txt
       bash ASF_poeorb_latest.txt
       cd -
    fi

    if [[ $template_file != *"Sen"* || $select_reference_flag == "0" ]]; then 
       cmd="run_workflow.bash $template_file --dostep ifgrams $copy_to_tmp"
       echo "Running.... $cmd"
       $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "run_workflow.bash $template_file --dostep ifgrams  exited with a non-zero exit code ($exit_status). Exiting."
          exit 1;
       fi

    else

       # run with checking and selecting of reference date
       echo "### Running step 1 to 5 to check whether reference date has enough bursts"
       cmd="run_workflow.bash $template_file --start 1 --stop 5 $copy_to_tmp"
       echo "Running.... $cmd"
       $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "run_workflow.bash $template_file --start 1 --stop 5 exited with a non-zero exit code ($exit_status). Exiting."
          exit 1;
       fi

       reference_date=$(get_reference_date)
       echo "Reference date: $reference_date" | tee reference_date_isce.txt

       # determine whether to select new reference date
       countbursts | tr '/' ' ' | sort -k 1 | sort -k 2 | sort -k 4 -s | sed 's/ /\//' > number_of_bursts_sorted.txt
       number_of_dates_with_less_or_equal_bursts_than_reference=$(grep -n reference number_of_bursts_sorted.txt | cut -f1 -d:)
       number_of_dates_with_less_bursts_than_reference=$(( $number_of_dates_with_less_or_equal_bursts_than_reference - 1 ))
       number_of_dates=$(wc -l < number_of_bursts_sorted.txt)
       percentage_of_dates_with_less_bursts_than_reference=$(echo "scale=2; $number_of_dates_with_less_bursts_than_reference / $number_of_dates * 100"  | bc)
       echo "#########################################" | tee -a log | tee -a `ls wor* | tail -1`
       echo "Number of dates with less bursts than reference: $number_of_dates_with_less_bursts_than_reference" | tee -a log | tee -a  `ls wor* | tail -1`
       echo "Total number of dates: $number_of_dates" | tee -a log | tee -a  `ls wor* | tail -1`
       echo "Percentage of dates with less bursts than reference: $percentage_of_dates_with_less_bursts_than_reference" | tee -a log | tee -a  `ls wor* | tail -1`
       echo "# head -$number_of_dates_with_less_or_equal_bursts_than_reference  number_of_bursts_sorted.txt:" | tee -a log | tee -a `ls wor* | tail -1`
       head -"$number_of_dates_with_less_or_equal_bursts_than_reference" number_of_bursts_sorted.txt | tee -a log | tee -a `ls wor* | tail -1`
       percentage_of_dates_allowed_to_exclude=3  # FA 12 Mar 2022: changed to 1 %
       percentage_of_dates_allowed_to_exclude=1
       tmp=$(echo "$percentage_of_dates_allowed_to_exclude $number_of_dates" | awk '{printf "%f", $1 / 100 * $2}')
       number_of_dates_allowed_to_exclude="${tmp%.*}"
       new_reference_date=$(head -$((number_of_dates_allowed_to_exclude+1))  number_of_bursts_sorted.txt | tail -1 | awk '{print $1}' | cut -d'/' -f2)

       if [[ $(echo "$percentage_of_dates_with_less_bursts_than_reference > $percentage_of_dates_allowed_to_exclude"  | bc -l ) -eq 1 ]] && [[ $new_reference_date != $reference_date ]] ; then
          # insert new reference date into templatefile and rerun from beginning
          new_reference_flag=1
          echo "Original reference date:  $reference_date" | tee -a log | tee -a `ls wor* | tail -1` | tee reference_date_isce.txt
          echo "Selected reference date (image $((number_of_dates_allowed_to_exclude+1)) after sorting): $new_reference_date" | tee -a log | tee -a `ls wor* | tail -1` | tee -a tee reference_date_isce.txt
          echo "#########################################" | tee -a log | tee -a `ls wor* | tail -1`

          rm -rf modified_template
          mkdir modified_template
          cp $template_file modified_template
          template_file=$PWD/modified_template/$(basename $template_file)
          sed -i  "s|topsStack.subswath.*|&\ntopsStack.referenceDate              = $new_reference_date|" $template_file

          mv $runfiles_dir modified_template
          mv $configs_dir modified_template
          rm -rf run_files configs

          # clean directory for processing
          cmd="clean_dir.bash $PWD --runfiles --ifgrams"
          echo "Running.... $cmd"
          $cmd
          exit_status="$?"
          if [[ $exit_status -ne 0 ]]; then
             echo "clean_dir.bash exited with a non-zero exit code ($exit_status). Exiting."
             exit 1;
          fi

          cmd="create_runfiles.py $template_file --jobfiles --queue $QUEUENAME $copy_to_tmp"
          echo "Running.... $cmd >create_jobfiles.e 1>out_create_jobfiles.o"
          $srun_cmd $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o
          exit_status="$?"
          if [[ $exit_status -ne 0 ]]; then
             echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
             exit 1;
          fi

          # rerun steps 1 to 5  with new reference
	  echo "### Re-running step 1 to 5 with reference $new_reference_date"
          cmd="run_workflow.bash $template_file --start 1 --stop 5 $copy_to_tmp --append"
          echo "Running.... $cmd"
          $cmd
          exit_status="$?"
          if [[ $exit_status -ne 0 ]]; then
             echo "run_workflow.bash $template_file --start 1 --stop 5 exited with a non-zero exit code ($exit_status). Exiting."
             exit 1;
          fi
       else
          echo "No new reference date selected. Continue with original date: $reference_date" | tee -a log | tee -a `ls wor* | tail -1`
          echo "#########################################" | tee -a log | tee -a `ls wor* | tail -1`
       fi

       # continue running starting step 6
       cmd="run_workflow.bash $template_file --start 6 --stop 11 $copy_to_tmp --append"
       echo "Running.... $cmd"
       $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "run_workflow.bash $template_file --start 6 --stop 11 exited with a non-zero exit code ($exit_status). Exiting."
          exit 1;
       fi
    fi
    # correct *xml and *vrt files
    sed -i "s|/tmp|$PWD|g" */*.xml */*/*.xml  */*/*/*.xml 
    sed -i "s|/tmp|$PWD|g" */*.vrt */*/*.vrt  */*/*/*.vrt 
fi

if [[ $mintpy_flag == "1" ]]; then

    if [[ $download_ECMWF_before_mintpy_flag == "1" ]]  && [[ "$template_file" == *"SenAT"* || "$template_file" == *"SenDT"* ]]; then
        #download weather models - run mintpy after downnload is completed
        cmd="download_ERA5_data.py --date_list SAFE_files.txt $template_file --weather_dir $WEATHER_DIR"
        echo "Running.... $cmd" | tee -a log
        $cmd 2>out_download_ERA5_2.e 1>out_download_ERA5_2.o
        exit_status="$?"
        if [[ $exit_status -ne 0 ]]; then
           echo "download_ERA5_data.py exited with a non-zero exit code ($exit_status). Exiting."
           exit 1;
        fi
    fi

    cmd="run_workflow.bash $template_file --append --dostep mintpy $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash $template_file --start mintpy exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $minopy_flag == "1" ]]; then

    # correct *xml and *vrt files (if skipped in ifgram step because of unwrap problems) 
    #FA sed -i "s|/tmp|$PWD|g" */*.xml */*/*.xml  */*/*/*.xml   #FA 1/22: commented out because it takes too long
    #FA sed -i "s|/tmp|$PWD|g" */*.vrt */*/*.vrt  */*/*/*.vrt 

    cmd="minopyApp.py $template_file --dir minopy --jobfiles --tmp"
    echo "Running.... $cmd"
    echo "$cmd" | tee -a log
    $srun_cmd $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$cmd exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    cmd="run_workflow.bash $template_file --append --dostep minopy $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash $template_file --start minopy exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $upload_flag == "1" ]]; then
    cmd="upload_data_products.py $template_file --mintpy"
    echo "Running.... $cmd"
    $cmd 2>out_upload_data_products.e 1>out_upload_data_products.o & 
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "upload_data_products.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $insarmaps_flag == "1" ]]; then
    cmd="run_workflow.bash $PWD --append --dostep insarmaps $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash --dostep insarmaps exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $finishup_flag == "1" ]]; then
    cmd="summarize_job_run_times.py $template_file $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "summarize_job_run_times.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    IFS=","
    last_file=($(tail -1 $download_dir/ssara_listing.txt))
    last_date=${last_file[3]}
    echo "Last file: $last_file"
    echo "Last processed image date: $last_date"
    unset IFS
fi

echo "Yup! That's all from minsarApp.bash."

