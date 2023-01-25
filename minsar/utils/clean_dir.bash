#! /bin/bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                     \n\
  Examples:                                                                    \n\
      clean_dir.bash                                                           \n\
      clean_dir.bash $PWD                                                      \n\
      clean_dir.bash $SAMPLESDIR/unittestGalapagos.template                    \n\
      clean_dir.bash  --process [default]                                      \n\
      clean_dir.bash  --no_mintpy                                              \n\
      clean_dir.bash  --no_runfiles                                            \n\
                                                                               \n\
   clean working directory for processing                                      \n\
                                                                               \n\
   --process           processed data including mintpy and miaplpy [default]    \n\
                       (same as --runfiles  --ifgram --mintpy --miaplpy)       \n\
   --no_mintpy         keep mintpy and miaplpy folders                          \n\
   --no_miaplpy         same                                                    \n\
   --no_runfiles       keep run_files and config directories                   \n\
                                                                               \n\
   --download          removes SLC, RAW_data [default: no]                     \n\
   --dem               removes DEM [default: no]                               \n\
   --runfiles          removes DEM [default: no]                               \n\
   --ifgram           removes ISCE-produced directories                       \n\
   --mintpy            removes mintpy directory                                \n\
   --miaplpy            removes miaplpy directory                                \n 
     "
    printf "$helptext"
    exit 0;
fi

if [[ $# -eq 0 ]]; then
  set -- "${@:1}" "--process"
fi

# change to directory if called with $TE/templatefile or $PWD as arguments
if [[ $# -eq 1 ]] && [[ $1 != *"--"* ]]; then
  if [[ $1 == *"template"* ]]; then
    PROJECT_NAME=$(basename "$1" | awk -F ".template" '{print $1}')
    WORKDIR=$SCRATCHDIR/$PROJECT_NAME
  else
    WORKDIR=$1
  fi
  cd $WORKDIR
  set -- "${@:1}" "--process"
fi

# set defaults and process command line arguments
download_flag=0
dem_flag=0
runfiles_flag=0
ifgram_flag=0
mintpy_flag=0
miaplpy_flag=0

while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        --process)
            runfiles_flag=1
            ifgram_flag=1
            mintpy_flag=1
            miaplpy_flag=1
            shift # past argument
            ;;
	--download)
            download_flag=1
            shift
            ;;
	--dem)
            dem_flag=1
            shift
            ;;
	--runfiles)
            runfiles_flag=1
            shift
            ;;
	--ifgram)
            ifgram_flag=1
            shift
            ;;
	--mintpy)
            mintpy_flag=1
            shift
            ;;
	--miaplpy)
            miaplpy_flag=1
            shift
            ;;
        --no_runfiles )
            runfiles_flag=0
            shift # past argument
            ;;
        --no_ifgram )
            ifgram_flag=0
            shift # past argument
            ;;
	--no_mintpy)
            mintpy_flag=0
            shift
            ;;
	--no_miaplpy)
            miaplpy_flag=0
            shift
            ;;
	--all)
            download_flag=1
            dem_flag=1
            runfiles_flag=1
            ifgram_flag=1
            mintpy_flag=1
            miaplpy_flag=1
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

####################################
#echo "Flags for cleaning:"
#echo "Directory: $PWD:"
#echo "download dem runfiles ifgram mintpy miaplpy" 
#echo "    $download_flag     $dem_flag      $runfiles_flag      $ifgram_flag        $mintpy_flag     $miaplpy_flag"

if [[ $download_flag == "1" ]]; then
    rm -rf SLC RAW_data
fi

if [[ $dem_flag == "1" ]]; then
    rm -rf DEM
fi

if [[ $runfiles_flag == "1" ]]; then
    rm -rf run_files run_files_tmp configs configs_tmp
fi

if [[ $ifgram_flag == "1" ]]; then
   rm -rf coreg_secondarys baselines coarse_interferograms secondarys geom_reference interferograms reference merged misreg stack hazard_products geom_reference_noDEM ESD *.{o,e} stdout_* remora_*'
   rm -rf baselines coregSLC geom_master Igrams merged offsets refineSecondaryTiming  SLC_crop stdout_* *.{o,e}'
fi

if [[ $mintpy_flag == "1" ]]; then
    rm -rf mintpy 
fi

if [[ $miaplpy_flag == "1" ]]; then
    rm -rf miaplpy 
fi



