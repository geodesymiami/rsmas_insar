###############################################
echo "sourcing $PWD/setup/setup_miami.bash ..."
[ -z ${USER_PREFERRED} ] && export USER_PREFERRED=$USER
[ -z ${NOTIFICATIONEMAIL} ] && export NOTIFICATIONEMAIL=${USER_PREFERRED}\@rsmas.miami.edu
[ -z ${RSMASINSAR_HOME} ] && export RSMASINSAR_HOME=$PWD

######  required variables ##################
# WORKDIR, SCRATCHDIR, JOBSCHEDULER, QUEUENAME
# customizable variables: SENTINEL_ORBITS, WEATHER_DIR, TESTDATA_ISCE, DOWNLOADHOST, PROJECTNAME

export WORKDIR=~/insarlab
export SCRATCHDIR=/projects/scratch/insarlab/${USER_PREFERRED}
export JOBSCHEDULER=LSF
export QUEUENAME=general

#############################################
########### known platforms ##################
#############################################

########### pegasus  #########################
if [[ (${HOST} == login3) || (${HOST} == login4) || (${HOST} =~ vis) ]]  
then
  export JOBSCHEDULER=LSF
  export QUEUENAME=general
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/projects/scratch/insarlab/${USER_PREFERRED}
  export TESTDATA_ISCE=/nethome/dwg11/insarlab/TESTDATA_ISCE
  export DOWNLOADHOST=visx.ccs.miami.edu
  export SENTINEL_ORBITS=/nethome/swdowinski/S1orbits
  export SENTINEL_AUX=/nethome/swdowinski/S1aux
  export WEATHER_DIR=/nethome/dwg11/insarlab/WEATHER
fi
###############################################
if [[ ${HOST} == eos ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/scratch/insarlab/${USER_PREFERRED}
fi
###############################################
if [[ ${HOST} == centos7.bogon105.com ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data/rsmasdata/famelung/SCRATCHDIR
  export TESTDATA_ISCE=/data/rsmasdata/famelung/TESTDATA_ISCE
fi
###############################################
if [[ ${HOST} == pgftsunami ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data1/Projects/insar/data
  export TESTDATA_ISCE=/data1/Projects/insar/data/TESTDATA_ISCE
fi
###############################################
if [[ ${HOST} =~ glic ]]
then
  export JOBSCHEDULER=LSF
  export QUEUENAME=serial
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data/scratch/${USER}
  export TESTDATA_ISCE=/data/Projects/insar/data/TESTDATA_ISCE
fi
###############################################
if [[ ${HOST} =~ mefe ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/misc/zs4
  export TESTDATA_ISCE=/misc/zs4/TESTDATA_ISCE
fi

###############################################
if [[ ${HOST} == *local ]]
then
  export WORKDIR=/Users/${USER}/Documents/insarlab
  export SCRATCHDIR=/Users/${USER}/Documents/insarlab/scratch
fi

###############################################
if [[ ${HOSTNAME} == *stampede* ]]
then
  export JOBSCHEDULER=SLURM
  export QUEUENAME=normal
  export PROJECTNAME=TG-EAR180014
  export WORKDIR=${WORK}/insarlab
  export SCRATCHDIR=${SCRATCH}
fi




