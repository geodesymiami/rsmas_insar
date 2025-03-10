#!/usr/bin/env bash
set -eo pipefail

### Install python #########################
rm -rf tools/miniforge3
miniforge_version=Miniforge3-Linux-x86_64.sh
if [ "$(uname)" == "Darwin" ]; then miniforge_version=Miniforge3-MacOSX-arm64.sh ; fi
wget https://github.com/conda-forge/miniforge/releases/latest/download/$miniforge_version

chmod 755 ${miniforge_version}
bash ${miniforge_version} -b -p tools/miniforge3
#tools/miniforge3/bin/mamba init bash

### Create Conda Environment #########################
tools/miniforge3/bin/conda create --name inversion python=3.9 -y
echo "Conda environment 'inversion' created with Python 3.9"

### Activate Environment (Optional) ##################
# tools/miniforge3/bin/conda activate inversion

echo "Python installation DONE"
