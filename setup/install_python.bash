#!/usr/bin/env bash
set -eo pipefail
echo "Exiting for circleCI test 9/2025"
exit 1 # for CircleCI test 9/2025

### Install python #########################
rm -rf tools/miniforge3
miniforge_version=Miniforge3-Linux-x86_64.sh
if [ "$(uname)" == "Darwin" ]; then miniforge_version=Miniforge3-MacOSX-arm64.sh ; fi
curl -L -O  https://github.com/conda-forge/miniforge/releases/latest/download/$miniforge_version

chmod 755 ${miniforge_version}
bash ${miniforge_version} -b -p tools/miniforge3
#tools/miniforge3/bin/mamba init bash

echo "Python installation DONE"
