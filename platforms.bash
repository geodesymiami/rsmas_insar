###############################################
echo "sourcing $PWD/platforms.bash ..."

if [[ (${HOST} == login3) || (${HOST} == login4) || (${HOST} =~ vis) ]]  
then
  export JOBSCHEDULER=LSF
  export QUEUENAME=general
  export SCRATCHDIR=/projects/scratch/insarlab/${USER}
  export TESTDATA_ISCE=/nethome/dwg11/insarlab/TESTDATA_ISCE
  export DOWNLOADHOST=visx.ccs.miami.edu
  export SENTINEL_ORBITS=/nethome/swdowinski/S1orbits
  export SENTINEL_AUX=/nethome/swdowinski/S1aux
  export WEATHER_DIR=/nethome/dwg11/insarlab/WEATHER
  export TESTDATADIR=visx.ccs.miami.edu:/famelung/famelung/testdata
  export MAKEDEM_BIN=/nethome/famelung/test/testq/rsmas_insar/sources/roipac/BIN/LIN
  export MATLABHOME=/share/opt/MATLAB/R2014b

  export PATH=${PATH}:${MATLABHOME}/bin:${MAKEDEM_BIN}
fi
###############################################
if [[ ${HOST} == eos ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export SCRATCHDIR=/scratch/insarlab/${USER}
fi
###############################################
if [[ ${HOST} == centos7.bogon105.com ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export SCRATCHDIR=/data/rsmasdata/famelung/SCRATCHDIR
  export TESTDATA_ISCE=/data/rsmasdata/famelung/TESTDATA_ISCE
  export SENTINEL_ORBITS=/home/famelung/insarlab/S1orbits
  export SENTINEL_AUX=/home/famelung/insarlab/S1aux
fi
###############################################
if [[ ${HOST} == pgftsunami ]]
then
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export SCRATCHDIR=/data1/Projects/insar/data
  export TESTDATA_ISCE=/data1/Projects/insar/data/TESTDATA_ISCE
fi
