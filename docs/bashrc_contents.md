.bashrc file contents:

```
# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific aliases and functions
shopt -s expand_aliases

modules_shell="bash"
[ -n module ] && purge
umask 002

alias s.bgood='s.bnew'

export RSMASINSAR_HOME=~/test/development/rsmas_insar

export JOBSCHEDULER=LSF
export QUEUENAME=general
export SCRATCHDIR=/projects/scratch/insarlab/${USER}

alias s.bnew='cd $RSMASINSAR_HOME; source setup/environment.bash;'  
alias s.bnew='cd $RSMASINSAR_HOME; source ~/accounts/platforms_defaults.bash; source setup/environment.bash; source ~/accounts/alias.bash; source ~/accounts/login_alias.bash; cd -;'

```

(The modules commands are only required for the pegasus system at RSMAS. The umask command gives others access to your files: everybody should be able to read/write in your scratch directory whereas nobody should be able to write in your home directory, but it is unclear whether this always works. s.bgood is required if your DOWNLOADHOST is not local for remore ssh). 
