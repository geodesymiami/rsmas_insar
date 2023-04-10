# Installation guide
How to install RSMAS InSAR code.

* Set `$RSMASINSAR_HOME` in your [.bashrc](https://github.com/falkamelung/rsmas_insar/blob/master/docs/bashrc_contents.md) 
and [.bash_profile](./bash_profile.md).  You may want to set your variables in an external file as we do in Miami (see [example](https://gist.github.com/falkamelung/f1281c38e301a3296ab0483f946cac4b)).

* Create an ~/accounts directory with your data download credentials (for contents see [here](./accounts_info.md)). If you have access to the RSMAS accounts repo clone it into your /home or `$WORK2` directory 

```
git clone https://github.com/geodesymiami/accounts.git ~/accounts ;
```

* Go to the area where you want to install the code:

```
cd $WORK2/code
```

* Install the code using the commands below (you need a reasonable recent git version). 

```
bash
module purge
export PATH=/bin
git clone https://github.com/geodesymiami/rsmas_insar.git ;
cd rsmas_insar

git clone https://github.com/insarlab/MintPy.git tools/MintPy ;
git clone https://github.com/isce-framework/isce2.git tools/isce2
git clone https://github.com/insarlab/MiaplPy.git tools/MiaplPy 
git clone https://github.com/geodesymiami/geodmod.git tools/geodmod ;
git clone https://github.com/geodesymiami/insarmaps_scripts.git tools/insarmaps_scripts ;
git clone https://github.com/geodesymiami/SSARA.git tools/SSARA ;
git clone https://github.com/geodesymiami/MimtPy.git tools/MimtPy ;
git clone https://github.com/TACC/launcher.git tools/launcher ;
########  Done with critical code.  ########

############################################
### Install your python environment: #######
cd setup
rm -rf ../tools/miniconda3
#miniconda_version=Miniconda3-latest-MacOSX-x86_64.sh    # python 3.8  - does not seem to work
miniconda_version=Miniconda3-latest-Linux-x86_64.sh
miniconda_version=Miniconda3-py38_4.9.2-Linux-x86_64.sh
wget http://repo.continuum.io/miniconda/$miniconda_version --no-check-certificate -O $miniconda_version #; if ($? != 0) exit; 
chmod 755 $miniconda_version
bash ./$miniconda_version -b -p ../tools/miniconda3
../tools/miniconda3/bin/conda config --add channels conda-forge
../tools/miniconda3/bin/conda install mamba --yes
../tools/miniconda3/bin/conda  update mamba --yes
../tools/miniconda3/bin/conda install --yes --file ../tools/MintPy/requirements.txt
sed -i "s|isce2|#isce2|g" ../tools/MiaplPy/docs/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/MiaplPy/docs/requirements.txt

../tools/miniconda3/bin/mamba install isce2 -c conda-forge --yes 
../tools/miniconda3/bin/conda install --yes --file ../minsar/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/insarmaps_scripts/docs/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/MimtPy/mimtpy/docs/requirements.txt 

############################################
### Compile MiaplPy and install SNAPHU #####
export MIAPLPY_HOME="${PWD%/*}/tools/MiaplPy"
cd $MIAPLPY_HOME/miaplpy/lib;
 ../../../../tools/miniconda3/bin/python  setup.py
 
cd $MIAPLPY_HOME;
wget --no-check-certificate  https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.4.tar.gz
tar -xvf snaphu-v2.0.4.tar.gz
mv snaphu-v2.0.4 snaphu;
rm snaphu-v2.0.4.tar.gz;
sed -i 's/\/usr\/local/$(MIAPLPY_HOME)\/snaphu/g' snaphu/src/Makefile
cd snaphu/src; make

############################################
### Adding ISCE fixes and copying latest ISCE version into miniconda directory ###
cd ../../../../setup/
cp -p ../minsar/additions/isce/logging.conf ../tools/miniconda3/lib/python3.?/site-packages/isce/defaults/logging/logging.conf
cp -p ../minsar/additions/isce2/topsStack/FilterAndCoherence.py ../tools/isce2/contrib/stack/topsStack
cp -p ../minsar/additions/isce2/stripmapStack/prepRawCSK.py ../tools/isce2/contrib/stack/stripmapStack
cp -p ../minsar/additions/isce2/stripmapStack/unpackFrame_TSX.py ../tools/isce2/contrib/stack/stripmapStack
cp -p ../minsar/additions/isce2/topo.py ../tools/isce2/contrib/stack/stripmapStack    #(uses method isce instead of gdal)

cp -p ../minsar/additions/isce2/VRTManager.py ../tools/isce2/contrib/stack/topsStack                          # 1/23 np.int issue
cp -p ../minsar/additions/isce2/TOPSSwathSLCProduct.py ../tools/isce2/components/isceobj/Sensor/TOPS          # 1/23 np.int issue
cp -p ../minsar/additions/isce2/Sentinel1.py  ../tools/isce2/components/isceobj/Sensor/TOPS                   # 2/23 np.int issue
cp -p ../minsar/additions/isce2/stripmapStack/cropFrame.py ../tools/isce2/contrib/stack/stripmapStack         # 1/23 np.int issue
cp ../tools/isce2/components/isceobj/Sensor/TOPS/TOPSSwathSLCProduct.py ../tools/miniconda3/lib/python3.?/site-packages/isce/components/isceobj/Sensor/TOPS
cp ../minsar/additions/isce2/Sentinel1.py  ../tools/miniconda3/lib/python3.?/site-packages/isce/components/isceobj/Sensor/TOPS/    # 4/23 np.int issue, not clear why need to copy into python3.?/site-packages directory
cp -r ../tools/isce2/contrib/stack/* ../tools/miniconda3/share/isce2 


cp -r ../tools/isce2/components/isceobj/Sensor/TOPS ../tools/miniconda3/share/isce2 

cp -p ../minsar/additions/mintpy/save_hdfeos5.py ../tools/MintPy/src/mintpy/
cp -p ../minsar/additions/mintpy/cli/save_hdfeos5.py ../tools/MintPy/src/mintpy/cli/
cp -p ../minsar/additions/miaplpy/find_short_baselines.py  ../tools/MiaplPy/miaplpy/
cp -p ../minsar/additions/miaplpy/prep_slc_isce.py  ../tools/MiaplPy/miaplpy/

############################################
### Source the environment and create aux directories. Install credential files for data download: ###
./install_credential_files.bash;

source ~/accounts/platforms_defaults.bash;
export RSMASINSAR_HOME=$(dirname $PWD)
source environment.bash;
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX $OPERATIONS/LOGS;

############################################
### create your `miniconda3.tar` and `minsar.tar`  (removing `pkgs` saves space, could cause problems with environments) (needed for `install_code_to_tmp.bash) ###
tar cf ../minsar.tar ../tools/launcher ../minsar ../setup ../tools/MintPy/src ../tools/MimtPy/mimtpy ../tools/MiaplPy/miaplpy ../tools/MiaplPy/snaphu/bin ../tools/insarmaps_scripts ../tools/isce2/contrib/stack
rm -rf ../tools/miniconda3/pkgs
tar cf ../tools/miniconda3.tar -C ../tools/ miniconda3 
echo "Installation DONE"
```

### #Orbits and aux files
This has created directories for the orbits for Sentinel-1 (`$SENTINEL_ORBITS`), which The can be downloaded using `dloadOrbits.py`. The IPF calibration files (`SENTINEL_AUX`) are downloaded from: https://qc.sentinel1.eo.esa.int/aux_cal/ .

### #Keep copys in the case your `$SCRATCHDIR` gets purged
The `$SENTINEL_ORBITS` and `miniconda3.tar` are located on `$SCRATCHDIR` which  gets purged every couple of weeks. `minsarApp.bash uses `$RSMASINSAR_HOME/tools/miniconda3.tar` and  `$WORKDIR/S1orbits.tar`  if files have been purged`.

### Next steps and possible problems
* To check your installation, run the testdata as explained [here](https://github.com/geodesymiami/rsmas_insar/wiki/Testing-the-code). You need to have the testdata in your `$TESTDATA_ISCE` directory.

```
ls  $TESTDATA_ISCE
unittestGalapagosSenDT128  unittestKrakatoaSenAT171

ll $TESTDATA_ISCE/unittestGalapagosSenDT128/SLC/
total 17528848
-rw-rw--w-+ 1 famelung insarlab        782 Jan 17 17:10 files.csv
-rw-rw--w-+ 1 famelung insarlab        644 Jan 17 17:13 log
-rw-rw--w-+ 1 famelung insarlab        777 Jan 17 17:10 new_files.csv
-rw-rw-rw-+ 1 famelung insarlab 2382498740 Jan 17 17:08 S1A_IW_SLC__1SSV_20160605T114943_20160605T115018_011575_011AEF_98EA.zip
-rw-rw-rw-+ 1 famelung insarlab 2596328889 Jan 17 17:10 S1A_IW_SLC__1SSV_20160629T114944_20160629T115019_011925_0125EE_41E2.zip
-rw-rw-rw-+ 1 famelung insarlab 2538509057 Jan 17 17:08 S1A_IW_SLC__1SSV_20160711T114945_20160711T115020_012100_012BB7_AD1C.zip
-rw-rw-rw-+ 1 famelung insarlab 2658073568 Jan 17 17:08 S1A_IW_SLC__1SSV_20160723T114945_20160723T115021_012275_01315B_4BF1.zip
-rw-rw-rw-+ 1 famelung insarlab 2619635729 Jan 17 17:09 S1A_IW_SLC__1SSV_20160804T114946_20160804T115022_012450_01372F_C4E2.zip
-rw-rw-rw-+ 1 famelung insarlab 2576452600 Jan 17 17:09 S1A_IW_SLC__1SSV_20160816T114947_20160816T115022_012625_013CEA_AD2C.zip
-rw-rw-rw-+ 1 famelung insarlab 2578011015 Jan 17 17:09 S1A_IW_SLC__1SSV_20160828T114947_20160828T115023_012800_0142DE_D868.zip
drwxrws-w-+ 2 famelung insarlab       4096 Jan 17 16:58 test
//login4/nethome/dwg11/insarlab/TESTDATA_ISCE[59]
```
* For possible problems, check [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/installation_issues.md).


### *. [Set-up in Miami](./set_up_miami.md) ###

