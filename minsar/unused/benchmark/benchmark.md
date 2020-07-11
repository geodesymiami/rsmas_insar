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
time=00:30:00

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
      --partition=$partition --time=$time  --export=run_step=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
echo $cmd | cut -d ' ' -f 1-8 ; echo $cmd | cut -d ' ' -f 9 | cut -c 1-26 ; echo -e $cmd | cut -d ' ' -f 10
$cmd
```

### 3. Benchmarking one step with a variety of nodes
*# Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy

```
run_step=13
nodes_list=( 1 2 3 4 5 )
partition=skx-normal
time=00:20:00

ntasks=48

for nodes in ${nodes_list[@]}; do

  name='run_'$run_step'_nodes'$nodes
  cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  --export=run_step=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
  
  echo  $cmd | cut -d ' ' -f 1-8 ; echo $cmd | cut -d ' ' -f 9 | cut -c 1-26 ; echo -e $cmd | cut -d ' ' -f 10
  $cmd
done
```

### 4. Backup - calculation for stampede proposal
3390 tasks   = 71 * 48
using:
1920 tasks = 40 * 48

4 bursts 
run_13: 120 sec -->  120 * 40 = 80 min 
run_15: 160 sec -->  160 * 40 = 107 min 
```
run_step=13
partition=skx-normal

nodes_list=( 1 2 ); time=02:0:00
nodes_list=( 3 4 5 ); time=01:00:00
nodes_list=( 6 8 10 ); time=0:30:00
nodes_list=( 12 14 16); time=0:10:00
nodes_list=( 20 ); time=0:05:00

ntasks=48

for nodes in ${nodes_list[@]}; do

  name='run_'$run_step'_nodes'$nodes
  cmd="sbatch --job-name=$name --nodes=$nodes --tasks-per-node=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  --export=run_step=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
  
  echo  $cmd | cut -d ' ' -f 1-8 ; echo $cmd | cut -d ' ' -f 9 | cut -c 1-26 ; echo -e $cmd | cut -d ' ' -f 10
  $cmd
done
```

