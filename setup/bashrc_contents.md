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
umask 002

module purge

alias s.bgood='s.bnew'

export RSMASINSAR_HOME=~/test/test_operations/rsmas_insar
alias s.bnew='cd $RSMASINSAR_HOME; source ~/accounts/platforms_defaults.bash; source setup/environment.bash; source ~/accounts/alias.bash; source ~/accounts/login_alias.bash; cd -;'
#alias s.bnew='cd $RSMASINSAR_HOME; source setup/environment.bash;'

```

(The modules commands are only required for the pegasus system at RSMAS. The umask command gives others access to your files: everybody should be able to read/write in your scratch directory whereas nobody should be able to write in your home directory, but it is unclear whether this always works. s.cgood allows you to switch between different versions). 
