#!/usr/bin/env bash
set -eo pipefail

### Source the environment  #################
export RSMASINSAR_HOME=$PWD
source setup/platforms_defaults.bash;
source setup/environment.bash;

git clone git@github.com:EliTras/VSM.git tools/VSM
git clone git@github.com:luhipi/sarvey tools/sarvey

### Install GDAL into sarvey environment #########################
conda create --name sarvey python=3.10 pip -y

#conda install -n sarvey -c conda-forge gdal -y
#conda env update --name sarvey -f tools/sarvey/environment.yml   #FA: elimintaed because OOM errors
#conda install -n sarvey -c conda-forge numpy scipy matplotlib h5py pyproj -y

# FA 5/2025: shoupd install whatever possible with pip, e.g. pip install PySide6
conda install -n sarvey -c conda-forge setuptools cython pyproj h5py numpy scipy matplotlib numba mintpy shapely geopandas gstools pydantic=1.10.* json5 overpy PySide6 -y
source tools/miniforge3/etc/profile.d/conda.sh
conda activate sarvey
pip install -e tools/MiaplPy
pip install -e tools/sarvey

###  Reduce miniforge3 directory size #################
rm -rf tools/miniforge3/pkgs

echo "Installation DONE"
