#!/usr/bin/env bash
######### copy credentials to right place ##############

# for ssara 
characterCount=`wc -m ../tools/SSARA/password_config.py`
characterCount=$(echo "${characterCount[0]%% *}")

if [[  $characterCount == 75 ]]; then
      echo "Use default password_config.py for SSARA (because existing file lacks passwords)"
      echo "Copying password_config.py into ../tools/SSARA"
      cp ~/accounts/password_config.py ../tools/SSARA
   else
      echo File password_config.py not empty - kept unchanged
fi

# for dem.py 
if [[ ! -f ~/.netrc ]]; then
  echo "copying .netrc file for DEM data download into ~/.netrc"
  cp ~/accounts/netrc ~/.netrc
fi

# for pyaps 
python_version=$(echo "python3.$(../tools/miniconda3/bin/python --version | cut -d. -f2)")
model_cfg_file=$(echo "../tools/miniconda3/lib/$python_version/site-packages/pyaps3/model.cfg")
if [[ ! -f $model_cfg_file ]]; then
      echo "Copying default model.cfg for ECMWF download with PyAPS into $(dirname $model_cfg_file)"
      cp ~/accounts/model.cfg $model_cfg_file
   else
      echo File model.cfg exists already - kept unchanged
fi

