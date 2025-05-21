#!/usr/bin/env bash
set -eo pipefail

### Source the environment  #################
export RSMASINSAR_HOME=$PWD

VSM_ENV_PATH=$(tools/miniforge3/bin/conda env list | grep "vsm " | awk '{print $NF}')
SARVEY_ENV_PATH=$(tools/miniforge3/bin/conda env list | grep "sarvey " | awk '{print $NF}')

# Check if the environment path was found
if [ -z "$VSM_ENV_PATH" ]; then
  echo "Environment 'vsm' not found."
  exit 1
fi

if [ -z "$SARVEY_ENV_PATH" ]; then
  echo "Environment 'sarvey' not found."
  exit 1
fi

source setup/platforms_defaults.bash;
source setup/environment.bash;

### Install basic code and c-dependencies (isce fails on Mac) ###
mamba install python=3.10 wget git tree numpy --yes
pip install bypy

if [[ "$(uname)" == "Darwin" ]]; then
  mamba install mintpy --yes
else
  mamba install isce2 mintpy --yes
fi

mamba install numpy pandas xarray netcdf4 packaging gmt pygmt --yes

### git clone the code   #################
git clone git@github.com:insarlab/MintPy.git tools/MintPy
git clone git@github.com:insarlab/MiaplPy.git tools/MiaplPy
git clone git@github.com:geodesymiami/insarmaps_scripts.git tools/insarmaps_scripts
git clone git@github.com:geodesymiami/insarmaps.git tools/insarmaps
git clone git@github.com:isce-framework/isce2.git tools/isce2
git clone git@github.com:geodesymiami/MimtPy.git tools/MimtPy
git clone git@github.com:geodesymiami/geodmod.git tools/geodmod
git clone git@github.com:geodesymiami/SSARA.git tools/SSARA
git clone git@github.com:TACC/launcher.git tools/launcher
git clone git@github.com:geodesymiami/PlotData tools/PlotData
git clone git@github.com:geodesymiami/PlotDataFA tools/PlotDataFA
git clone git@github.com:geodesymiami/precip tools/Precip
git clone git@github.com:geodesymiami/precip_web tools/Precip_web
git clone git@github.com:geodesymiami/precip_cron tools/Precip_cron
git clone git@github.com:scottstanie/sardem tools/sardem
git clone git@github.com:luhipi/sarvey tools/sarvey
git clone git@github.com:falkamelung/MintPy.git tools/MintPy_falk
git clone git@github.com:EliTras/VSM.git tools/VSM

mamba install python=3.10  --file minsar/environment.yml --yes -c conda-forge                     # first install c-code
mamba install --file tools/insarmaps_scripts/environment.yml -c conda-forge

### Install python code and dependencies  ########
pip install -e tools/MintPy
pip install -e tools/MiaplPy
pip install -r minsar/requirements.txt
pip install -r tools/insarmaps_scripts/requirements.txt
pip install -r tools/PlotData/requirements.txt
pip install -r tools/Precip/requirements.txt
pip install -r tools/sardem/requirements.txt
pip install -e tools/sardem

# pip install tools/VSM
$VSM_ENV_PATH/bin/pip install -r tools/VSM/VSM/requirements.txt

### Install GDAL into sarvey environment #########################
tools/miniforge3/bin/conda install -n sarvey -c conda-forge gdal -y

###  Reduce miniforge3 directory size #################
rm -rf tools/miniforge3/pkgs

### Install credential files ###############
#setup/install_credential_files.bash;

###  Install SNAPHU #################
wget --no-check-certificate  https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.5.tar.gz  -P tools
tar -xvf tools/snaphu-v2.0.5.tar.gz -C tools
perl -pi -e 's/\/usr\/local/\$(PWD)\/snaphu-v2.0.5/g' tools/snaphu-v2.0.5/src/Makefile 
cc=tools/miniforge3/bin/cc
make -C tools/snaphu-v2.0.5/src

### Adding not-commited MintPy fixes
cp -p minsar/additions/mintpy/save_hdfeos5.py tools/MintPy/src/mintpy/
cp -p minsar/additions/mintpy/cli/save_hdfeos5.py tools/MintPy/src/mintpy/cli/

### Adding MiaplPy fix which Sara says she is going to fix
cp -p minsar/additions/miaplpy/prep_slc_isce.py tools/MiaplPy/src/miaplpy

### Adding ISCE fixes and copying checked-out ISCE version (the latest) into miniforge directory ###
if [[ "$(uname)" == "Linux" ]]; then
cp -p minsar/additions/isce/logging.conf tools/miniforge3/lib/python3.?/site-packages/isce/defaults/logging/logging.conf
cp -p minsar/additions/isce2/topsStack/FilterAndCoherence.py tools/isce2/contrib/stack/topsStack
cp -p minsar/additions/isce2/stripmapStack/prepRawCSK.py tools/isce2/contrib/stack/stripmapStack
cp -p minsar/additions/isce2/stripmapStack/unpackFrame_TSX.py tools/isce2/contrib/stack/stripmapStack
cp -p minsar/additions/isce2/DemStitcher.py tools/isce2/contrib/demUtils/demstitcher


### Copying ISCE fixes into miniforge directory ###
cp -r tools/isce2/contrib/stack/* tools/miniforge3/share/isce2
cp -r tools/isce2/components/isceobj/Sensor/TOPS tools/miniforge3/share/isce2
cp tools/isce2/components/isceobj/Sensor/TOPS/TOPSSwathSLCProduct.py tools/miniforge3/lib/python3.?/site-packages/isce/components/isceobj/Sensor/TOPS
cp tools/isce2/contrib/demUtils/demstitcher/DemStitcher.py  tools/miniforge3/lib/python3.??/site-packages/isce/components/contrib/demUtils
fi

### Create orbits and aux directories
echo "mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX"
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX
ls -d $SENTINEL_ORBITS $SENTINEL_AUX

echo "Installation DONE"
