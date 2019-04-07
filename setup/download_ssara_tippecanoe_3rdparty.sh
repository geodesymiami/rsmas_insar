#!/bin/csh -v
# downloads all necessary 3rdparty codes

mkdir -p ../3rdparty; 
cd ../3rdparty;

#### SSARA ######;
echo "downloading ssara ...  "
git clone https://github.com/bakerunavco/SSARA.git

#### INSARMAPS ####
echo "downloading tippecanoe ...  "
git clone https://github.com/mapbox/tippecanoe.git;    
git clone https://github.com/DenisCarriere/geocoder;

### copy code to be compiled ###
#cp -r /nethome/famelung/development/rsmas_insar/3rdparty_for_installation_DO_NOT_REMOVE/* .;               

