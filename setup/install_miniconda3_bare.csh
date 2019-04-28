#!/bin/csh -v

module purge all
rm -r ../3rdparty/miniconda3
mkdir -p downloads; 
cd downloads;

echo "downloading miniconda ..."
set miniconda_version=Miniconda3-4.5.12-Linux-x86_64.sh
wget http://repo.continuum.io/miniconda/$miniconda_version --no-check-certificate #; if ($? != 0) exit; 
chmod 755 $miniconda_version
cd ..
downloads/$miniconda_version -b -p ../3rdparty/miniconda3
cp condarc ../3rdparty/miniconda3/.condarc
