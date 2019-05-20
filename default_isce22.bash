#!/usr/bin/env bash
# vim: set filetype=sh:
echo "sourcing ${PWD}/default_isce22.bash ..."
#####################################################
export PARENTDIR=${PWD}
export TERM=xterm
export VISUAL=/bin/vi
export CPL_ZIP_ENCODING=UTF-8

###### for JOB SUBMISSION ###################
export WORKDIR=~/insarlab
export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
export INT_SCR=${PARENTDIR}/sources/roipac/INT_SCR
export DOWNLOADHOST=local

############ Standard directories ###########
export JOBDIR=${WORKDIR}/JOBS
export OPERATIONS=${HOME}/insarlab/OPERATIONS
export SAMPLESDIR=${PARENTDIR}/samples
export DEMDIR=${WORKDIR}/DEMDIR
export TESTDATA_ISCE=${WORKDIR}/TESTDATA_ISCE
export TEMPLATES=${WORKDIR}/infiles/${USER}/TEMPLATES
export TE=${TEMPLATES}

export GEODMOD_WORKDIR=${WORKDIR}/MINDIR
export GEODMODHOME=${PARENTDIR}/sources/geodmod
export GEODMOD_TESTDATA=${PARENTDIR}/data/testdata/geodmod
export GEODMOD_TESTBENCH=${SCRATCHDIR}/GEODMOD_TESTBENCH

export MAKEDEMHOME=${PARENTDIR}/sources/roipac/makedem
export MAKEDEM_SCR=${MAKEDEMHOME}/SCRIPTS
export MAKEDEM_BIN=/nethome/famelung/test/testq/rsmas_insar/sources/roipac/BIN/LIN

export SENTINEL_ORBITS=${WORKDIR}/S1orbits
export SENTINEL_AUX=${WORKDIR}/S1aux
export WEATHER_DIR=${WORKDIR}/WEATHER

############ FOR PROCESSING  #########
export SSARAHOME=${PARENTDIR}/3rdparty/SSARA
export SSARA_ASF=${PARENTDIR}/sources/ssara_ASF
export ISCE_HOME=${PARENTDIR}/3rdparty/miniconda3/lib/python3.7/site-packages/isce
export RSMAS_INSAR=${PARENTDIR}
export ISCE_STACK=${PARENTDIR}/sources/isceStack/topsStack
#export ISCE_STACK=${PARENTDIR}/sources/isceStack/stripmapStack
export PYSAR_HOME=${PARENTDIR}/sources/PySAR
export SQUEESAR=${PARENTDIR}/sources/pysqsar

##############  PYTHON  ##############
export PYTHON3DIR=${PARENTDIR}/3rdparty/miniconda3
export CONDA_ENVS_PATH=${PARENTDIR}/3rdparty/miniconda3/envs
export CONDA_PREFIX=${PARENTDIR}/3rdparty/miniconda3
export PROJ_LIB=${CONDA_PREFIX}/share/proj
export GDAL_DATA=${PYTHON3DIR}/share/gdal
export DASK_CONFIG=${RSMAS_INSAR}/minsar/defaults/dask

export PYTHONPATH=${PYTHONPATH-""}
export PYTHONPATH=${PYTHONPATH}:${PYSAR_HOME}
export PYTHONPATH=${PYTHONPATH}:${INT_SCR}
export PYTHONPATH=${PYTHONPATH}:${SSARA_ASF}
export PYTHONPATH=${PYTHONPATH}:${PYTHON3DIR}/lib/python3.7/site-packages:${ISCE_HOME}:${ISCE_HOME}/components
export PYTHONPATH=${PYTHONPATH}:${SQUEESAR}
export PYTHONPATH=${PYTHONPATH}:${RSMAS_INSAR}
export PYTHONPATH=${PYTHONPATH}:${PARENTDIR}/sources/rsmas_tools
export PYTHONPATH=${PYTHONPATH}:${PARENTDIR}/3rdparty/PyAPS
export PYTHONPATH=${PYTHONPATH}:${ISCE_STACK}
export PYTHONPATH_RSMAS=${PYTHONPATH}

######### Ignore warnings ############
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

#####################################
############ Set paths ##############
#####################################
export PATH=${PATH}:${SSARAHOME}
export PATH=${PATH}:${SSARA_ASF}
export PATH=${PATH}:${SQUEESAR}
export PATH=${PATH}:${RSMAS_INSAR}/minsar:${RSMAS_INSAR}/minsar/utils
export PATH=${PATH}:${PARENTDIR}/minsar
export PATH=${PATH}:${PARENTDIR}/setup/accounts
export PATH=${PATH}:${PARENTDIR}/sources/rsmas_tools/SAR:${PARENTDIR}/sources/rsmas_tools/GPS:${PARENTDIR}/sources/rsmas_tools/notebooks
export PATH=${ISCE_HOME}/applications:${ISCE_HOME}/bin:${ISCE_STACK}:${PATH}
export PATH=${PATH}:${PYSAR_HOME}/pysar:${PYSAR_HOME}/sh
export PATH=${PYTHON3DIR}/bin:${PATH}
export PATH=${PATH}:${PROJ_LIB}
export PATH=${PATH}:${PARENTDIR}/3rdparty/tippecanoe/bin
export PATH=${PATH}:${DASK_CONFIG}

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH-""}
export LD_LIBRARY_PATH=${PYTHON3DIR}/lib
export LD_RUN_PATH=${PYTHON3DIR}/lib

if [ -n "${prompt}" ]
then
    echo "PARENTDIR:      " ${PARENTDIR}
    echo "PYTHON3DIR:     " ${PYTHON3DIR}
    echo "SSARAHOME:      " ${SSARAHOME}
fi
