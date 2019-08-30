# rsmas_insar
How to install RSMAS InSAR code.

* Use bash shell [see here for tcsh.](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/readme_old_tcsh.md) 
* Your [.bashrc](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/bashrc_contents.md) and [.bash_profile](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/bash_profile.md)

* CLone the RSMAS accounts repo into your `$HOME` if you have access (for the contents see [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/accounts_info.md)).

```
git clone https://github.com/geodesymiami/accounts.git ~/accounts ;
```

* Go to the area where you want to install the code (e.g. ~/test/test1).

```
cd ~/test/test1
```

* Install the code using the commands below (you need a reasonable recent git version (the default on pegasus is too old, get a [local version](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/install_git.md), or use an old rsmas_insar version). Installation takes about 10 minutes.  

```
bash
[ -f ~/local_git/miniconda3/bin/git ] && alias git=~/local_git/miniconda3/bin/git	

git clone https://github.com/geodesymiami/rsmas_insar.git ;
cd rsmas_insar

git clone https://github.com/insarlab/MintPy.git sources/MintPy ;
git clone https://github.com/geodesymiami/geodmod.git sources/geodmod;
git clone https://github.com/bakerunavco/SSARA.git 3rdparty/SSARA
git clone https://github.com/yunjunz/pyaps3.git 3rdparty/PyAPS/pyaps3
git clone https://github.com/geodesymiami/MimtPy.git sources/MimtPy ;

git clone https://github.com/isce-framework/isce2.git 3rdparty/isce2
mkdir -p sources/isceStack
cp -r 3rdparty/isce2/contrib/stack/topsStack sources/isceStack
cp -r 3rdparty/isce2/contrib/stack/stripmapStack sources/isceStack
rm -rf 3rdparty/isce2
########  Done with critical code.  ########

# Install tippecanoe for insarmaps (need gcc 4.9.1 or younger):
module load gcc/4.9.4
cd ../3rdparty
git clone https://github.com/mapbox/tippecanoe.git;
cd tippecanoe
make install PREFIX=$PWD
```
* Install your python environment:
```
#cd ../3rdparty; ln -s /nethome/famelung/MINICONDA3_GOOD miniconda3; cd ..; 

rm -r ../3rdparty/miniconda3
miniconda_version=Miniconda3-4.5.12-Linux-x86_64.sh
miniconda_version=Miniconda3-4.6.14-Linux-x86_64.sh
wget http://repo.continuum.io/miniconda/$miniconda_version --no-check-certificate #; if ($? != 0) exit; 
chmod 755 $miniconda_version
mkdir -p ../3rdparty
./$miniconda_version -b -p ../3rdparty/miniconda3
../3rdparty/miniconda3/bin/conda config --add channels conda-forge
../3rdparty/miniconda3/bin/conda install isce2 -c conda-forge --yes

../3rdparty/miniconda3/bin/conda install --yes --file ../sources/MintPy/docs/conda.txt
../3rdparty/miniconda3/bin/conda install --yes --file conda.txt
../3rdparty/miniconda3/bin/pip install --upgrade pip
../3rdparty/miniconda3/bin/pip install opencv-python
../3rdparty/miniconda3/bin/pip install geocoder
#../3rdparty/miniconda3/bin/pip install git+https://github.com/matplotlib/basemap.git#egg=mpl_toolkits. #needed for ARIA products
../3rdparty/miniconda3/bin/conda install basemap --yes
../3rdparty/miniconda3/bin/pip install git+https://github.com/tylere/pykml.git
```
* create aux directories (after sourcing environment), install credentials
```
source ~/accounts/platforms_defaults.bash;
source environment.bash;
mkdir -p $SENTINEL_ORBITS $SENTINEL_AUX $OPERATIONS/LOGS;
./$RSMASINSAR_HOME/setup/install_credential_files.csh;
```

* Get your an others inputfiles (default location: ~/insarlab/infiles/famelung/TEMPLATES) (optional):

```
cd $WORKDIR;
mkdir -p infiles;
cd infiles;
git clone https://github.com/geodesymiami/infiles_famelung.git famelung; 
git clone https://github.com/geodesymiami/infiles_sxh733.git sxh733; 
git clone https://github.com/geodesymiami/infiles_sxm1611.git sxm1611;
git clone https://github.com/geodesymiami/infiles_yzhang1.git yzhang1 ; 
git clone https://github.com/geodesymiami/infiles_bkv3.git bkv3;
git clone https://github.com/geodesymiami/infiles_lvxr.git lvxr;
echo DONE;
```

* Get the python scripts plus notebooks from other group members (all your code should be here) (optional) 

```
cd $RSMASINSAR_HOME/sources;
git clone https://github.com/geodesymiami/rsmas_tools.git ; 
```

### Orbits and aux files
You need to specify a directory for the orbits for Sentinel-1 (`$SENTINEL_ORBITS`). You can say `setenv SENTINEL_ORBITS ./orbits`  but it would download the orbits again and again. The orbits can be downloaded into `$SENTINEL_ORBITS` using `dloadOrbits.py`. The aux files (`SENTINEL_AUX`) are IPF calibration files. They can be downloaded from: https://qc.sentinel1.eo.esa.int/aux_cal/

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

* Next we need to add repositories to use Gamma and roi_pac. 

* The current installation contains password information. Once this is separated this repository can be made public. 

