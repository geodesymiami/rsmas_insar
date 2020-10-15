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

if [[ $startstep == "dem" ]]; then
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
if [[ $download_flag == "1" ]]; then
    echo "Running.... download_ssara.py $template_file"
    download_ssara.py $template_file
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "download_ssara.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    cd SLC
    cat ../ssara_command.txt
    echo "Running.... 'cat ../ssara_command.txt'"
    bash ../ssara_command.txt
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "ssara_federated_query.bash exited with a non-zero exit code ($exit_status). Exiting."
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
    cmd="create_runfiles.py $template_file --jobfiles"
    echo "Running.... $cmd >create_jobfiles.e 1>out_create_jobfiles.o"
    $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
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
    last_file=($(tail -1 $WORK_DIR/SLC/ssara_listing.txt))
    last_date=${last_file[3]}
    echo "Last file: $last_file"
    echo "Last processed image date: $last_date"
    unset IFS
fi

