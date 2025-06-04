#!/usr/bin/env bash
set -eo pipefail

### Source the environment  #################
export RSMASINSAR_HOME="$PWD"
source setup/platforms_defaults.bash
source setup/environment.bash

git clone git@github.com:EliTras/VSM.git tools/VSM

### Install dependencies into vsm environment #########################
conda create --name vsm python=3.10 pip -y
source tools/miniforge3/etc/profile.d/conda.sh
conda activate vsm

pip install -r tools/VSM/VSM/requirements.txt
#pip install -e tools/VSM
###  Reduce miniforge3 directory size #################
rm -rf tools/miniforge3/pkgs

echo ""
echo "Installation of install_VSM.bash DONE"
