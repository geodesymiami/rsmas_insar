###############################################
SCRIPT_DIR=$(dirname "${BASH_SOURCE[0]}")
echo "sourcing ${SCRIPT_DIR}/platforms_defaults.bash ..."

[ -z ${USER_PREFERRED} ] && export USER_PREFERRED=$USER
[ -z $HOSTNAME ] && export HOSTNAME=`hostname`
export JOBSCHEDULER=NONE
export QUEUENAME=NONE
export WORKDIR=~/insarlab
export SCRATCHDIR=${WORKDIR}/scratch

#############################################
########### known platforms ##################
#############################################
export NUMBER_OF_CORES_PER_NODE=16
export NUMBER_OF_THREADS_PER_CORE=1
export MAX_MEMORY_PER_NODE=16000

export JOB_SUBMISSION_SCHEME=singleTask
export JOB_SUBMISSION_SCHEME=multiTask_multiNode
export JOB_SUBMISSION_SCHEME=multiTask_singleNode
export JOB_SUBMISSION_SCHEME=launcher_multiTask_multiNode
export JOB_SUBMISSION_SCHEME=launcher_multiTask_singleNode

###############################################
if [[ ${HOSTNAME} == eos ]]
then
  export PLATFORM_NAME=eos_sanghoon
  export JOBSCHEDULER=PBS
  export QUEUENAME=batch
  export SCRATCHDIR=/scratch/insarlab/${USER_PREFERRED}
  export JOB_SUBMISSION_SCHEME=singleTask
fi
###############################################
if [[ ${HOSTNAME} == perfectly-elegant-tapir ]]
then
  export PLATFORM_NAME=jetstream
  export JOBSCHEDULER=NONE
  export QUEUENAME=NONE
  export WORKDIR=~/insarlab
  export SCRATCHDIR=/data/HDF5EOS
fi
###############################################
if [[ ${HOSTNAME} == *stampede* ]] || [[ ${TACC_SYSTEM} == *stampede* ]]
then
  export PLATFORM_NAME=stampede3
  # export PLATFORM_NAME=circleci         # for testing
  export JOBSCHEDULER=SLURM
  export JOBSHEDULER_PROJECTNAME=TG-EAR200012
  export WORKDIR=$(dirname -- "$WORK2")/stampede2/insarlab
  export SCRATCHDIR=${SCRATCH}
  export QUEUE_NORMAL=skx
  export QUEUE_DEV=skx-dev
  export QUEUENAME=$QUEUE_NORMAL
fi
###############################################
if [[ ${HOSTNAME} == *frontera* ]] || [[ ${TACC_SYSTEM} == *frontera* ]]
then
  export PLATFORM_NAME=frontera
  export JOBSCHEDULER=SLURM
  export JOBSHEDULER_PROJECTNAME=EAR20011
  export WORKDIR=$(dirname -- "$WORK2")/stampede2/insarlab
  export SCRATCHDIR=${SCRATCH}
  export SCRATCHDIR=$(echo $HOME | sed  's/home1/scratch2/')
  export QUEUE_NORMAL=normal
  export QUEUE_DEV=development
  export QUEUE_DEV2=development
  export QUEUENAME=flex
  export QUEUENAME=small
fi
###############################################
###############################################
if [[ ${HOSTNAME} == *comet* ]]
then
  export PLATFORM_NAME=comet
  export JOBSCHEDULER=SLURM
  #export QUEUENAME=compute
  export QUEUENAME=gpu
  export MAX_MEMORY_PER_NODE=20000
  export NUMBER_OF_CORES_PER_NODE=24
  export NUMBER_OF_THREADS_PER_CORE=1
  export JOBSHEDULER_PROJECTNAME=TG-EAR180012
  export WORKDIR=${HOME}/insarlab
  export SCRATCHDIR=/oasis/scratch/comet/$USER/temp_project
fi
###############################################
if [[ ${USER} == *circleci* ]] 
then
  export PLATFORM_NAME=circleci
  export JOBSCHEDULER=SLURM
  export JOBSHEDULER_PROJECTNAME=TG-EAR200012
  export WORKDIR=${HOME}
  export SCRATCHDIR=${HOME}
  export QUEUE_NORMAL=skx
  export QUEUE_DEV=skx-dev
  export QUEUENAME=$QUEUE_NORMAL
fi
###############################################
if [ "$(uname)" == "Darwin" ]
then
  export PLATFORM_NAME=mac
  export JOBSCHEDULER=NONE
  export QUEUENAME=NONE
  export WORKDIR=~/oneDrive/insarlab
  export SCRATCHDIR=~/onedrive/scratch
  export GEOS_DIR=/opt/homebrew/Cellar/geos/3.12.0
fi
