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

### 2. Benchmarking one processing step
*# Copy the job file into your project directory:
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

### 3. Benchmarking step as a function of nodes
*# Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy

```
run_step=13
nodes=2
nodes_list=( 1 2 3 4 )
partition=skx-normal
time=00:20:00

ntasks=48

for i in ${!nodes_list[@]}; do

  name='run_'$run_step'_nodes'$nodes
  cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  --export=run_num=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
  echo $cmd
   $cmd
done
```

