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
```
############################################
### Source the environment and create aux directories. Install credential files for data download: ###
```
source ~/accounts/platforms_defaults.bash;
export RSMASINSAR_HOME=$(dirname $PWD)
source environment.bash;
./install_credential_files.bash;
```

# Dec 3  try on t2 without mamba, idevdev
```
conda install isce2 -c conda-forge --yes
conda install --yes --file ../minsar/requirements_all.txt
# conda install mintpy --yes     ## took to long
pip install -e ../tools/MintPy
#pip install --no-deps -e ../tools/MintPy

```

# Dec 3  I think this should work but was not veryified
* idevdev,
../tools/miniconda3/bin/conda install --yes --file ../minsar/requirements_all.txt
../tools/miniconda3/bin/conda install isce2 -c conda-forge --yes
../tools/miniconda3/bin/conda install mamba --yes                          # Very slow 20 hours
cat ../tools/MiaplPy/conda-env.yml | sed '/conda-for/d;/defaults/d' | awk '/^  -/ {print $2}' | sed 's/\([>=<]\)/ \1 /g' | cut -d ' ' -f1 | grep -v '^$' > ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/mamba install --yes --file ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/conda install mintpy --yes


* idevdev, conda isce, conda mamba, mambd miaplpy worked fine. Problems with mimtpy
 conda minsar requirements_all, conda isce, conda mamba, mambd miaplpy worked fine. Problems with mimtpy
* idevdev, conda isce, conda mamba, mambd miaplpy worked fine. Problems with mimtpy
* conda isce on idevdev, conda miaplpy on login, t2
#cd setup
../tools/miniconda3/bin/conda config --set solver classic
# run on an interactive node (idevdev), took 10 minutes for me
../tools/miniconda3/bin/conda install --yes --file ../tools/insarmaps_scripts/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/MimtPy/mimtpy/docs/requirements.txt 
../tools/miniconda3/bin/conda install --yes --file ../minsar/requirements.txt
../tools/miniconda3/bin/conda install isce2 -c conda-forge --yes 
cat ../tools/MiaplPy/conda-env.yml | sed '/conda-for/d;/defaults/d' | awk '/^  -/ {print $2}' | sed 's/\([>=<]\)/ \1 /g' | cut -d ' ' -f1 | grep -v '^$' > ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/pip install --no-deps -e ../tools/MiaplPy
../tools/miniconda3/bin/conda install mintpy --yes

# conda isce, mamba miaplpy, uninstall mamba, conda mintpy (t3)
#cd setup
../tools/miniconda3/bin/conda config --set solver classic
../tools/miniconda3/bin/conda install isce2 -c conda-forge --yes
../tools/miniconda3/bin/conda install mamba --yes
cat ../tools/MiaplPy/conda-env.yml | sed '/conda-for/d;/defaults/d' | awk '/^  -/ {print $2}' | sed 's/\([>=<]\)/ \1 /g' | cut -d ' ' -f1 | grep -v '^$' > ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/mamba install --yes --file ../tools/MiaplPy/requirements.txt
../tools/miniconda3/bin/pip install --no-deps -e ../tools/MiaplPy
../tools/miniconda3/bin/conda uninstall mamba --yes
../tools/miniconda3/bin/conda install mintpy --yes
../tools/miniconda3/bin/conda install --yes --file ../tools/insarmaps_scripts/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../tools/MimtPy/mimtpy/docs/requirements.txt
../tools/miniconda3/bin/conda install --yes --file ../minsar/requirements.txt
