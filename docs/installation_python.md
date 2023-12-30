## ... and install credential files
./install_credential_files.bash;

## Different python installations 
* install miniconda
```
#cd setup
rm -rf ../tools/miniconda3
miniconda_version=Miniconda3-latest-Linux-x86_64.sh
if [ "$(uname)" == "Darwin" ]; then miniconda_version=Miniconda3-latest-MacOSX-arm64.sh ; fi
wget http://repo.continuum.io/miniconda/$miniconda_version --no-check-certificate -O $miniconda_version #; if ($? != 0) exit; 
chmod 755 $miniconda_version
bash ./$miniconda_version -b -p ../tools/miniconda3

### Source the environment and create aux directories.
source ~/accounts/platforms_defaults.bash;
export RSMASINSAR_HOME=$(dirname $PWD)
source environment.bash;
```

```
conda install mamba --yes
mamba install isce2 -c conda-forge --yes
pip install -e ../tools/MintPy
pip install -e ../tools/MiaplPy

pip install -r ../minsar/requirements.txt
conda install --file ../minsar/environment.yml

###  Install SNAPHU #####
wget --no-check-certificate  https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.5.tar.gz
tar -xvf snaphu-v2.0.5.tar.gz
mv snaphu-v2.0.5 ../tools/snaphu
sed -i 's/\/usr\/local/$(PWD)\/snaphu/g' ../tools/snaphu/src/Makefile
cc=../../../miniconda3/bin/cc
cd  ../tools/snaphu/src; make
```

