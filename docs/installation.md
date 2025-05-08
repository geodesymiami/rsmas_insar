# Installation guide

* Set `$RSMASINSAR_HOME` in your [.bashrc](https://github.com/falkamelung/rsmas_insar/blob/master/docs/bashrc_contents.md) 
and [.bash_profile](./bash_profile.md).  You may want to set your variables in an external file as we do in Miami (see [example](https://gist.github.com/falkamelung/f1281c38e301a3296ab0483f946cac4b)).

* Create an ~/accounts directory with your data download credentials (for contents see [here](./accounts_info.md)). If you have access to the RSMAS accounts repo clone it into your /home or `$WORK2` directory 


## How to install RSMAS InSAR code 
Create an ~/accounts directory with your data download credentials (for contents see [here](./accounts_info.md)).  If you have access to the RSMAS accounts repo clone it into your /home or `$WORK2` directory  using **SSH** protocol (you need to copy the public key from your machine to github). 

```
git clone git@github.com:geodesymiami/accounts.git ~/accounts ;
```

* Go to the area where you want to install the code:

```
cd $WORK2/code
```
* Create a bash virgin environmen, clone the repo and install the code (including miniforge3 python) as user circleci (on the development queue (`idevdev` on Stampede3):
```
# command -v module &> /dev/null && module purge
env -i HOME=$HOME PATH=/usr/bin:/bin SHELL=/bin/bash USER=circleci bash --noprofile --norc
export USER=circleci
git clone git@github.com:geodesymiami/rsmas_insar.git ;
cd rsmas_insar
bash -x setup/install_python.bash
bash -x setup/install_code.bash
bash -x setup/install_credential_files.bash
```
The `install_python.bash` command is [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/install_python.bash) and  `install_code.bash`  is  [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/install_code.bash) and  `install_credential_files.bash`  is  [here](https://github.com/geodesymiami/rsmas_insar/blob/master/setup/install_credential_files.bash).

---
### Test your installation
```
cd $SCRATCHDIR
wget http://149.165.154.65/data/circleci/ci_small_unittestGalapagosSenDT128.tar
tar xvf ci_small_unittestGalapagosSenDT128.tar
minsarApp.bash $SAMPLESDIR/circleci/ci_unittestGalapagosSenDT128.template --start dem
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
