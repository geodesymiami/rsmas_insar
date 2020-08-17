#!/bin/bash
#SBATCH -J unittestGalapagosSenDT128
#SBATCH -A TG-EAR200012
#SBATCH --mail-user=sxm1611@rsmas.miami.edu
#SBATCH --mail-type=fail
#SBATCH -N 1
#SBATCH -n 48
#SBATCH -o out_job_%J.o
#SBATCH -e out_job_%J.e
#SBATCH -p skx-normal
#SBATCH -t 00:30:00

export PATH=$ISCE_STACK/topsStack:$PATH
export PROJECTDIR=$SCRATCH/unittestGalapagosSenDT128
export templatefile=$SAMPLESDIR/unittestGalapagosSenDT128.template

mkdir -p $PROJECTDIR/DEM

cd $PROJECTDIR/DEM
dem_rsmas.py $templatefile

cd $PROJECTDIR
create_runfiles.py $templatefile --job

module load launcher
export LAUNCHER_WORKDIR=$PROJECTDIR/run_files
export LAUNCHER_SCHED=block
input=$PROJECTDIR/run_files_list

while IFS= read -r line
do
for entry in "$line"_*
do
if [ ! "${entry: -2}" == ".o" ] && [ ! "${entry: -2}" == ".e" ] && [ ! "${entry: -4}" == ".job" ]; then
echo "$entry"
export LAUNCHER_JOB_FILE="$entry"
$LAUNCHER_DIR/paramrun
check_job_outputs.py "$entry"
fi
done
done < $input

smallbaselineApp.py $templatefile --dir $PROJECTDIR/mintpy
