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

### 3. Benchmarking one step as function of nodes
*# Copy the job file into your project directory
```
cp $RSMASINSAR_HOME/minsar/unused/benchmark/run_launcher.job .
```
* #Select number of nodes, walltime and copy-paste. Job

```
run_step=13
nodes_list=( 3 4 5 6 7 8 9 10 )
partition=skx-normal      # can't use skx-dev in loop 
time=00:03:00

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
grep "Total" run_*.e | sort -V

```

### 4. Scaling plots for stampede proposal
```
aa=[
1 783 
2 472 
3 364
4 297
5 271
6 241
8 205
10 183
12 161
14 144
16 129
18 123
20 122
]
nodes=aa(:,1)
time=aa(:,2)


subplot(2,1,2)
plot(nodes,time(1)./time(:),'o-'), xlabel('nodes'),ylabel('speedup'), xlim([0 21]),ylim([0 7]), xticks([0:21]),yticks([0:7]),axis equal,set(gca,'FontSize',18)
xl=xlim

subplot(2,1,1)
plot(nodes,time,'o--'), xlabel('nodes'),ylabel('seconds'),xticks([0:21]),set(gca,'FontSize',18)
xlim(xl)
set(gcf,'color','w')
```
### 5. Benchmarking one step as function of tasks
*# NOT COMPLETED YET ###
```
```
* #Select number of nodes, walltime and copy-paste. Job

```
run_step=13
tasks_list=( 47 97 200 400 600 800 1000 )

partition=skx-normal      # can't use skx-dev in loop 
time=00:05:00

delay_const=1200          # submit next job with delay to not start simultaneously

XXXXXXX MODIFY run_launcher.py.  XXXXXXX
XXXXXXX to accept num_tasks and modiy run_file accordingly
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
grep "Total" run_*.e | sort -V

```

### 6. Scaling plot
```
aa=[
2 26
10 28
47 46
146 54
470 78
950 101
]
tasks=aa(:,1)
time=aa(:,2)


subplot(2,1,2)
plot(tasks,time(1)./time(:),'o-'), xlabel('tasks'),ylabel('speedup'),axis equal,set(gca,'FontSize',18)
xl=xlim

subplot(2,1,1)
plot(tasks,time,'o--'), xlabel('tasks'),ylabel('seconds'),set(gca,'FontSize',18)
xlim(xl)
set(gcf,'color','w')
```
### 7. bash tricks
```
#trap read debug
```

