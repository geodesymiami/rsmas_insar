##  Run the workflow using Containers

Using containers, you don't need to install the software. Instead follow this instruction:

The Docker image and information about containers can be found [here](https://gitlab.com/mirzaees/mgeolab)

1 - Edit your .bashrc and add the following:
```
module load tacc-singularity
module load python3
export MGEOLAB=mgeolab.sif
export PYTHONPATH=$SCRATCH/mjobs
export PATH=$PYTHONPATH:$PATH
export SINGULARITY_BINDPATH="/tmp:/home/jovyan"
alias s.bi='source ~/accounts/platforms_defaults.bash; source ~/accounts/environment.bash; source ~/accounts/alias.bash; source ~/accounts/login_alias.bash;' 
```

2 - Run following and modify password_config.py in `$SCRATCH/mjobs` then source with `s.bi`:
```
git clone https://github.com/geodesymiami/accounts.git ~/accounts ;
git clone https://github.com/geodesymiami/mjobs.git $SCRATCH/mjobs ;
```

3 - Login to a compute node and run 
```
cds; singularity pull mgeolab.sif docker://registry.gitlab.com/mirzaees/mgeolab:0.2
```

4 - Add this option to your template file:
```
topsStack.textCmd                 = "singularity exec /tmp/mgeolab.sif "
```

if singularity is on scratch use:
```
topsStack.textCmd                 = "singularity exec $SCRATCH/mgeolab.sif "
```

5 - Run `minsarApp.bash $templatefile`
