##  Run the workflow using Containers

Using containers, you don't need to install the software. Instead follow this instruction:

The Docker image and information about containers can be found [here](https://gitlab.com/mirzaees/mgeolab)

1 - Edit your .bashrc and add the following and source with `s.bi`:
```
module load tacc-singularity
export PYTHONPATH=$SCRATCH/mjobs
export PATH=$PYTHONPATH:$PATH
export SINGULARITY_BINDPATH="/tmp:/home/jovyan"
alias s.bi='source ~/accounts/platforms_defaults.bash; source ~/accounts/environment.bash; source ~/accounts/alias.bash; source ~/accounts/login_alias.bash;' 
```

2 - Run `git clone https://github.com/geodesymiami/mjobs.git $SCRATCH`

3 - Run `singularity pull docker://registry.gitlab.com/mirzaees/mgeolab:0.1`

4 - Add this option to your template file:
```
topsStack.textCmd                 = "singularity exec $SCRATCH/mgeolab_0.1.sif"
```

4 - Run `minsarApp.bash $templatefile`
