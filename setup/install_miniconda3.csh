#!/bin/csh -v

module purge all
rm -r ../3rdparty/miniconda3
mkdir -p downloads; 
cd downloads;

echo "downloading miniconda ..."
wget http://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh --no-check-certificate #; if ($? != 0) exit; 
chmod 755 Miniconda3-latest-Linux-x86_64.sh
cd ..
downloads/Miniconda3-latest-Linux-x86_64.sh -b -p ../3rdparty/miniconda3
cp condarc ../3rdparty/miniconda3/.condarc

# possibly needed in China
#miniconda3/bin/conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
#miniconda3/bin/conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
#miniconda3/bin/conda config --set show_channel_urls yes

../3rdparty/miniconda3/bin/conda install --yes --file requirements_isce22.txt
cd ../3rdparty/miniconda3/bin
ln -s cython cython3
cd ../lib
unlink libuuid.so
unlink libuuid.so.1
ln -s /lib64/libuuid.so.1.3.0 libuuid.so.1
ln -s /lib64/libuuid.so.1.3.0 libuuid.so
cd ../bin

./pip install --upgrade pip
./pip install opencv-python

#setenv CONDA_ENVS_PATH ${PARENTDIR}/3rdparty/miniconda3/envs/
#conda env create -f ${PARENTDIR}/requirements_isce22.txt --name isce22
