#!/bin/csh 
######### copy credentials to right place ##############

# for ssara 
set characterCount=`wc -m ../3rdparty/SSARA/password_config.py`

if (  $characterCount[1] == 75) then
      echo "Use default password_config.py for SSARA (because existing file lacks passwords)"
      echo "Copying password_config.py into ../3rdparty/SSARA"
      cp ~/accounts/password_config.py ../3rdparty/SSARA
   else
      echo File password_config.py not empty - kept unchanged
endif

echo "Copying password_config.py into ../minsar/utils/ssara_ASF"
cp ~/accounts/password_config.py ../minsar/utils/ssara_ASF

# for dem.py 
if (! -f ~/.netrc) then
  echo "copying .netrc file for DEM data download into ~/.netrc"
  cp ~/accounts/netrc ~/.netrc
endif

# for pyaps 
if (! -f 3rdparty/PyAPS/pyaps3/model.cfg) then
      echo Copying default model.cfg for ECMWF download with PyAPS into ../3rdparty/PyAPS/pyaps3
      cp ~/accounts/model.cfg ../3rdparty/PyAPS/pyaps3
   else
      echo File model.cfg exists already - kept unchanged
endif

