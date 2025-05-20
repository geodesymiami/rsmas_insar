#!/usr/bin/env bash
######### copy credentials to right place ##############

# Determine the script's directory
SCRIPT_DIR=$(dirname "$(realpath "${BASH_SOURCE[0]}")")
echo SCRIPT_DIR "$SCRIPT_DIR"

# for ssara
SSARA_FILE="$SCRIPT_DIR/../tools/SSARA/password_config.py"
characterCount=$(wc -m < "$SSARA_FILE" | xargs)

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
if [[ ! -f ~/.cdsapirc ]]; then
  echo "Copying default cdsapirc for ECMWF download with PyAPS into HOME directory"
  cp ~/accounts/cdsapirc ~/.cdsapirc
else
  echo "File  ~/.cdsapirc exists already - kept unchanged"
fi
