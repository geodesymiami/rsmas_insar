## Benchmarking

### 1. Running as one job
*#Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
*#Select number of nodes, walltime and run in project directory

```
nodes=2
partition=skx-normal
time=00:10:00

ntasks=48
name='run_nodes'$nodes

cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  run_launcher.job"
echo $cmd
$cmd
```

### 1. Benchmarking one processing step
* # Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy

```
run_step=13
nodes=2
partition=skx-dev
time=00:10:00

ntasks=48
name='run_'$run_step'_nodes'$nodes

cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  --export=run_num=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
echo $cmd
$cmd


```

