#_#! /bin/bash
##################################################################################
function create_template_array() {
mapfile -t array < <(grep -e ^minsar -e ^mintpy -e ^miaplpy $1)
declare -gA template
for item in "${array[@]}"; do
  #echo "item: <$item>"
  IFS='=' ; read -a arr1 <<< "$item"
  item="${arr1[1]}"
  IFS='#' ; read -a arr2 <<< "$item"
  key="${arr1[0]}"
  key=$(echo $key | tr -d ' ')
  value="${arr2[0]}"
  shopt -s extglob
  value="${value##*( )}"          # Trim leading whitespaces
  value="${value%%*( )}"          # Trim trailing whitespaces
  shopt -u extglob
  #echo "key, value: <$key> <$value>"
  if [ ! -z "$key"  ]; then
     template[$key]="$value"
  fi
unset IFS
done
}

###########################################
function get_date_str() {
# get string with start and end date
if  [ ! -z ${template[miaplpy.load.startDate]} ] && [ ! ${template[miaplpy.load.startDate]} == "auto" ]; then
    start_date=${template[miaplpy.load.startDate]} 
else
    start_date=$(ls merged/SLC | head -1)
fi
if  [ ! -z ${template[miaplpy.load.endDate]} ] && [ ! ${template[miaplpy.load.endDate]} == "auto" ]; then
    end_date=${template[miaplpy.load.endDate]} 
else
    end_date=$(ls merged/SLC | tail -1)
fi
date_str="${start_date:0:6}_${end_date:0:6}"
echo $date_str
}

###########################################
function get_miaplpy_dir_name() {
# assign miaplpyDir.Addition  lalo,dirname or 'miaplpy' for 'auto'
date_str=$(get_date_str)
if [ -z ${template[minsar.miaplpyDir.addition]} ] || [ ${template[minsar.miaplpyDir.addition]} == "auto" ]; then
   miaply_dir_name="miaplpy"
elif [ ${template[minsar.miaplpyDir.addition]} == "date" ]; then
   miaply_dir_name=miaplpy_${date_str}
elif [ ${template[minsar.miaplpyDir.addition]} == "lalo" ]; then
   if  [ ! -z ${template[miaplpy.subset.lalo]} ]; then
       subset_lalo="${template[miaplpy.subset.lalo]}"
   elif [ ! -z ${template[mintpy.subset.lalo]} ]; then
       subset_lalo="${template[mintpy.subset.lalo]}"
   else
       echo "ERROR: No subset.lalo given -- Exiting"
   fi
   IFS=',' ; read -a lalo_array <<< "$subset_lalo"
   IFS=':' ; read -a lat_array <<< "${lalo_array[0]}"
   IFS=':' ; read -a lon_array <<< "${lalo_array[1]}"
   lat_min=${lat_array[0]}
   lat_max=${lat_array[1]}
   lon_min=${lon_array[0]}
   lon_max=${lon_array[1]}
   lalo_str=$(printf "%.2f_%.2f_%.2f_%.2f\n" "$lat_min" "$lat_max" "$lon_min" "$lon_max")
   miaply_dir_name="miaplpy_${lalo_str}_$date_str"
else
   miaply_dir_name=miaplpy_"${template[minsar.miaplpyDir.addition]}"_${date_str}
fi
unset IFS
echo $miaply_dir_name
}
###########################################
function get_network_type {
# get single_reference or delaunay_4 ect. from template file
network_type=${template[miaplpy.interferograms.networkType]}
if [[ $network_type == "auto" ]] || [[ -z "$network_type" ]];   then
      network_type=single_reference                  # default of MiaplPy
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
echo $network_type
}
##################################################################################
##################################################################################
##################################################################################
source $RSMASINSAR_HOME/minsar/utils/minsar_functions.bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                       \n\
  Examples:                                                                      \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep dem                \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --start  ifgram            \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --dostep upload             \n\
      minsarApp.bash  $TE/GalapagosSenDT128.template --start jobfiles --mintpy --miaplpy\n\
      minsarApp.bash  $TE/GalapagosSenDT128.template                             \n\
                                                                                 \n\
  Processing steps (start/end/dostep): \n\
   Command line options for steps processing with names are chosen from the following list: \n\
                                                                                 \n\
   ['download', 'dem', 'jobfiles', 'ifgram', 'mintpy', 'miaplpy', 'insarmaps', 'upload']             \n\
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
   --miaplpy         use miaplpyApp.py                                           \n\
   --mintpy --miaplpy    both                                                    \n\
                                                                                 \n\
   --sleep SECS     sleep seconds before running                                 \n\
   --select_reference     select reference date [default].                       \n\
   --no_select_reference  don't select reference date.                           \n\
   --download_ECMWF       download from ECMWF during ISCE processing             \n\
   --no_download_ECMWF    don't download while processing                        \n\
   --chunks         process in form of multiple chunks.                          \n\
   --tmp            copy code and data to local /tmp [default].                  \n\
   --no-tmp         no copying to local /tmp. This can be                        \n 
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
export template_file
WORK_DIR=$SCRATCHDIR/$PROJECT_NAME
mkdir -p $WORK_DIR
cd $WORK_DIR

