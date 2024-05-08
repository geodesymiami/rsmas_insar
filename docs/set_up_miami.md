## Research and development workflow in Miami
* If you want to use GBIS clone the repo (Marco Bagnardi plans to place this on GitHub soon) 
```
cd $RSMASINSAR_HOME
git clone https://github.com/geodesymiami/GBIS.git tools/GBIS;
```

* In order to facilitate  switching between  platforms (e.g. between pegasus, stampede and your mac), it is recommended to keep all your control files (minsar, geodmod, gbis) in your infiles directory and share via github, following this convention. the directory name is set using the customizable USER_PREFERRED environment variable.
```
$WORKDIR/infiles_famelung/TEMPLATES
$WORKDIR/infiles_famelung/GEODMOD_INFILES
$WORKDIR/infiles_famelung/GBIS_INFILES
```
You can get the infiles form other group members by cloning their infiles directories: 

```bash
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
Also, everybody should keep their matlab, python and other scripts  plus notebooks that are not part of MinSAR in our [tools repository](https://github.com/geodesymiami/rsmas_tools). This is an effort to make your code available to others. (optional)
```bash
cd $RSMASINSAR_HOME/sources;
git clone https://github.com/geodesymiami/rsmas_tools.git ; 
```
Useful Jupyter Notebooks:
```
mkdir -p $RSMAS_INSAR/notebooks;
cd $RSMAS_INSAR/notebooks
git clone https://github.com/insarlab/MintPy-tutorial.git 
git clone https://github.com/insarlab/MiaplPy_notebooks.git
git clone https://github.com/geodesymiami/2021_MaunaLoa_Varugu_Amelung.git 
git clone https://github.com/mirzaees/2022_MiaplPy_Mirzaee_Amelung_Fattahi.git 
git clone https://github.com/geodesymiami/Yunjun_et_al-2019-MintPy.git
git clone https://github.com/geodesymiami/PlotData-notebooks.git
git clone https://github.com/geodesymiami/viewPS-notebooks.git
git clone https://github.com/geodesymiami/precip-notebooks.git
git clone https://github.com/isce-framework/isce2-docs.git
```
