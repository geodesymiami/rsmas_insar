#! /bin/bash
#set -x

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                       \n\
  Examples:                                                                      \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep dem                \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --start  ifgrams            \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep upload             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
                                                                                 \n\
  Processing steps (start/end/dostep): \n\
   Command line options for steps processing with names are chosen from the following list: \n\
                                                                                 \n\
   ['download', 'dem', 'jobfiles', 'ifgrams', 'timeseries', 'insarmaps', 'upload']             \n\
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
    exit_status="$?"
    if [[ $PROJECT_NAME == "" ]]; then
       echo "Could not compute basename for that file. Exiting. Make sure you have specified an input file as the first argument."
       exit 1;
    fi
fi
template_file=$1
WORK_DIR=$SCRATCHDIR/$PROJECT_NAME

mkdir -p $WORK_DIR
cd $WORK_DIR

echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` $@ " >> "${WORK_DIR}"/log

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

if [[ ${#POSITIONAL[@]} -gt 1 ]]; then
    echo "Unknown parameters provided."
    exit 1;
fi

download_flag=1
dem_flag=1
jobfiles_flag=1
ifgrams_flag=1
timeseries_flag=1
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
elif [[ $startstep == "timeseries" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
elif [[ $startstep == "upload" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
elif [[ $startstep == "insarmaps" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
elif [[ $startstep == "finishup" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
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
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "dem" ]]; then
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "jobfiles" ]]; then
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "ifgrams" ]]; then
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "timeseries" ]]; then
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "upload" ]]; then
    upload_flag=0
    finishup_flag=0
elif [[ $stopstep == "insarmaps" ]]; then
    finishup_flag=0
elif [[ $stopstep != "" ]]; then
    echo "stopstep received value of "${stopstep}". Exiting."
    exit 1
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
cat ASF_poeorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_poeorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep 20210[4-9] > ASF_poeorb_latest.txt
bash ASF_poeorb_latest.txt
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
        echo "ssara_federated_query.bash exited with a non-zero exit code ($exit_status). Trying again in 5 hours."
        echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_status}. Trying again in 5 hours" >> /log
        echo "$(date +"%Y%m%d:%H-%m") * Something went wrong. Exit code was ${exit_status}. Trying again in 5 hours" >> ../log

        sleep 180 # sleep for 5 hours
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
    cmd="create_runfiles.py $template_file --jobfiles --queue $QUEUENAME"
    echo "Running.... $cmd >create_jobfiles.e 1>out_create_jobfiles.o"
    $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    
    # modify config files to use /tmp on compute node 

    # run_03_average_baseline`
    files="configs/config_baseline_*"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="geom_referenceDir : $PWD"
    new="geom_referenceDir : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_04_fullBurst_geo2rdr
    files="configs/config_fullBurst_geo2rdr_*"

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="geom_referenceDir : $PWD"
    new="geom_referenceDir : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_05_fullBurst_resample
    files="configs/config_fullBurst_resample_*"
    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_07_merge_reference_secondary_slc
    files="configs/config_merge_[0-9]*"

    old="stack : $PWD"
    new="stack : /tmp"
    sed -i "s|$old|$new|g" $files

    old="inp_reference : $PWD"
    new="inp_reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="dirname : $PWD"
    new="dirname : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_08_generate_burst_igram
    files="configs/config_generate_igram_*"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_09_merge_burst_igram
    files="configs/config_merge_igram_[0-9]*"

    old="stack : $PWD"
    new="stack : /tmp"
    sed -i "s|$old|$new|g" $files

    old="inp_reference : $PWD"
    new="inp_reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="dirname : $PWD"
    new="dirname : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_10_filter_coherence
    files="configs/config_igram_filt_coh_*"
    old="input : $PWD"
    new="input : /tmp"
    sed -i "s|$old|$new|g" $files

    #old="slc1 : $PWD/merged/SLC"
    #new="slc1 : /tmp"
    #sed -i "s|$old|$new|g" $files
    #old="slc2 : $PWD/merged/SLC"
    #new="slc2 : /tmp"
    #sed -i "s|$old|$new|g" $files

    # run_11_unwrap
    files="configs/config_igram_unw_*"

    old="ifg : $PWD"
    new="ifg : /tmp"
    sed -i "s|$old|$new|g" $files

    old="coh : $PWD"
    new="coh : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files


fi

if [[ $ifgrams_flag == "1" ]]; then
    # possibly set local WEATHER_DIR if WORK is slow
    #timeout 2 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #timeout 0.1 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #cmd_try="download_ERA5_data.py --date_list SAFE_files.txt $template_file"

    download_ERA5_cmd=`which download_ERA5_data.py`
    cmd="$download_ERA5_cmd --date_list SAFE_files.txt $template_file"
    echo " Running.... python $cmd >& out_download_ERA5_data.e &"
    python $cmd >& out_download_ERA5_data.e &
    echo "$(date +"%Y%m%d:%H-%m") * $cmd" >> "${WORKDIR}"/log

 
    cmd="submit_jobs.bash $template_file --stop ifgrams"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "submit_jobs.bash --stop ifgrams  exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $timeseries_flag == "1" ]]; then
    cmd="submit_jobs.bash $PWD --dostep timeseries"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "submit_jobs.bash --start timeseries exited with a non-zero exit code ($exit_status). Exiting."
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
    cmd="submit_jobs.bash $PWD --dostep insarmaps"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "submit_jobs.bash --dostep insarmaps exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $finishup_flag == "1" ]]; then
    cmd="summarize_job_run_times.py $template_file"
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

