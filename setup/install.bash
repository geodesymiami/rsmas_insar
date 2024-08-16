#!/usr/bin/env bash
set -eo pipefail

git clone git@github.com:insarlab/MintPy.git tools/MintPy ;
git clone git@github.com:insarlab/MiaplPy.git tools/MiaplPy ;
git clone git@github.com:geodesymiami/insarmaps_scripts.git tools/insarmaps_scripts ;
git clone git@github.com:isce-framework/isce2.git tools/isce2
git clone git@github.com:geodesymiami/MimtPy.git tools/MimtPy ;
git clone git@github.com:geodesymiami/geodmod.git tools/geodmod ;
git clone git@github.com:geodesymiami/SSARA.git tools/SSARA ;
git clone git@github.com:TACC/launcher.git tools/launcher ;
git clone git@github.com:geodesymiami/PlotData tools/PlotData
git clone git@github.com:geodesymiami/precip tools/Precip
git clone git@github.com:geodesymiami/precip_web tools/Precip_web
git clone git@github.com:geodesymiami/precip_cron tools/Precip_cron
git clone git@github.com:scottstanie/sardem tools/sardem

### Install python #########################
rm -rf tools/miniconda3
miniconda_version=Miniconda3-latest-Linux-x86_64.sh
if [ "$(uname)" == "Darwin" ]; then miniconda_version=Miniconda3-latest-MacOSX-arm64.sh ; fi
wget http://repo.continuum.io/miniconda/${miniconda_version} --no-check-certificate -P setup
chmod 755 setup/${miniconda_version}
bash setup/${miniconda_version} -b -p tools/miniconda3

### Source the environment  #################
export RSMASINSAR_HOME=$(dirname $PWD)
source setup/platforms_defaults.bash;
source setup/environment.bash;

### Install c-dependencies (isce fails on Mac) ###
conda install conda-libmamba-solver --yes
conda install python=3.10  --file minsar/environment.yml --solver libmamba --yes -c conda-forge                     # first install c-code
conda install --file tools/insarmaps_scripts/environment.yml --solver libmamba --yes  -c conda-forge
conda install isce2 -c conda-forge  --solver libmamba --yes

### Install python code and dependencies  ########
pip install -e tools/MintPy
pip install -e tools/MiaplPy
pip install -r minsar/requirements.txt
pip install -r tools/insarmaps_scripts/requirements.txt
pip install -r tools/PlotData/requirements.txt
pip install -r tools/Precip/requirements.txt
pip install -r tools/sardem/requirements.txt
pip install -e tools/sardem

###  Reduce miniconda3 directory size #################
rm -rf tools/miniconda3/pkgs

### Install credential files ###############
setup/install_credential_files.bash;

###  Install SNAPHU #################
wget --no-check-certificate  https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.5.tar.gz  -P tools
tar -xvf tools/snaphu-v2.0.5.tar.gz -C tools
mv tools/snaphu-v2.0.5 tools/snaphu
sed -i '' 's|/usr/local|$(PWD)/snaphu|g' tools/snaphu/src/Makefile
cc=tools/miniconda3/bin/cc
make -C tools/snaphu/src
# cd  ../tools/snaphu/src; make
# cd ../../../setup/

### Adding not-commited MintPy fixes
cp -p minsar/additions/mintpy/save_hdfeos5.py tools/MintPy/src/mintpy/
cp -p minsar/additions/mintpy/cli/save_hdfeos5.py tools/MintPy/src/mintpy/cli/

### Adding MiaplPy fix which Sara says she is going to fix
cp -p minsar/additions/miaplpy/prep_slc_isce.py tools/MiaplPy/src/miaplpy

### Adding ISCE fixes and copying checked-out ISCE version (the latest) into miniconda directory ###
cp -p minsar/additions/isce/logging.conf tools/miniconda3/lib/python3.?/site-packages/isce/defaults/logging/logging.conf
cp -p minsar/additions/isce2/topsStack/FilterAndCoherence.py tools/isce2/contrib/stack/topsStack
cp -p minsar/additions/isce2/stripmapStack/prepRawCSK.py tools/isce2/contrib/stack/stripmapStack
cp -p minsar/additions/isce2/stripmapStack/unpackFrame_TSX.py tools/isce2/contrib/stack/stripmapStack
cp -p minsar/additions/isce2/DemStitcher.py tools/isce2/contrib/demUtils/demstitcher

### Copying ISCE fixes into miniconda directory ###
cp -r tools/isce2/contrib/stack/* tools/miniconda3/share/isce2
cp -r tools/isce2/components/isceobj/Sensor/TOPS tools/miniconda3/share/isce2
cp tools/isce2/components/isceobj/Sensor/TOPS/TOPSSwathSLCProduct.py tools/miniconda3/lib/python3.?/site-packages/isce/components/isceobj/Sensor/TOPS
cp tools/isce2/contrib/demUtils/demstitcher/DemStitcher.py  tools/miniconda3/lib/python3.??/site-packages/isce/components/contrib/demUtils

### Create orbits and aux directories
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX $OPERATIONS/LOGS;

echo "Installation DONE"
