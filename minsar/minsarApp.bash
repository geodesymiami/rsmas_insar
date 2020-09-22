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
fi
template_file=$1
WORK_DIR=$SCRATCHDIR/$PROJECT_NAME

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

download_flag=1
dem_flag=1
jobfiles_flag=1
ifgrams_flag=1
timeseries_flag=1
upload_flag=1
insarmaps_flag=1

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
    ifgrams_flags=0
    timeseries_flag=0
elif [[ $startstep == "insarmaps" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
fi

if [[ $stopstep == "download" ]]; then
    dem_flag=0
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $stopstep == "dem" ]]; then
    jobfiles_flag=0
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $stopstep == "jobfiles" ]]; then
    ifgrams_flag=0
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $stopstep == "ifgrams" ]]; then
    timeseries_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $stopstep == "timeseries" ]]; then
    upload_flag=0
    insarmaps_flag=0
elif [[ $stopstep == "upload" ]]; then
    upload_flag=0
fi

if [[ $download_flag == "1" ]]; then
    echo "Running.... download_ssara.py $template_file"
    string="`download_ssara.py $template_file`"
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "download_ssara.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    cd SLC
    echo "Running.... `cat ../ssara_command.txt`"
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
    cmd="dem_rsmas.py $template_file"
    echo "$cmd"
    echo "$cmd" | bash
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "dem_rsmas.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $jobfiles_flag == "1" ]]; then
    cmd="create_runfiles.py $template_file --jobfiles"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "create_jobfile.py exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $ifgrams_flag == "1" ]]; then
    cmd="submit_jobs.bash $template_file --stop timeseries"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "submit_jobs.bash --stop timeseires exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    timeseries_flag=0
fi

echo QQ $download_flag $dem_flag $jobsfile_flag $ifgrams_flag $timeseries_flag
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
    $cmd
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

