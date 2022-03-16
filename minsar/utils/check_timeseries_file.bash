#! /bin/bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                                  \n\
  Examples:                                                                                 \n\
      check_timeseries_file.bash                                                            \n\
                                                                                            \n\
      removes incomplete timeseries.h5 file (created by interrupting ifgram_inversion.py)   \n\
                                                                                            \n\
      removes timeseries.* if only one timerseries* file exist. (the assumption is that     \n\
      only one file exist because the previous job got interrupted                          \n\
      remove *demErr* if rms_timeseriesResidual_ramp.txt DOES NOT exist                     \n
     "
    printf "$helptext"
    exit 0;
fi

dir="mintpy"

#################################

args=( "$@" )    # copy of command line arguments

dir=mintpy

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
        --dir)
            dir="$2"
            shift # past argument
            shift # past value
            ;;
esac
done

#echo Checking: $dir/timeseries.h5

test -f $dir/timeseries.h5 || exit 0

[[ $(ls $dir/timeseries* | wc -l) -eq 1 ]] && rm -f $dir/timeseries*
! test -f $dir/rms_timeseriesResidual_ramp.txt  &&  rm -f $dir/*demErr*

