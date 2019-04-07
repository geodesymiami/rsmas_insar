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
module load share-rpms65

if  [ -n ${PARENTDIR} ] 
then
   export PYTHONPATH=${PYTHONPATH_RSMAS}
fi
alias s.bgood='s.btest1'
alias s.btest1='cd  ~/test/test1/rsmas_insar; source default_isce22.bash; source platforms.bash; source alias.bash; source custom.bash; cd -;'

export HISTSIZE=1000
```

(The modules commands are only required for the pegasus system at RSMAS. The umask command gives others access to your files: everybody should be able to read/write in your scratch directory whereas nobody should be able to write in your home directory, but it is unclear whether this always works. s.cgood allows you to switch between different versions). 
