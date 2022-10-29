# Installation guide
How to install RSMAS InSAR code.

* Set `$RSMASINSAR_HOME` in your [.bashrc](https://github.com/falkamelung/rsmas_insar/blob/master/docs/bashrc_contents.md) 
and [.bash_profile](./bash_profile.md).  You may want to set your variables in an external file as we do in Miami (see [example](https://gist.github.com/falkamelung/f1281c38e301a3296ab0483f946cac4b)).

* Create an ~/accounts directory with your data download credentials (for contents see [here](./accounts_info.md)). If you have access to the RSMAS accounts repo clone it into your /home or `$WORK2` directory 

```
git clone https://github.com/geodesymiami/accounts.git $WORK2/accounts ;
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

git clone https://github.com/insarlab/MintPy.git sources/MintPy ;
git clone https://github.com/isce-framework/isce2.git sources/isce2
git clone https://github.com/insarlab/MiaplPy.git sources/MiaplPy 
git clone https://github.com/geodesymiami/geodmod.git sources/geodmod ;
git clone https://github.com/geodesymiami/insarmaps_scripts.git sources/insarmaps_scripts ;
git clone https://github.com/geodesymiami/SSARA.git 3rdparty/SSARA ;
git clone https://github.com/geodesymiami/MimtPy.git sources/MimtPy ;
git clone https://github.com/TACC/launcher.git 3rdparty/launcher ;

########  Done with critical code.  ########
```
* #Install your python environment:
```
cd setup
rm -rf ../3rdparty/miniconda3
#miniconda_version=Miniconda3-latest-MacOSX-x86_64.sh    # python 3.8  - does not seem to work
miniconda_version=Miniconda3-latest-Linux-x86_64.sh
miniconda_version=Miniconda3-py38_4.9.2-Linux-x86_64.sh
wget http://repo.continuum.io/miniconda/$miniconda_version --no-check-certificate -O $miniconda_version #; if ($? != 0) exit; 
chmod 755 $miniconda_version
mkdir -p ../3rdparty
mkdir -p ../3rdparty
./$miniconda_version -b -p ../3rdparty/miniconda3
../3rdparty/miniconda3/bin/conda config --add channels conda-forge
../3rdparty/miniconda3/bin/conda install mamba --yes
../3rdparty/miniconda3/bin/conda install --yes --file ../sources/MintPy/requirements.txt
sed -i "s|isce2|#isce2|g" ../sources/MiaplPy/docs/requirements.txt
../3rdparty/miniconda3/bin/conda install --yes --file ../sources/MiaplPy/docs/requirements.txt

#../3rdparty/miniconda3/bin/pip install git+https://github.com/insarlab/PySolid.git
../3rdparty/miniconda3/bin/mamba install isce2 -c conda-forge --yes 
../3rdparty/miniconda3/bin/conda install --yes --file ../sources/insarmaps_scripts/docs/requirements.txt

```
* #Compile [MiaplPy](https://github.com/geodesymiami/MiaplPy) and install [SNAPHU](https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/) (if required):
```
export MIAPLPY_HOME="${PWD%/*}/sources/MiaplPy"
cd $MIAPLPY_HOME/miaplpy/lib;
python setup.py

cd $MIAPLPY_HOME;
wget --no-check-certificate  https://web.stanford.edu/group/radar/softwareandlinks/sw/snaphu/snaphu-v2.0.4.tar.gz
tar -xvf snaphu-v2.0.4.tar.gz
mv snaphu-v2.0.4 snaphu;
rm snaphu-v2.0.4.tar.gz;
sed -i 's/\/usr\/local/$(MIAPLPY_HOME)\/snaphu/g' snaphu/src/Makefile
cd snaphu/src; make

cd ../../../../setup/
```
* #Adding ISCE fixes and copying latest version into miniconda directory
```
cp -p ../minsar/additions/isce/logging.conf ../3rdparty/miniconda3/lib/python3.*/site-packages/isce/defaults/logging/logging.conf
cp -p ../minsar/additions/isce2/topsStack/FilterAndCoherence.py ../sources/isce2/contrib/stack/topsStack
cp -p ../minsar/additions/isce2/topsStack/fetchOrbit.py ../sources/isce2/contrib/stack/topsStack
cp -p ../minsar/additions/isce2/stripmapStack/prepRawCSK.py ../sources/isce2/contrib/stack/stripmapStack
cp -p ../minsar/additions/isce2/topo.py ../sources/isce2/contrib/stack/stripmapStack    #(uses method isce instead of gdal)

cp -r ../sources/isce2/contrib/stack/* ../3rdparty/miniconda3/share/isce2 

#cp -p ../minsar/additions/mintpy/plot_smallbaselineApp.sh ../sources/MintPy/mintpy/sh/
#cp -p ../minsar/additions/isce/invertMisreg.py ../sources/isce2/contrib/stack/stripmapStack
#cp -p ../minsar/additions/stackStripMap.py $ISCE_STACK/stripmapStack
#cp -p ../minsar/additions/isce/stackSentinel.py $ISCE_STACK/topsStack

```
* #create your `miniconda3.tar` and `minsar.tar`  (removing `pkgs` saves space, could cause problems with environments) (needed for `install_code_to_tmp.bash)
```
rm -rf ../3rdparty/miniconda3/pkgs
tar cf ../3rdparty/miniconda3.tar -C ../3rdparty/ miniconda3 &
tar cf ../minsar.tar ../3rdparty/launcher ../minsar ../setup ../sources/MintPy/mintpy ../sources/MimtPy/mimtpy ../sources/MiaplPy/miaplpy ../sources/MiaplPy/snaphu/bin ../sources/insarmaps_scripts ../sources/isce2/contrib/stack
```

* #Source the environment and create aux directories. Install credential files for data download:
```
./install_credential_files.csh;

source ~/accounts/platforms_defaults.bash;
export RSMASINSAR_HOME=$(dirname $PWD)
source environment.bash;
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX $OPERATIONS/LOGS;

```


### #Orbits and aux files
This has created directories for the orbits for Sentinel-1 (`$SENTINEL_ORBITS`), which The can be downloaded using `dloadOrbits.py`. The IPF calibration files (`SENTINEL_AUX`) are downloaded from: https://qc.sentinel1.eo.esa.int/aux_cal/ .

### #Keep copys in the case your `$SCRATCHDIR` gets purged
The `$SENTINEL_ORBITS` and `miniconda3.tar` are located on `$SCRATCHDIR` which  gets purged every couple of weeks. `minsarApp.bash uses `$RSMASINSAR_HOME/3rdparty/miniconda3.tar` and  `$WORKDIR/S1orbits.tar`  if files have been purged`.

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

