## Benchmarking

### 1. Running as one job
* #Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy

```
nodes=2
partition=skx-normal
time=00:10:00

ntasks=48
name='run_'$run_num'_nodes'$nodes

cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  run_launcher.job"
echo $cmd
$cmd
```


```

run_num=13
nodes=1

declare -i ntasks=nodes*48 
ntasks=48
name='run_'$run_num'_nodes'$nodes
partition=skx-dev
time=00:10:00

cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time --export=run_num=$run_num,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
echo $cmd
$cmd

#sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output=$name.o --error=$name.e \
#      --partition=$partition --time=$time --export=run_num=$run_num run_launcher.job
```

