## Benchmarking

I tried using --tasks-per-node and --ntasks-per-node but this did not work - I don't know why
### 1. Running as one job
*#Copy the job file into your project directory:
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
*#Select number of nodes, walltime and run in project directory

```
nodes=6
partition=skx-normal
time=01:00:00

name='run_all_nodes'$nodes
ntasks=$((nodes*48));

cmd="sbatch --job-name=$name --nodes=$nodes --ntasks=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
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
nodes=4
partition=skx-dev
time=00:20:00

name='run_'$run_step'_nodes'$nodes
ntasks=$((nodes*48));

cmd="sbatch --job-name=$name --nodes=$nodes --ntasks=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
      --partition=$partition --time=$time  --export=run_step=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
echo $cmd | cut -d ' ' -f 1-8 ; echo $cmd | cut -d ' ' -f 9 | cut -c 1-26 ; echo -e $cmd | cut -d ' ' -f 10
$cmd
```

### 3. Benchmarking one step with a variety of nodes (not tested)
*# Copy the job file into your project directory
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy-paste. Job

```
run_step=13
nodes_list=( 3 4 5 )
partition=skx-normal      # can't use skx-dev in loop 
time=00:06:00
delay_const=1200          # submit next job with delay to not start simultaneously

i=0
for nodes in ${nodes_list[@]}; do
   
  name='run_'$run_step'_nodes'$nodes
  ntasks=$((nodes*48));
  
  delay=$((i*$delay_const))

  cmd="sbatch --job-name=$name --nodes=$nodes --ntasks=$ntasks --output="$name"_%J.o --error="$name"_%J.e \
          --begin=now+$delay --partition=$partition --time=$time  --export=run_step=$run_step,PATH=$PATH,SCRATCHDIR=$SCRATCHDIR run_launcher.job"
  echo  $cmd | cut -d ' ' -f 1-8 ; echo $cmd | cut -d ' ' -f 9 | cut -c 1-26 ; echo -e $cmd | cut -d ' ' -f 10
  $cmd
  
  i=$((i+1))
done
```

### 4. Scaling plots for stampede proposal
```
aa = [ 1   895
     2   441
     3   295
     4   235
     5   240
     6   212
     7   176
     8   173
     9   173
    10   167
    12   249
    14   154 ]
    
nodes=aa(:,1)
time=aa(:,2)


subplot(2,1,2)
plot(nodes,time(1)./time(:),'o-'), xlabel('nodes'),ylabel('speedup'), xlim([0 7]),ylim([0 7]), xticks([0:7]),yticks([0:7]),axis equal,set(gca,'FontSize',18)
xl=xlim

subplot(2,1,1)
plot(nodes,time,'o--'), xlabel('nodes'),ylabel('seconds'),xticks([0:7]),set(gca,'FontSize',18)
xlim(xl)
set(gcf,'color','w')
```

