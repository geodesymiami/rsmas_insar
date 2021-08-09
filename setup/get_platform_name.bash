echo "sourcing ${RSMASINSAR_HOME}/setup/get_platform_name.bash ..."
# get the PLATFORM_NAME
[ -z $HOSTNAME ] && export HOSTNAME=`hostname
[[ ${HOSTNAME} == *stampede* ]] || [[ ${TACC_SYSTEM} == *stampede* ]] && export PLATFORM_NAME=STAMPEDE2
[[ ${HOSTNAME} == *frontera* ]] || [[ ${TACC_SYSTEM} == *frontera* ]] && export PLATFORM_NAME=FRONTERA
[[ ${HOSTNAME} == *comet* ]]                                          && export PLATFORM_NAME=COMET
