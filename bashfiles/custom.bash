# vim: set filetype=sh:
echo "sourcing $PWD/custom.bash ..."

###### MACHINE AND JOBSUBMISSION ####################################
#export NOTIFICATIONEMAIL=f.amelung@miami.edu           # If different from the typical famelung@rsmas.miami.edu (USER=famelung)

###################################################
#if [[ ${USER} == famelung ]] || [[  ${USER} == sxh733 ]]
#then
#  export SCRATCHDIR_ORIG=/scratch/projects/vdm/${USER}
#fi

############# GMT SOFTWARE ##########################
#export GMTHOME=/your/custom/path

export COOKIE_DLR="# HTTP cookie file.\nsupersites.eoc.dlr.de\tFALSE\t/\tFALSE\t0\tPHPSESSID\tfflk63nu8j3e1rv45auujq2586"