create_template_array $template_file
#echo template keys: ${!template[@]}

# create name including $TE for concise log file
template_file_dir=$(dirname "$template_file")          # create name including $TE for concise log file
if   [[ $template_file_dir == $TEMPLATES ]]; then
    template_print_name="\$TE/$(basename $template_file)"
elif [[ $template_file_dir == $SAMPLESDIR ]]; then
    template_print_name="\$SAMPLESDIR/$(basename $template_file)"
else
    template_print_name="$template_file"
fi
echo "$(date +"%Y%m%d:%H-%M") * minsarApp.bash $template_print_name ${@:2}" | tee -a "${WORK_DIR}"/log

#Switches
chunks_flag=0
jobfiles_flag=1
select_reference_flag=1
new_reference_flag=0
download_ECMWF_flag=1
download_ECMWF_before_mintpy_flag=0

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

# Default steps
download_flag=1
dem_flag=1
ifgram_flag=1
mintpy_flag=1
miaplpy_flag=0
upload_flag=1
insarmaps_flag=1
finishup_flag=1

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
        --no-mintpy)
            mintpy_flag=0
            shift
            ;;
        --miaplpy)
            miaplpy_flag=1
            shift
            ;;
        --no-upload)
            upload_flag=0
            shift
            ;;
        --no-insarmaps)
            insarmaps_flag=0
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
        --no-tmp)
            copy_to_tmp="--no-tmp"
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

# always use --no-tmp on stampede3
if [[ $HOSTNAME == *"stampede3"* ]] && [[ $copy_to_tmp == "--tmp" ]]; then
   copy_to_tmp="--no-tmp"
   runfiles_dir="run_files"
   configs_dir="configs"
   echo "Running on stampede3: switched from --tmp to --no-tmp because of too slow copying to /tmp"
fi
miaplpy_tmp_flag=$copy_to_tmp   

