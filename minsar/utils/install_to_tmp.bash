##! /bin/bash

job_name="$1"
prefix=""

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --prefix)
            prefix="$2"
            shift
            ;;
        *)
            POSITIONAL+=("$1") # save it in an array for later
            shift # past argument
            ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

# ------------------

df -h /tmp
rm -rf /tmp/rsmas_insar
mkdir -p /tmp/rsmas_insar
cp -r $RSMASINSAR_HOME/minsar /tmp/rsmas_insar
cp -r $RSMASINSAR_HOME/setup  /tmp/rsmas_insar
mkdir -p /tmp/rsmas_insar/3rdparty ;

if [[ $job_name == *"smallbaseline_wrapper"* || $job_name == *"insarmaps"* || $job_name == *"mintpy"* ]]; then
    mkdir -p /tmp/rsmas_insar/sources
    cp -r $RSMASINSAR_HOME/sources/MintPy /tmp/rsmas_insar/sources
    cp -r $RSMASINSAR_HOME/3rdparty/PyAPS /tmp/rsmas_insar/3rdparty
    cp -r $RSMASINSAR_HOME/sources/insarmaps_scripts /tmp/rsmas_insar/sources
fi

if [[ $job_name == *"minopy"* ]]; then
    mkdir -p /tmp/rsmas_insar/sources
    cp -r $RSMASINSAR_HOME/sources/MiNoPy /tmp/rsmas_insar/sources
    cp -r $RSMASINSAR_HOME/sources/MintPy /tmp/rsmas_insar/sources
fi

cp -r $RSMASINSAR_HOME/3rdparty/launcher /tmp/rsmas_insar/3rdparty 
cp $SCRATCH/miniconda3.tar /tmp
tar xf /tmp/miniconda3.tar -C /tmp/rsmas_insar/3rdparty
rm /tmp/miniconda3.tar
cp -r $RSMASINSAR_HOME/sources/isce2/contrib/stack/*  /tmp/rsmas_insar/3rdparty/miniconda3/share/isce2
# set environment    
export RSMASINSAR_HOME=/tmp/rsmas_insar

if [[ $prefix == *"stripmap"* ]]; then
    cd $RSMASINSAR_HOME
    source ~/accounts/platforms_defaults.bash
    source setup/environment.bash
    export PATH=$ISCE_STACK/stripmapStack:$PATH;
    cd -
else
    cd $RSMASINSAR_HOME
    source ~/accounts/platforms_defaults.bash
    source setup/environment.bash
    export PATH=$ISCE_STACK/topsStack:$PATH
    cd -
fi

cd $RSMASINSAR_HOME; source ~/accounts/platforms_defaults.bash; source setup/environment.bash; export PATH=$ISCE_STACK/topsStack:$PATH; cd -;
# remove /scratch and /work from PATH
export PATH=`echo ${PATH} | awk -v RS=: -v ORS=: '/scratch/ {next} {print}' | sed 's/:*$//'` 
export PATH=`echo ${PATH} | awk -v RS=: -v ORS=: '/work/ {next} {print}' | sed 's/:*$//'` 
export PATH=`echo ${PATH} | awk -v RS=: -v ORS=: '/home/ {next} {print}' | sed 's/:*$//'` 
export PYTHONPATH=`echo ${PYTHONPATH} | awk -v RS=: -v ORS=: '/scratch/ {next} {print}' | sed 's/:*$//'` 
export PYTHONPATH=`echo ${PYTHONPATH} | awk -v RS=: -v ORS=: '/home/ {next} {print}' | sed 's/:*$//'` 
export PYTHONPATH_RSMAS=`echo ${PYTHONPATH_RSMAS} | awk -v RS=: -v ORS=: '/scratch/ {next} {print}' | sed 's/:*$//'` 
export PYTHONPATH_RSMAS=`echo ${PYTHONPATH_RSMAS} | awk -v RS=: -v ORS=: '/home/ {next} {print}' | sed 's/:*$//'`

echo After copy-to-tmp: `df -h /tmp`cat