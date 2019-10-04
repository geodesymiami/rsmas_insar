#!/usr/bin/env bash
echo "sourcing ${RSMASINSAR_HOME}/setup/environment.bash ..."
#####################################
# Setting the environment (don't modify)
# check for required variables
[ -z $RSMASINSAR_HOME ] && echo ERROR: RSMASINSAR_HOME is required variable && return
[ -z $JOBSCHEDULER ] && echo ERROR: JOBSCHEDULER is required variable && return
[ -z $QUEUENAME ] && echo ERROR: QUEUENAME is required variable && return
[ -z $SCRATCHDIR ] && echo ERROR: SCRATCHDIR is required variable && return

#  set customizable variables to defaults if not given
[ -z ${WORKDIR} ] && export WORKDIR=~/insarlab
[ -z ${USER_PREFERRED} ] && export USER_PREFERRED=$USER
[ -z ${DOWNLOADHOST} ] && export DOWNLOADHOST=local
[ -z ${JOBSHEDULER_PROJECTNAME} ] && export JOBSHEDULER_PROJECTNAME=insarlab
[ -z ${SENTINEL_ORBITS} ] && export SENTINEL_ORBITS=${WORKDIR}/S1orbits
[ -z ${SENTINEL_AUX} ] && export SENTINEL_AUX=${WORKDIR}/S1aux
[ -z ${WEATHER_DIR} ] && export WEATHER_DIR=${WORKDIR}/WEATHER
[ -z ${TESTDATA_ISCE} ] && export TESTDATA_ISCE=${WORKDIR}/TESTDATA_ISCE

############ FOR PROCESSING  #########
export SSARAHOME=${RSMASINSAR_HOME}/3rdparty/SSARA
export ISCE_HOME=${RSMASINSAR_HOME}/3rdparty/miniconda3/lib/python3.7/site-packages/isce
export ISCE_STACK=${RSMASINSAR_HOME}/sources/isceStack/topsStack
export MINTPY_HOME=${RSMASINSAR_HOME}/sources/MintPy
export MINOPY_HOME=${RSMASINSAR_HOME}/sources/minopy
export MIMTPY_HOME=${RSMASINSAR_HOME}/sources/MimtPy
export JOBDIR=${WORKDIR}/JOBS
export OPERATIONS=${WORKDIR}/OPERATIONS

############ FOR MODELLING  ###########
export MODELDATA=${WORKDIR}/MODELDATA
export GEODMOD_INFILES=${WORKDIR}/infiles/${USER_PREFERRED}/GEODMOD_INFILES
export GEODMOD_HOME=${RSMASINSAR_HOME}/sources/geodmod
export GEODMOD_TESTDATA=${WORKDIR}/TESTDATA_GEODMOD
export GBIS_TESTDATA=${WORKDIR}/TESTDATA_GBIS
export GEODMOD_TESTBENCH=${SCRATCHDIR}/GEODMOD_TESTBENCH
export GBIS_INFILES=${WORKDIR}/infiles/${USER_PREFERRED}/GBIS_INFILES

###########  USEFUL VARIABLES  #########
export SAMPLESDIR=${RSMASINSAR_HOME}/samples
export DEMDIR=${WORKDIR}/DEMDIR
export TEMPLATES=${WORKDIR}/infiles/${USER_PREFERRED}/TEMPLATES
export TE=${TEMPLATES}

############## DASK ##############
export DASK_CONFIG=${RSMASINSAR_HOME}/minsar/defaults/dask
export DASK_CONFIG=${RSMASINSAR_HOME}/sources/MintPy/mintpy/defaults

############## LAUNCHER ##############
export LAUNCHER_DIR=${RSMASINSAR_HOME}/3rdparty/launcher
export LAUNCHER_PLUGIN_DIR=${LAUNCHER_DIR}/plugins
export LAUNCHER_RMI=${JOBSCHEDULER}
export LAUNCHER_SCHED=block   ## could be one of: dynamic, interleaved, block

##############  PYTHON  ##############
export PYTHON3DIR=${RSMASINSAR_HOME}/3rdparty/miniconda3
export CONDA_ENVS_PATH=${PYTHON3DIR}/envs
export CONDA_PREFIX=${PYTHON3DIR}
export PROJ_LIB=${PYTHON3DIR}/share/proj
export GDAL_DATA=${PYTHON3DIR}/share/gdal

export PYTHONPATH=${PYTHONPATH-""}
export PYTHONPATH=${PYTHONPATH}:${MINTPY_HOME}
export PYTHONPATH=${PYTHONPATH}:${INT_SCR}
export PYTHONPATH=${PYTHONPATH}:${PYTHON3DIR}/lib/python3.7/site-packages:${ISCE_HOME}:${ISCE_HOME}/components
export PYTHONPATH=${PYTHONPATH}:${MINOPY_HOME}
export PYTHONPATH=${PYTHONPATH}:${MIMTPY_HOME}
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/sources/rsmas_tools
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/3rdparty/PyAPS
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/minsar/utils/ssara_ASF
export PYTHONPATH=${PYTHONPATH}:${ISCE_STACK}
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/sources      # needed for mimt. Need to talk to Sara on how to do this smarter
export PYTHONPATH_RSMAS=${PYTHONPATH}

######### Ignore warnings ############
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

#####################################
############  PATH  #################
#####################################
export PATH=${PATH}:${SSARAHOME}
export PATH=${PATH}:${SSARA_ASF}
export PATH=${PATH}:${MINOPY_HOME}
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar:${RSMASINSAR_HOME}/minsar/utils
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar/utils/ssara_ASF
export PATH=${PATH}:${RSMASINSAR_HOME}/setup/accounts
export PATH=${PATH}:${RSMASINSAR_HOME}/sources/rsmas_tools/SAR:${RSMASINSAR_HOME}/sources/rsmas_tools/GPS:${RSMASINSAR_HOME}/sources/rsmas_tools/notebooks
export PATH=${ISCE_HOME}/applications:${ISCE_HOME}/bin:${ISCE_STACK}:${PATH}
export PATH=${PATH}:${RSMASINSAR_HOME}/sources/MimtPy
export PATH=${PATH}:${MINTPY_HOME}/mintpy:${MINTPY_HOME}/sh
export PATH=${PYTHON3DIR}/bin:${PATH}
export PATH=${PATH}:${PROJ_LIB}
export PATH=${PATH}:${RSMASINSAR_HOME}/3rdparty/tippecanoe/bin
export PATH=${PATH}:${DASK_CONFIG}
[ -n ${MATLAB_HOME} ] && export PATH=${PATH}:${MATLAB_HOME}/bin

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH-""}
export LD_LIBRARY_PATH=${PYTHON3DIR}/lib
export LD_RUN_PATH=${PYTHON3DIR}/lib

if [ -n "${prompt}" ]
then
    echo "RSMASINSAR_HOME:" ${RSMASINSAR_HOME}
    echo "PYTHON3DIR:     " ${PYTHON3DIR}
    echo "SSARAHOME:      " ${SSARAHOME}
fi
