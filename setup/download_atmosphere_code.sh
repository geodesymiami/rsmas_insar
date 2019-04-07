#!/bin/csh -v
# downloads 3rdparty code for atmospheric correction

mkdir -p ../3rdparty; 
cd ../3rdparty;

#### PYAPS ####
echo "downloading PyAPS ...  "
git clone https://github.com/yunjunz/PyAPS.git

