#!/bin/csh 
######### copy credentials to right place ##############

set characterCount=`wc -m ../3rdparty/SSARA/password_config.py`

if (  $characterCount[1] == 75) then
      echo "Use default password_config.py for SSARA (because existing file lacks passwords)"
      echo "Copying password_config.py into ../3rdparty/SSARA"
      cp accounts/password_config.py ../3rdparty/SSARA
   else
      echo File password_config.py not empty - kept unchanged
endif

cp accounts/password_config.py ../sources/ssara_ASF

# for dem.py 
if (! -f ~/.netrc) then
  echo "copying .netrc file for DEM data download into ~/.netrc"
  cp accounts/netrc ~/.netrc
endif

if (! -f 3rdparty/PyAPS/pyaps/model.cfg) then
      echo Copying default model.cfg for ECMWF download with PyAPS into ../3rdparty/PyAPS/pyaps
      cp accounts/model.cfg ../3rdparty/PyAPS/pyaps
   else
      echo File model.cfg exists already - kept unchanged
endif

