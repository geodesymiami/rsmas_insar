###############################################
echo "sourcing $PWD/bashfiles/platforms.bash ..."

if [[ (${HOST} == login3) || (${HOST} == login4) || (${HOST} =~ vis) ]]  
then
  export PLATFORM=pegasus
  export JOBSCHEDULER=LSF
  export QUEUENAME=general
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/projects/scratch/insarlab/${USER}
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
  export TESTDATA_ISCE=/nethome/dwg11/insarlab/TESTDATA_ISCE
  export DOWNLOADHOST=visx.ccs.miami.edu
  export SENTINEL_ORBITS=/nethome/swdowinski/S1orbits
  export SENTINEL_AUX=/nethome/swdowinski/S1aux
  export WEATHER_DIR=/nethome/dwg11/insarlab/WEATHER
  export TESTDATADIR=visx.ccs.miami.edu:/famelung/famelung/testdata
  export MAKEDEM_BIN=/nethome/famelung/test/testq/rsmas_insar/sources/roipac/BIN/LIN
  export MATLABHOME=/share/opt/MATLAB/R2018b

  export PATH=${PATH}:${MATLABHOME}/bin:${MAKEDEM_BIN}
fi
###############################################
if [[ ${HOST} == eos ]]
then
  export PLATFORM=$HOST
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/scratch/insarlab/${USER}
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
fi
###############################################
if [[ ${HOST} == centos7.bogon105.com ]]
then
  export PLATFORM=$HOST
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data/rsmasdata/famelung/SCRATCHDIR
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
  export TESTDATA_ISCE=/data/rsmasdata/famelung/TESTDATA_ISCE
  export SENTINEL_ORBITS=/home/famelung/insarlab/S1orbits
  export SENTINEL_AUX=/home/famelung/insarlab/S1aux
fi
###############################################
if [[ ${HOST} == pgftsunami ]]
then
  export PLATFORM=$HOST
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data1/Projects/insar/data
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu  
  export TESTDATA_ISCE=/data1/Projects/insar/data/TESTDATA_ISCE
fi
###############################################
if [[ ${HOST} =~ glic ]]
then
  export PLATFORM=$HOST
  export JOBSCHEDULER=LSF
  export QUEUENAME=serial
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/data/scratch/${USER}
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
  export TESTDATA_ISCE=/data/Projects/insar/data/TESTDATA_ISCE
fi
###############################################
if [[ ${HOST} =~ mefe ]]
then
  export PLATFORM=$HOST
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export PROJECTNAME =insarlab
  export SCRATCHDIR=/misc/zs4
  export WORKDIR=~/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
  export TESTDATA_ISCE=/misc/zs4/TESTDATA_ISCE
fi

###############################################
if [[ ${HOST} == *local ]]
then
  export SCRATCHDIR=/Users/${USER}/Documents/insarlab/scratch
  export WORKDIR=/Users/${USER}/Documents/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
fi

###############################################
if [[ ${HOSTNAME} == *stampede* ]]
then
  export SCRATCHDIR=${SCRATCH}
  export JOBSCHEDULER=SLURM
  export QUEUENAME=normal
  export PROJECTNAME=TG-EAR180014
  export WORKDIR=${WORK}/insarlab
  export NOTIFICATIONEMAIL=${USER}\@rsmas.miami.edu
fi




