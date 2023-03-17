#! /bin/bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                                     \n\
  Examples:                                                                                    \n\
      recalc_dem_error.bash [n_exclude]      default: 10                                                \n\
      recalc_dem_error.bash 5
                                                                                               \n\
      recalculates demError after removing the most noisy acquisitions (calculated using  phaseVelocity=yes)  \n\
                                                                                            \n\
      it first calculates the timeseriesResidual after demError removal. For that we have to   \n\
      set 'mintpy.timeFunc.polynomial = 2' (here is is assumed that demError was calculated with second order polynominal)   \n\
      then it runs timeseries_rms.py to calculate the RMS . The n_exclude most noisy dates are removed  \n\
      and theh demError is recalculated  \n\
      as a reminderm demError is calculated using dem_error.py timeseries.h5 -t smallbaseline.cfg -o timeseries_demErr.h5 --update -g inputs/geometryRadar.h5  \n\
                                                                                            \n
     "
    printf "$helptext"
    exit 0;
fi

#################################
args=( "$@" )    # copy of command line arguments
#################################

n_exclude=$1
if [ ! $# -eq 1 ]; then
   n_exclude=10
fi

files=$(ls *timeseriesResidual*)
echo removing: $files
rm *timeseriesResidual*
cp smallbaselineApp.cfg tmp_smallbaseline.cfg
# modify smallbaselineApp.cfg to create timeseriesResidual.h5 (and velocity.h5) for PhaseVelocity-calculated demError
sed -i "s|mintpy.timeFunc.polynomial = auto|mintpy.timeFunc.polynomial = 2|g" tmp_smallbaselineApp.cfg
cmd="timeseries2velocity.py --save-res timeseries_demErr.h5 -t tmp_smallbaselineApp.cfg"
echo "Running.... $cmd"
echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
$cmd

# create timeseriesResidual.h5 (and velocity.h5) for PhaseVelocity
cmd="timeseries_rms.py timeseriesResidual.h5 -t tmp_smallbaselineApp.cfg"
echo "Running.... $cmd"
echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
$cmd

# determine dates with strongest troposphere (highest RMS) which will be excluded
# recalculate demError without bnoisy dates
tmp1=$(sort -k 2,2 -rn rms_timeseriesResidual_ramp.txt | head -$n_exclude | awk  '{printf "%s,", $1}')
tmp2=$(echo ${tmp1::-1})
sed -i "s|mintpy.topographicResidual.excludeDate       = auto|mintpy.topographicResidual.excludeDate = ${tmp2}|g" tmp_smallbaseline.cfg
cmd="dem_error.py timeseries.h5 -t tmp_smallbaseline.cfg -o timeseries_demErr.h5 --update -g inputs/geometryRadar.h5 --outfile timeseries_demErr_exclude${n_exclude}.h5"
echo "Running.... $cmd"
echo "$(date +"%Y%m%d:%H-%M") * $cmd" | tee -a log
$cmd
mv demErr.h5 demErr_exclude${n_exclude}.h5

