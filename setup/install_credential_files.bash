#!/usr/bin/env bash
######### copy credentials to right place ##############

# Determine the script's directory
SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
echo SCRIPT_DIR "$SCRIPT_DIR"

# for ssara
SSARA_FILE="$SCRIPT_DIR/../tools/SSARA/password_config.py"
characterCount=$(wc -m < "$SSARA_FILE")

if [[ $characterCount == 75 ]]; then
  echo "Use default password_config.py for SSARA (because existing file lacks passwords)"
  echo "Copying password_config.py into $SCRIPT_DIR/../tools/SSARA"
  cp ~/accounts/password_config.py "$SCRIPT_DIR/../tools/SSARA"
else
  echo "File password_config.py not empty - kept unchanged"
fi

# for dem.py
if [[ ! -f ~/.netrc ]]; then
  echo "copying .netrc file for DEM data download into ~/.netrc"
  cp ~/accounts/netrc ~/.netrc
fi

# for pyaps
PYTHON_VERSION=$(echo "python3.$("$SCRIPT_DIR/../tools/miniforge3/bin/python" --version | cut -d. -f2)")
MODEL_CFG_FILE="$SCRIPT_DIR/../tools/miniforge3/lib/$PYTHON_VERSION/site-packages/pyaps3/model.cfg"
if [[ ! -f $MODEL_CFG_FILE ]]; then
  echo "Copying default model.cfg for ECMWF download with PyAPS into $(dirname "$MODEL_CFG_FILE")"
  cp ~/accounts/model.cfg "$MODEL_CFG_FILE"
else
  echo "File model.cfg exists already - kept unchanged"
fi
