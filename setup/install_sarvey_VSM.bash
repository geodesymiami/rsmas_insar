#!/usr/bin/env bash
set -eo pipefail

### Source the environment  #################
export RSMASINSAR_HOME=$PWD
source setup/platforms_defaults.bash;
source setup/environment.bash;

#git clone git@github.com:EliTras/VSM.git tools/VSM
#git clone git@github.com:luhipi/sarvey tools/sarvey

### install VSM in new conda environment  #########################
#tools/miniforge3/bin/conda create --name vsm pip -y
#tools/miniforge3/envs/vsm/bin/pip install -r tools/VSM/VSM/requirements.txt

### Install GDAL into sarvey environment #########################
tools/miniforge3/bin/conda create --name sarvey pip -y
#tools/miniforge3/bin/conda install -n sarvey -c conda-forge gdal -y
conda env update --name sarvey -f tools/sarvey/environment.yml
tools/miniforge3/envs/sarvey/bin/pip install -e tools/sarvey
tools/miniforge3/envs/sarvey/bin/pip install -e tools/MiaplPy

###  Reduce miniforge3 directory size #################
rm -rf tools/miniforge3/pkgs

echo "Installation DONE"
