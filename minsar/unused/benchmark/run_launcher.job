#! /bin/bash
#SBATCH -J run_all
#SBATCH -A TG-EAR200012
#SBATCH --mail-user=famelung@rsmas.miami.edu
#SBATCH --mail-type=fail
#SBATCH -N 1
#SBATCH -n 48
#SBATCH -o run_all_%J.o
#SBATCH -e run_all_%J.e
#SBATCH -p skx-dev
#SBATCH -t 01:00:00

declare -a run_files_list run_files num_threads
run_files_list=( run_01_unpack_topo_reference run_02_unpack_secondary_slc run_03_average_baseline \
            run_04_extract_burst_overlaps run_05_overlap_geo2rdr run_06_overlap_resample \
            run_07_pairs_misreg run_08_timeseries_misreg run_09_fullBurst_geo2rdr run_10_fullBurst_resample \
            run_11_extract_stack_valid_region run_12_merge_reference_secondary_slc \
            run_13_generate_burst_igram run_14_merge_burst_igram run_15_filter_coherence run_16_unwrap )
num_threads=(8 2 2 2 4 2 2 4 4 4 4 2 2 8 8 2)
num_threads=(8 1 1 1 4 4 1 1 8 4 1 1 1 1 1 1)

project=$(basename $PWD)

SECONDS=0
module load launcher
export LD_PRELOAD=/home1/apps/tacc-patches/python_cacher/myopen.so
export PATH=$RSMASINSAR_HOME/sources/isce2/contrib/stack/topsStack:$PATH
export LAUNCHER_WORKDIR="$SCRATCH/$project/run_files"

if [ -z ${run_step+x} ]; then 
   echo "run_step is unset; using all";
   run_files=(${run_files_list[@]})
else
   echo "run_step is set: $run_step";
   run_files=${run_files_list[$((run_step-1))]}
fi

echo "SCRATCHDIR:" $SCRATCH
echo "project:" $project
echo "LAUNCHER_WORKDIR: $LAUNCHER_WORKDIR"
echo "run_files:  ${run_files[@]}"

echo "#######################"
for i in ${!run_files[@]}; do
 export OMP_NUM_THREADS=${num_threads[$i]}
 export LAUNCHER_JOB_FILE=$LAUNCHER_WORKDIR/${run_files[$i]}
 echo $OMP_NUM_THREADS $LAUNCHER_JOB_FILE
 echo "LAUNCHER_JOB_FILE: $LAUNCHER_JOB_FILE"
 prior=$SECONDS
 $LAUNCHER_DIR/paramrun
 >&2 echo elapsed time [sec]: ${run_files[$i]} "$(($SECONDS-$prior))"
done

sec_total=$SECONDS
((sec=SECONDS%60, SECONDS/=60, min=SECONDS%60, hrs=SECONDS/60))
timestamp=$(printf "%d:%02d:%02d" $hrs $min $sec)

>&2 echo Total elapsed time [sec, HH:MM:SS]: $sec_total  $timestamp
