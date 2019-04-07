# rsmas_insar
How to install RSMAS InSAR code.

* Use bash shell [see here for tcsh.](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/readme_old_tcsh) 
* Your [.bashrc](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/bashrc_contents.md) and [.bash_profile](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/bash_profile.md)

* Go to the area where you want to install the code (e.g. ~/test/test1).

```
cd ~/test/test1
```

* Install the code using the commands below (you need a reasonable recent git version (the default on pegasus is too old, get a [local version](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/install_git.md), or use an old rsmas_insar version). Installation takes about 10 minutes.  For the contents of the accounts repository see [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/accounts_info.md) if you don't have access.

Old version:
```
git clone https://github.com/geodesymiami/rsmas_insar.git ;
cd rsmas_insar;
source default_isce22.bash;
cd setup;
./install_miniconda3.csh;
hash -r;
git clone https://github.com/geodesymiami/accounts ;
./download_ssara_tippecanoe_3rdparty.sh;
./download_atmosphere_code.sh;
./install_credential_files.csh;
./download_isce.py
./install_isce22.csh;

cd ../sources ;
git clone https://github.com/geodesymiami/rsmas_isce.git ; 
git clone https://github.com/yunjunz/PySAR.git ;
git clone https://github.com/falkamelung/geodmod.git ;
cd ..;
cd setup;
make PYKML ;
mkdir -p ~/insarlab/OPERATIONS/LOGS
echo DONE WITH CRITICAL CODE ;

make INSARMAPS;
cd .. ;
cd sources;
git clone https://github.com/geodesymiami/rsmas_tools.git ; 
cd -;
mkdir -p $SENTINEL_ORBITS;
mkdir -p $SENTINEL_AUX;
echo DONE;
```

New version, to use once Sara's restructuring is complete:
```
alias git='~/local_git/miniconda3/bin/git'

git clone https://github.com/geodesymiami/rsmas_insar.git ;
cd rsmas_insar;
source default_isce22.bash;
cd setup;
./install_miniconda3.csh;
hash -r;
git clone https://github.com/geodesymiami/accounts ;
./download_ssara_tippecanoe_3rdparty.sh;
./install_credential_files.csh;
./download_isce.py
./install_isce22.csh;
cd ../sources ;

git clone https://github.com/yunjunz/PySAR.git ;
git clone https://github.com/falkamelung/geodmod.git ;
cd -;
cd setup;
make PYKML ;
mkdir -p ~/insarlab/OPERATIONS/LOGS
echo DONE WITH CRITICAL CODE ;

make INSARMAPS;
cd .. ;
cd sources;
git clone https://github.com/geodesymiami/rsmas_tools.git ; 
cd -;
mkdir -p $SENTINEL_ORBITS;
mkdir -p $SENTINEL_AUX;
echo DONE;
```

The rsmas_tools clone gives you the python scripts plus notebooks from other group members. Put all your code into these directories and occasionaly push to github so that they will be available to others. We also share all other input files through github:

* The infiles is optional:

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

If you keep your *template files in this default location (e.g. /nethome/famelung/insarlab/infiles/famelung/TEMPLATES) they will be available to others. We also would like to share other input files (geodmod, coulomb, comsol through this directory).

### Orbits and aux files
You need to specify a directory for the orbits for Sentinel-1 (`$SENTINEL_ORBITS`). You can say `setenv SENTINEL_ORBITS ./orbits`  but it would download the orbits again and again.  It is unclear what the aux files do (`SENTINEL_AUX`)

(from Emre: aux files are IPF calibration files. They can be downloaded from this website:

https://qc.sentinel1.eo.esa.int/aux_cal/

The orbits can be downloaded automatically using dloadOrbits.py which is included in the first version we were using through Shimon’s account.)


### Next steps and possible problems
* To check your installation, run the testdata as explained [here](https://github.com/geodesymiami/rsmas_isce/wiki/Testing-the-code). You need to have the testdata in your `$TESTDATA_ISCE` directory.

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

* We still use tcsh. We plan to upgrade to bash asap.

* Next we need to add repositories to use Gamma and roi_pac. 

* The current installation contains password information. Once this is separated this repository can be made public. Rsmas_isce should be made part of this repository.

