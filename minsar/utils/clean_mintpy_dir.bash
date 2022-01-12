#! /bin/bash

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                                                     \n\
  Examples:                                                                    \n\
      clean_mintpy_dir.bash                                                    \n\
                                                                               \n\
   clean mintpy directory for processing:                                      \n\
      remove timeseries.* if only one timerseries* file exist                  \n\
      remove *demErr* if rms_timeseriesResidual_ramp.txt DOES NOT exist        \n
     "
    printf "$helptext"
    exit 0;
fi

test -f mintpy/timeseries.h5 || exit 0

[[ $(ls mintpy/timeseries* | wc -l) -eq 1 ]] && rm -f mintpy/timeseries*
! test -f mintpy/rms_timeseriesResidual_ramp.txt  &&  rm -f mintpy/*demErr*

