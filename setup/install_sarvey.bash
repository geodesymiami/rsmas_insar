#!/usr/bin/env bash
set -eo pipefail

### Source the environment  #################
export RSMASINSAR_HOME=$PWD
source setup/platforms_defaults.bash;
source setup/environment.bash;

git clone git@github.com:luhipi/sarvey tools/sarvey

### Install GDAL into sarvey environment #########################
conda create --name sarvey python=3.10 pip -y
source tools/miniforge3/etc/profile.d/conda.sh
conda activate sarvey

conda install -c conda-forge pysolid gdal --yes
pip install -e tools/sarvey[dev]

pip install PySide6

git clone git@github.com:falkamelung/sarplotter-main.git tools/sarplotter-main
###  Reduce miniforge3 directory size #################
rm -rf tools/miniforge3/pkgs

echo ""
echo "Installation of install_sarvey.bash DONE"
echo ""

# FA 5/2025: should install whatever possible with pip, e.g. pip install PySide6
#conda install -n sarvey -c conda-forge setuptools cython pyproj h5py numpy scipy matplotlib numba mintpy shapely geopandas gstools pydantic=1.10.* json5 overpy PySide6 -y
#pip install -e tools/MiaplPy
#pip install -e tools/sarvey

