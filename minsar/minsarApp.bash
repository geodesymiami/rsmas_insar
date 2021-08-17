#! /bin/bash
#set -x

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
   --mintpy --minopy    both                                                     \n
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

template_file=$1
if [[ $1 == $PWD ]]; then
   template_file=$TEMPLATES/$PROJECT_NAME.template
fi

WORK_DIR=$SCRATCHDIR/$PROJECT_NAME

mkdir -p $WORK_DIR
cd $WORK_DIR

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` $@ " | tee -a "${WORK_DIR}"/log

copy_to_tmp="--tmp"

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
        --no_tmp)
            copy_to_tmp=""
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

download_flag=1
dem_flag=1
jobfiles_flag=1
ifgrams_flag=1

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

upload_flag=1
insarmaps_flag=1
finishup_flag=1

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

echo "Flags for processing steps:"
echo "download dem jobfiles ifgrams mintpy minopy upload insarmaps"
echo "    $download_flag     $dem_flag      $jobfiles_flag      $ifgrams_flag        $mintpy_flag     $minopy_flag      $upload_flag       $insarmaps_flag"
if [[ $copy_to_tmp == "--tmp" ]]; then
    echo "Copying files to /tmp"
fi

###################################
# adjust insarmaps_flag based on $template_file
str_insarmaps_flag=($(grep ^insarmaps $template_file | cut -d "=" -f 2 | xargs))
length_str_insarmaps_flag=$(wc -w <<< $str_insarmaps_flag)
[[ $length_str_insarmaps_flag == '0' ]] && str_insarmaps_flag=False 
str_insarmaps_flag=${str_insarmaps_flag[-1]}
if [[ $str_insarmaps_flag == "False" ]]; then
   insarmaps_flag=0
fi

####################################
if  ! test -f "$SCRATCH/miniconda3.tar" ; then
    echo "Copying miniconda3.tar to SCRATCH ..."
    cp $RSMASINSAR_HOME/3rdparty/miniconda3.tar $SCRATCH
fi
####################################
if  ! test -f "$SCRATCHDIR/S1orbits.tar" ; then
    echo "Copying S1orbits.tar to SCRATCHDIR ..."
    cp $WORK/S1orbits.tar $SCRATCH
fi

if [ ! "$(ls -A $SCRATCHDIR/S1orbits)" ]; then
     echo "SCRATCHDIR/S1orbits is empty, untarring S1orbits.tar ..."
     tar xf $SCRATCHDIR/S1orbits.tar -C $SCRATCHDIR
fi
# download latest orbits from ASF mirror
cd $SCRATCHDIR/S1orbits
curl --ftp-ssl --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_poeorb/ > ASF_poeorb.txt
curl --ftp-ssl --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_resorb/ > ASF_resorb.txt
cat ASF_poeorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_poeorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep 20210[4-9] > ASF_poeorb_latest.txt
cat ASF_resorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep 20210[4-9] > ASF_resorb_latest.txt
bash ASF_poeorb_latest.txt
#bash ASF_resorb_latest.txt

cd -
####################################
download_dir=$WORK_DIR/SLC

platform_str=$(grep platform $template_file | cut -d'=' -f2)
if [[ $platform_str == *"COSMO-SKYMED"* ]]; then
   download_dir=$WORK_DIR/RAW_data
fi
echo download_dir: $download_dir
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
fi

if [[ $dem_flag == "1" ]]; then
    cmd=" dem_rsmas.py $template_file"
    echo "Running... $cmd"
    echo "$cmd" | bash
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "dem_rsmas.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $jobfiles_flag == "1" ]]; then
    cmd="create_runfiles.py $template_file --jobfiles --queue $QUEUENAME $copy_to_tmp"
    echo "Running.... $cmd >create_jobfiles.e 1>out_create_jobfiles.o"
    $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    # # modify config files to use /tmp on compute node

fi

if [[ $ifgrams_flag == "1" ]]; then
    # possibly set local WEATHER_DIR if WORK is slow
    #timeout 2 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #timeout 0.1 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #cmd_try="download_ERA5_data.py --date_list SAFE_files.txt $template_file"

    # need to use differnt date_list file for CSK
    download_ERA5_cmd=`which download_ERA5_data.py`
    cmd="$download_ERA5_cmd --date_list SAFE_files.txt $template_file --weather_dir $WEATHER_DIR "
    echo " Running.... python $cmd >& out_download_ERA5_data.e &"
    python $cmd >& out_download_ERA5_data.e &
    echo "$(date +"%Y%m%d:%H-%m") * download_ERA5_data.py --date_list SAFE_files.txt $template_file --weather_dir $WEATHER_DIR " >> "${WORK_DIR}"/log

 
    cmd="run_workflow.bash $template_file --dostep ifgrams $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash --dostep ifgrams  exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    # correct *xm and *vrt files
    sed -i "s|/tmp|$PWD|g" */*.xml */*/*.xml  */*/*/*.xml 
    sed -i "s|/tmp|$PWD|g" */*.vrt */*/*.vrt  */*/*/*.vrt 
fi

if [[ $mintpy_flag == "1" ]]; then
    cmd="run_workflow.bash $PWD --append --dostep mintpy $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash --start mintpy exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $minopy_flag == "1" ]]; then
    cmd="minopyApp.py $template_file --dir minopy --jobfiles"
    echo "Running.... $cmd"
    $cmd
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
       echo "run_workflow.bash --start minopy exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $upload_flag == "1" ]]; then
    cmd="upload_data_products.py $template_file --mintpyProducts"
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

