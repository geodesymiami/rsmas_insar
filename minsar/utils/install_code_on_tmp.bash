##! /bin/bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                              \n\
  Examples:                                                                             \n\
      install_code_on_tmp.bash                                                          \n\
      install_code_on_tmp.bash smallbaseline_wrapper.job                                \n\
      install_code_on_tmp.bash mintpy                                                   \n\
      install_code_on_tmp.bash minopy.job                                               \n\
      install_code_on_tmp.bash minopy                                                   \n\
      install_code_on_tmp.bash insarmaps                                                \n\
                                                                                        \n\
  Installs code on /tmp (includes MintPy, MinoPy, insarmaps_ingest depending on options)\n                                                          \n
     "
printf "$helptext"
exit 0;
fi

###########################################
job_name="$1"

module load TACC
if [[ $PLATFORM_NAME == *"stampede2"* ]]; then
    export CDTOOL=/scratch/01255/siliu/collect_distribute
elif [[ $PLATFORM_NAME == *"frontera"* ]]; then
    export CDTOOL=/scratch1/01255/siliu/collect_distribute
fi
module load intel/19.1.1 2> /dev/null
export PATH=${PATH}:${CDTOOL}/bin

#df -h /tmp
rm -rf /tmp/rsmas_insar
mkdir -p /tmp/rsmas_insar
mkdir -p /tmp/rsmas_insar/3rdparty ;
mkdir -p /tmp/rsmas_insar/sources ;

code_dir=$(echo $(basename $(dirname $RSMASINSAR_HOME)))
distribute.bash $SCRATCHDIR/${code_dir}_miniconda3.tar
distribute.bash $SCRATCHDIR/${code_dir}_minsar.tar
tar xf /tmp/${code_dir}_miniconda3.tar -C /tmp/rsmas_insar/3rdparty
tar xf /tmp/${code_dir}_minsar.tar -C /tmp/rsmas_insar
rm /tmp/${code_dir}_miniconda3.tar
rm /tmp/${code_dir}_minsar.tar

echo After copy-to-tmp: `df -h /tmp`

echo "#### To set environment: ####"
echo "export PATH=/bin; export RSMASINSAR_HOME=/tmp/rsmas_insar; cd \$RSMASINSAR_HOME; source ~/accounts/platforms_defaults.bash; source setup/environment.bash; export PATH=\$ISCE_STACK/topsStack:\$PATH; cd -;"

