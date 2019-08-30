.bashrc file contents:

```
# .bashrc
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi
shopt -s expand_aliases

modules_shell="bash"
umask 002

module purge
#module load share-rpms65

#if  [ -n ${PARENTDIR} ] 
#then
#   export PYTHONPATH=${PYTHONPATH_RSMAS}
#fi
#[ -n ${PARENTDIR} ] && export PYTHONPATH=${PYTHONPATH_RSMAS}
          
# export the required variables (unless you use defaults_platforms.bash):
# WORKDIR, SCRATCHDIR, JOBSCHEDULER, QUEUENAME

export RSMASINSAR_HOME=~/test/operations/rsmas_insar
alias s.bgood='cd $RSMASINSAR_HOME; source setup/environment.bash;'
# In Miami:
alias s.bgood='cd $RSMASINSAR_HOME; source ~/accounts/defaults_platforms.bash; source setup/environment.bash; source ~/accounts/alias.bash; cd -;'
             
# vim: set filetype=sh:
export TERM=xterm
export VISUAL=/bin/vi
export CPL_ZIP_ENCODING=UTF-8
export HISTSIZE=1000
```

(The modules commands are only required for the pegasus system at RSMAS. The umask command gives others access to your files: everybody should be able to read/write in your scratch directory whereas nobody should be able to write in your home directory, but it is unclear whether this always works. s.cgood allows you to switch between different versions). 
