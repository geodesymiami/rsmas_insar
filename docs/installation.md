# Installation guide
How to install RSMAS InSAR code.

* Set the required environment variables (`$RSMASINSAR_HOME, $JOBSCHEDULER, $QUEUENAME, $SCRATCHDIR`) in your [.bashrc](https://github.com/falkamelung/rsmas_insar/blob/master/docs/bashrc_contents.md) 
and [.bash_profile](./bash_profile.md). There are several other customizable environment variables. The defaults are given [here](./custom_variables.md). You may want to set your variables in an external file as we do in Miami (see [example](https://gist.github.com/falkamelung/f1281c38e301a3296ab0483f946cac4b)).

* Create an ~/accounts directory with your data download credentials (for contents see [here](./accounts_info.md)). If you have access to the RSMAS accounts repo clone it into your `$HOME` directtory.

```
git clone https://github.com/geodesymiami/accounts.git ~/accounts ;
```

* Go to the area where you want to install the code:

```
cd ~/test/test1
```

* Install the code using the commands below (you need a reasonable recent git version). 

```
bash
git clone https://github.com/geodesymiami/rsmas_insar.git ;
cd rsmas_insar
export RSMASINSAR_HOME=`pwd`

git clone https://github.com/insarlab/MintPy.git sources/MintPy ;
git clone https://github.com/isce-framework/isce2.git sources/isce2
git clone https://github.com/geodesymiami/MiNoPy.git sources/MiNoPy 
git clone https://github.com/geodesymiami/geodmod.git sources/geodmod ;
git clone https://github.com/geodesymiami/insarmaps_scripts.git sources/insarmaps_scripts ;
git clone https://github.com/geodesymiami/SSARA.git 3rdparty/SSARA ;
git clone https://github.com/yunjunz/pyaps3.git 3rdparty/PyAPS ;
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
./$miniconda_version -b -p ../3rdparty/miniconda3
../3rdparty/miniconda3/bin/conda config --add channels conda-forge
../3rdparty/miniconda3/bin/conda install --yes --file ../sources/MintPy/docs/conda.txt
../3rdparty/miniconda3/bin/pip install git+https://github.com/insarlab/PySolid.git
../3rdparty/miniconda3/bin/pip install git+https://github.com/tylere/pykml.git
../3rdparty/miniconda3/bin/conda install isce2 -c conda-forge --yes
../3rdparty/miniconda3/bin/conda install --yes --file ../docs/conda.txt
```
* #Source the environment and create aux directories. Install credential files for data download:
```
install_credential_files.csh;
cp -p ../minsar/additions/isce/logging.conf ../3rdparty/miniconda3/lib/python3.*/site-packages/isce/defaults/logging/logging.conf

source ~/accounts/platforms_defaults.bash;
source environment.bash;
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX $OPERATIONS/LOGS;

```
* #Adding HPC support for MintPy (parallel plotting and defaults to use dask Local Cluster) and latest isce version plus fixes
```
cp -p ../minsar/additions/mintpy/smallbaselineApp_auto.cfg ../sources/MintPy/mintpy/defaults/
cp -p ../minsar/additions/mintpy/plot_smallbaselineApp.sh ../sources/MintPy/mintpy/sh/

cp -p ../minsar/additions/isce2/topsStack/FilterAndCoherence.py ../sources/isce2/contrib/stack/topsStack
cp -p ../minsar/additions/isce2/topsStack/fetchOrbit.py ../sources/isce2/contrib/stack/topsStack
cp -p ../minsar/additions/isce2/stripmapStack/prepRawCSK.py ../sources/isce2/contrib/stack/stripmapStack

cp -r ../sources/isce2/contrib/stack/* $ISCE_STACK 

#cp -p ../minsar/additions/isce/invertMisreg.py ../sources/isce2/contrib/stack/stripmapStack
#cp -p ../minsar/additions/stackStripMap.py $ISCE_STACK/stripmapStack
#cp -p ../minsar/additions/isce/stackSentinel.py $ISCE_STACK/topsStack

```
* #create your `miniconda3.tar`  (removing `pkgs` saves space, could cause problems with environments)
```
cd $RSMASINSAR_HOME/3rdparty
rm -rf miniconda3/pkgs
tar cf miniconda3.tar miniconda3
```


### Orbits and aux files
This has created directories for the orbits for Sentinel-1 (`$SENTINEL_ORBITS`), which The can be downloaded using `dloadOrbits.py`. The IPF calibration files (`SENTINEL_AUX`) are downloaded from: https://qc.sentinel1.eo.esa.int/aux_cal/ .
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