if [[ ${#POSITIONAL[@]} -gt 1 ]]; then
    echo "Unknown parameters provided."
    exit 1;
fi

if [ ! -z ${sleep_time+x} ]; then
  echo "sleeping $sleep_time secs before starting ..."
  sleep $sleep_time
fi

#if [[ -v mintpy_flag ]]; then lock_mintpy_flag=1; fi
#mintpy_flag=1
#if [[ -v miaplpy_flag ]]; then  
#    miaplpy_flag=1;
#   if [[ -v lock_mintpy_flag ]]; then
#      mintpy_flag=1; 
#   else
#      mintpy_flag=0; 
#   fi
#else
#    miaplpy_flag=0;
#fi

if [[ $startstep == "download" ]]; then
    download_flag=1
elif [[ $startstep == "dem" ]]; then
    download_flag=0
    dem_flag=1
elif [[ $startstep == "jobfiles" ]]; then
    download_flag=0
    dem_flag=0
elif [[ $startstep == "ifgram" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
elif [[ $startstep == "mintpy" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
elif [[ $startstep == "miaplpy" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=1
elif [[ $startstep == "upload" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=0
elif [[ $startstep == "insarmaps" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=0
    upload_flag=0
elif [[ $startstep == "finishup" ]]; then
    download_flag=0
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=0
    upload_flag=0
    insarmaps_flag=0
elif [[ $startstep != "" ]]; then
    echo "startstep received value of "${startstep}". Exiting."
    exit 1
fi

if [[ $stopstep == "download" ]]; then
    dem_flag=0
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    minooy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "dem" ]]; then
    jobfiles_flag=0
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "jobfiles" ]]; then
    ifgram_flag=0
    mintpy_flag=0
    miaplpy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "ifgram" ]]; then
    mintpy_flag=0
    miaplpy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "mintpy" ]]; then
    miaplpy_flag=0
    upload_flag=0
    insarmaps_flag=0
    finishup_flag=0
elif [[ $stopstep == "miaplpy" ]]; then
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
echo "download dem jobfiles ifgram mintpy miaplpy upload insarmaps finishup"
echo "    $download_flag     $dem_flag      $jobfiles_flag       $ifgram_flag       $mintpy_flag      $miaplpy_flag      $upload_flag       $insarmaps_flag        $finishup_flag"

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

# FA 12/23  remove checking/copying of miniconda3.tar
#code_dir=$(echo $(basename $(dirname $RSMASINSAR_HOME)))
#if  ! test -f "$SCRATCHDIR/${code_dir}_miniconda3.tar" || [[ "$RSMASINSAR_HOME/tools/miniconda3.tar" -nt "$SCRATCHDIR/${code_dir}_miniconda3.tar" ]]; then
#    echo "Copying $RSMASINSAR_HOME/tools/miniconda3.tar to $SCRATCHDIR/${code_dir}_miniconda3.tar ..."
#    cp $RSMASINSAR_HOME/tools/miniconda3.tar $SCRATCHDIR/${code_dir}_miniconda3.tar
#fi
#if  ! test -f "$SCRATCHDIR/${code_dir}_minsar.tar" || [[ "$RSMASINSAR_HOME/minsar.tar" -nt "$SCRATCHDIR/${code_dir}_minsar.tar" ]]; then
#    echo "Copying $RSMASINSAR_HOME/minsar.tar to $SCRATCHDIR/${code_dir}_minsar.tar ..."
#    cp $RSMASINSAR_HOME/minsar.tar $SCRATCHDIR/${code_dir}_minsar.tar
#fi

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
collectionName_str=$(grep collectionName $template_file | cut -d'=' -f2)
if [[ $collectionName_str == *"TSX"* ]]; then
   download_dir=$WORK_DIR/SLC_ORIG
fi
####################################
srun_cmd="srun -n1 -N1 -A $JOBSHEDULER_PROJECTNAME -p $QUEUENAME  -t 00:07:00 "
srun_cmd="srun -n1 -N1 -A $JOBSHEDULER_PROJECTNAME -p $QUEUENAME  -t 00:25:00 "
####################################
###       Processing Steps       ###
####################################
if [[ $download_flag == "1" ]]; then

    echo "Running.... generate_download_command.py $template_file"
    generate_download_command.py $template_file
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "generate_download_command.py exited with a non-zero exit code ($exit_status). Exiting."
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
       cmd="dem_rsmas.py $template_file --ssara_kml"
       #cmd="$srun_cmd -t 00:$job_minutes:00 $cmd"    # 1/23 swicthed off 
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
            --miaplpy)
                options="$options --miaplpy"
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
#############################################################
# download latest orbits from ASF mirror
    if [[ $template_file == *"Sen"*  ]]; then 
       echo "Preparing to download latest poe and res orbits from ASF..."
       year=$(date +%Y)
       current_month=$(date +%Y%m)
       previous_month=$(date -d'-1 month' +%Y%m)

       cd $WORKDIR/S1orbits
       curl --ftp-ssl-reqd --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_poeorb/ > ASF_poeorb.txt
       curl --ftp-ssl-reqd --silent --use-ascii --ftp-method nocwd --list-only https://s1qc.asf.alaska.edu/aux_resorb/ > ASF_resorb.txt
       cat ASF_poeorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_poeorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep $year > ASF_poeorb_latest.txt
       #cat ASF_resorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep $year > ASF_resorb_latest.txt
       cat ASF_resorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep $current_month  >  ASF_resorb_latest.txt
       cat ASF_resorb.txt | awk '{printf "! test -f %s && wget -c https://s1qc.asf.alaska.edu/aux_resorb/%s\n", substr($0,10,77), substr($0,10,77)}' | grep $previous_month >> ASF_resorb_latest.txt
       echo "Downloading poe orbits: running bash ASF_poeorb_latest.txt in orbit directory  $SENTINEL_ORBITS  ..."
       bash ASF_poeorb_latest.txt
       echo "Downloading res orbits: running bash ASF_resorb_latest.txt in orbit directory  $SENTINEL_ORBITS  ..."
       bash ASF_resorb_latest.txt
       cd -
    fi
    
    # clean directory for processing
    pwd=`pwd`; echo "DIR: $pwd"
    cmd="clean_dir.bash $PWD --runfiles --ifgram --mintpy --miaplpy"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "clean_dir.bash exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    cmd="create_runfiles.py $template_file --jobfiles --queue $QUEUENAME $copy_to_tmp"
    echo "Running.... $cmd >out_create_jobfiles.e 1>out_create_jobfiles.o"
    #$srun_cmd $cmd 2>create_jobfiles.e 1>out_create_jobfiles.o   # FA 1/23:  the 2 pipes more output to terminal (I think)
    $cmd 2>out_create_jobfiles.e 1>out_create_jobfiles.o
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
 
if [[ $ifgram_flag == "1" ]]; then
    # possibly set local WEATHER_DIR if WORK is slow
    #timeout 2 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #timeout 0.1 ls  $WEATHER_DIR/ERA5/* >> /dev/null ; echo $?
    #cmd_try="download_ERA5_data.py --date_list SAFE_files.txt $template_file"


    if [[ $template_file != *"Sen"* || $select_reference_flag == "0" ]]; then 
       cmd="run_workflow.bash $template_file --dostep ifgram $copy_to_tmp"
       echo "Running.... $cmd"
       $cmd
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "run_workflow.bash $template_file --dostep ifgram  exited with a non-zero exit code ($exit_status). Exiting."
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
          cmd="clean_dir.bash $PWD --runfiles --ifgram"
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
    #sed -i "s|/tmp|$PWD|g" */*.xml */*/*.xml  */*/*/*.xml 
    #sed -i "s|/tmp|$PWD|g" */*.vrt */*/*.vrt  */*/*/*.vrt 
    sed -i "s|/tmp|$PWD|g" merged/geom_reference/*.vrt merged/SLC/*/*.vrt   merged/interferograms/*/*vrt
    sed -i "s|/tmp|$PWD|g" merged/geom_reference/*.xml merged/SLC/*/*.xml   merged/interferograms/*/*xml
fi

########################
#       MintPy         #
########################
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

    # run MintPy 
    cmd="run_workflow.bash $template_file --append --dostep mintpy $copy_to_tmp"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$cmd exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    # upload mintpy directory 
    if [[ $upload_flag == "1" ]]; then
        cmd="upload_data_products.py --dir mintpy"
        echo "Running.... $cmd"
        echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
        $cmd 2>out_upload_mintpy_data_products.e 1>out_upload_mintpy_data_products.o & 
        exit_status="$?"
        if [[ $exit_status -ne 0 ]]; then
           echo "upload_data_products.py exited with a non-zero exit code ($exit_status). Exiting."
           exit 1;
        fi
    fi
fi

########################
#       MiaplPy        #
########################
if [[ $miaplpy_flag == "1" ]]; then
    # correct *xml and *vrt files (if skipped in ifgram step because of unwrap problems) (skipping merged/interferograms because it takes long)
    sed -i "s|/tmp|$PWD|g" merged/geom_reference/*.vrt merged/SLC/*/*.vrt  
    sed -i "s|/tmp|$PWD|g" merged/geom_reference/*.xml merged/SLC/*/*.xml  

    # unset $miaplpy_tmp_flag for --no-tmp as miaplpyApp.py does not understand --no-tmp option 
    if [[ $miaplpy_tmp_flag == "--no-tmp" ]]; then
       unset miaplpy_tmp_flag
    fi

    miaplpy_dir_name=$(get_miaplpy_dir_name)
    network_type=$(get_network_type)
    network_dir=${miaplpy_dir_name}/network_${network_type}

    # create miaplpy jobfiles
    cmd="miaplpyApp.py $template_file --dir $miaplpy_dir_name --jobfiles $miaplpy_tmp_flag"
    echo "Running.... $cmd"
    echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
    $srun_cmd $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$srun_cmd $cmd exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    # create the save_hdfeos5_radar jobfile and copy into network_*/runfiles (to run after miaplpy)
    cmd="create_save_hdf5_jobfile.py  $template_file $network_dir --queue $QUEUENAME --walltime 0:30"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$cmd with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
    mv save_hdfeos5_radar.job $network_dir/run_files/run_10_save_hdfeos5_radar_0.job

    # run miaplpy jobfiles
    cmd="run_workflow.bash $template_file --append --dostep miaplpy --dir $miaplpy_dir_name"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$cmd with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    # create index.html with all images
    cmd="create_html.py ${network_dir}/pic"
    echo "Running.... $cmd"
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "$cmd with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi

    # upload data products
    if [[ $upload_flag == "1" ]]; then
       cmd="upload_data_products.py --dir $network_dir"
       echo "Running.... $cmd"
       echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
       $cmd 2>out_upload_data_products.e 1>out_upload_data_products.o & 
       exit_status="$?"
       if [[ $exit_status -ne 0 ]]; then
          echo "upload_data_products.py exited with a non-zero exit code ($exit_status). Exiting."
          exit 1;
       fi
    fi   
fi


if [[ $insarmaps_flag == "1" ]]; then
    cmd="run_workflow.bash $PWD --append --dostep insarmaps $copy_to_tmp"
    echo "Running.... $cmd"
    echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
    $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "run_workflow.bash --dostep insarmaps exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
fi

if [[ $finishup_flag == "1" ]]; then
    if [[ $miaplpy_flag == "1" ]]; then
        miaplpy_opt="--miaplpyDir $miaplpy_dir_name"
    else
        miaplpy_opt=""
    fi
    cmd="summarize_job_run_times.py $template_file $copy_to_tmp $miaplpy_opt"
    echo "Running.... $cmd"
    $cmd
    echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
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

echo
echo "network_dir: <$network_dir>"
echo
echo "hdfeos5 files produced:"
ls mintpy/*he5 2>/dev/null
ls $network_dir/*he5 2>/dev/null
echo "Implement waiting for completion of  save_hdfeos5_radar.job to list radar coordinate files" 
echo

echo "Yup! That's all from minsarApp.bash."

