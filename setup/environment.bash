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
[ -z ${NOTIFICATIONEMAIL} ] && export NOTIFICATIONEMAIL=${USER_PREFERRED}@rsmas.miami.edu
[ -z ${DOWNLOADHOST} ] && export DOWNLOADHOST=local
[ -z ${JOBSHEDULER_PROJECTNAME} ] && export JOBSHEDULER_PROJECTNAME=insarlab
[ -z ${SENTINEL_ORBITS} ] && export SENTINEL_ORBITS=${WORKDIR}/S1orbits
[ -z ${SENTINEL_AUX} ] && export SENTINEL_AUX=${WORKDIR}/S1aux
[ -z ${WEATHER_DIR} ] && export WEATHER_DIR=${WORKDIR}/WEATHER
[ -z ${TESTDATA_ISCE} ] && export TESTDATA_ISCE=${WORKDIR}/TESTDATA_ISCE

############ FOR PROCESSING  #########
python_version=$(echo "python3.$(${RSMASINSAR_HOME}/tools/miniconda3/bin/python --version | cut -d. -f2)")        # e.g. python3.10
export SSARAHOME=${RSMASINSAR_HOME}/tools/SSARA
export ISCE_HOME=${RSMASINSAR_HOME}/tools/miniconda3/lib/$python_version/site-packages/isce
export ISCE_STACK=${RSMASINSAR_HOME}/tools/miniconda3/share/isce2
export MINTPY_HOME=${RSMASINSAR_HOME}/tools/MintPy
export MIAPLPY_HOME=${RSMASINSAR_HOME}/tools/MiaplPy
export MIMTPY_HOME=${RSMASINSAR_HOME}/tools/MimtPy
export PLOTDATA_HOME=${RSMASINSAR_HOME}/tools/PlotData
export GBIS_HOME=${RSMASINSAR_HOME}/tools/GBIS
export JOBDIR=${WORKDIR}/JOBS
export OPERATIONS=${WORKDIR}/OPERATIONS

############ FOR MODELLING  ###########
export MODELDATA=${WORKDIR}/MODELDATA
export GEODMOD_INFILES=${WORKDIR}/infiles/${USER_PREFERRED}/GEODMOD_INFILES
export GEODMOD_HOME=${RSMASINSAR_HOME}/tools/geodmod
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
export DASK_CONFIG=${MINTPY_HOME}/src/mintpy/defaults/

############## LAUNCHER ##############
export LAUNCHER_DIR=${RSMASINSAR_HOME}/tools/launcher
export LAUNCHER_PLUGIN_DIR=${LAUNCHER_DIR}/plugins
export LAUNCHER_RMI=${JOBSCHEDULER}
export LAUNCHER_SCHED=block   ## could be one of: dynamic, interleaved, block

##############  PYTHON  ##############
export PYTHON3DIR=${RSMASINSAR_HOME}/tools/miniconda3
export CONDA_ENVS_PATH=${PYTHON3DIR}/envs
export CONDA_PREFIX=${PYTHON3DIR}
export PROJ_LIB=${PYTHON3DIR}/share/proj
export GDAL_DATA=${PYTHON3DIR}/share/gdal

export PYTHONPATH=${PYTHONPATH-""}
export PYTHONPATH=${PYTHONPATH}:${MIMTPY_HOME}
export PYTHONPATH=${PYTHONPATH}:${ISCE_HOME}:${ISCE_HOME}/components
export PYTHONPATH=${PYTHONPATH}:${ISCE_STACK}
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/tools/PyAPS
export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/tools/PySolid
export PYTHONPATH=${PYTHONPATH}:${PLOTDATA_HOME}/src/cli
export PYTHONPATH=${PYTHONPATH}:${PLOTDATA_HOME}/src
#export PYTHONPATH=${PYTHONPATH}:${RSMASINSAR_HOME}/tools      # needed for mimt. Need to talk to Sara on how to do this smarter
#export MPLBACKEND='Agg'

######### Ignore warnings ############
#export PYTHONWARNINGS="ignore:Unverified HTTPS request"   (FA 6/20: Deprecation and VisibleDepreciation dis not work) 
export PYTHONWARNINGS="ignore"

#####################################
############  PATH  #################
#####################################
export PATH=${PATH}:${SSARAHOME}
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar/cli
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar
export PATH=${PATH}:${RSMASINSAR_HOME}/minsar/utils
export PATH=${PATH}:${MINTPY_HOME}/src/mintpy/cli
export PATH=${PATH}:${MIAPLPY_HOME}/src/miaplpy
export PATH=${PATH}:${PLOTDATA_HOME}/src/cli
export PATH=${PATH}:${RSMASINSAR_HOME}/tools/MimtPy
export PATH=${PATH}:${RSMASINSAR_HOME}/tools/snaphu/bin
export PATH=${PATH}:${RSMASINSAR_HOME}/tools/insarmaps_scripts
export PATH=${PATH}:${RSMASINSAR_HOME}/tools/autoencoder
export PATH=${PATH}:${PROJ_LIB}
export PATH=${PATH}:${DASK_CONFIG}
export PATH=${PATH}:${RSMASINSAR_HOME}/tools/S4I/viewer4falk
export PATH=${ISCE_HOME}/applications:${ISCE_HOME}/bin:${ISCE_STACK}:${PATH}
export PATH=${PYTHON3DIR}/bin:${PATH}

[ -n ${MATLAB_HOME} ] && export PATH=${PATH}:${MATLAB_HOME}/bin

#export LD_LIBRARY_PATH=${LD_LIBRARY_PATH-""}
#export LD_LIBRARY_PATH=${PYTHON3DIR}/lib
unset LD_LIBRARY_PATH
export LD_RUN_PATH=${PYTHON3DIR}/lib

########## bash functions #########
source $RSMASINSAR_HOME/minsar/utils/minsar_functions.bash

if [ -n "${prompt}" ]
then
    echo "RSMASINSAR_HOME:" ${RSMASINSAR_HOME}
    echo "PYTHON3DIR:     " ${PYTHON3DIR}
    echo "SSARAHOME:      " ${SSARAHOME}
fi
