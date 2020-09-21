#! /bin/bash

PROJECT_DIR="$(readlink -f $1)"
template_file=$TEMPLATES/`basename $PROJECT_DIR`.template

#start_datetime=$(date +"%Y%m%d:%H-%m")
#echo "${start_datetime} * `basename "$0"` ${PROJECT_DIR} ${@:2}" >> "${PROJECT_DIR}"/log
echo "$(date +"%Y%m%d:%H-%m") * `basename "$0"` $@ " >> "${PROJECT_DIR}"/log

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
    ifgram_flags=1
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
    insarmaps_flag=0
fi

if [[ $download_flag == "1" ]]; then
    echo "download_ssara.py ${template_file}"
    download_ssara.py $template_file
    exit_status="$?"
    
    if [[ $exit_status -ne 0 ]]; then
       echo "download_ssara.py exited with a non-zero exit code ($exit_status). Exiting."
       exit $exit_status;
    fi
    
    ssara_cmd=$(cat ssara_command.txt)
    cd SLC
    eval "$ssara_cmd"    
    
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "ssara_federated_query.bash exited with a non-zero exit code ($exit_status). Exiting."
       cd ..
       exit $exit_status;
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
   echo do job_files
fi

if [[ $ifgrams_flag == "1" ]]; then
   echo do ifgrams
fi

if [[ $timeseries_flag == "1" ]]; then
   echo do timeseries
fi

if [[ $upload_flag == "1" ]]; then
   echo do upload
fi

if [[ $insarmaps_flag == "1" ]]; then
   echo do insarmaps
fi
