#!/usr/bin/env python3
########################
# Author:  Falk Amelung
# 2/2020
#######################

import os
import subprocess
import sys
import glob
import time
import shutil
from pathlib import Path
import argparse
from minsar.objects.rsmas_logging import loglevel
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from natsort import natsorted

EXAMPLE = """example:
  summarize_job_run_times.py --local
  summarize_job_run_times.py
  cd run_files; summarize_job_run_times.py --local

  summarize_job_run_times.py $SAMPLESDIR/unittestGalapagosSenDT128.template
  \n
"""

##############################################################################

def main(iargs=None):
    """
    summarize job durations
    """

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Utility to summarize job times and service units billed',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument('custom_template_file', metavar="FILE", default='None', nargs='?', help='template file to use [default: working directory]')
    parser.add_argument('--local', dest='local_flag', action='store_true', default=False, help='for current (local) directory')

    inps = parser.parse_args(args=iargs)

    try: 
        inps = putils.create_or_update_template(inps)
        run_files_dir = inps.work_dir + '/run_files'
    except:
        cwd = os.getcwd()
        if 'run_files' in os.path.basename(cwd):
            inps.work_dir = os.path.dirname(cwd)
            inps.project_name = os.path.basename(inps.work_dir)
            run_files_dir = cwd
        else:
            inps.work_dir = cwd
            inps.project_name = os.path.basename(inps.work_dir)
            run_files_dir = cwd + '/run_files'

    run_stdout_files = glob.glob(run_files_dir + '/run_*_*_[0-9][0-9][0-9][0-9]*.o') + glob.glob(run_files_dir + '/*/run_*_*_[0-9][0-9][0-9][0-9]*.o')
    #run_stdout_files = natsorted(run_stdout_files)
    
    #run_stdout_files2 = glob.glob(run_files_dir + '/stdout_run_*/run_*.o')
    #run_stdout_files2 = natsorted(run_stdout_files2)
    #run_stdout_files.extend(run_stdout_files2)

    if len(run_stdout_files) == 0:
        run_stdout_files = glob.glob(run_files_dir + '/stdout_run_*/run_*.o')
        run_stdout_files = natsorted(run_stdout_files)
   
    run_stdout_files_base=[]
    for f in run_stdout_files:
        run_stdout_files_base.append(os.path.basename(f))
    run_stdout_files = natsorted(run_stdout_files_base)

    bursts = glob.glob(inps.work_dir + '/geom_reference/*/hgt*rdr')
    number_of_bursts = len(bursts)
    
    if len(bursts) == 0:
        number_of_bursts = 1

    out_lines = []
    string = 'run_files_dir:  ' + run_files_dir
    print( string ); out_lines.append(string)
    text = 'Number of bursts: ' + str(number_of_bursts)
    string ='{:32} {:1}'.format( text , "  NNodes  Timelimit   Reserved    Elapsed  Time_per_burst")
    print (string); out_lines.append(string)

    num_nodes_list = []
    wall_time_list = []
    reserved_time_list = []
    elapsed_time_list = []

    hostname = subprocess.Popen("hostname -f", shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")

    scheduler = None
    for platform in ['frontera', 'stampede2', 'comet']:
        if platform in hostname:
            scheduler = 'SLURM'
            break
    if not scheduler == 'SLURM':
       print('Not on TACC system - return from summarize_job_run_times.py')
       return None

    test_lines=[]
    last_name=[]
    for fname in run_stdout_files:
        job_id = fname.split('.o')[0].split('_')[-1]
        
        command = 'sacct --format=NNodes,Timelimit,reserved,elapsed -j ' + job_id
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
        stdout, stderr = process.communicate()
        try:
            out = stdout.splitlines()[2]
        except:
            continue
        num_nodes     = out.decode('utf-8').split()[0]
        wall_time     = out.decode('utf-8').split()[1]
        reserved_time = out.decode('utf-8').split()[2]
        elapsed_time  = out.decode('utf-8').split()[3]
   
        time_per_burst = putils.multiply_walltime(elapsed_time, factor = 1/number_of_bursts)

        name = '_'.join(fname.split('_')[0:-2])
        if name != last_name:
           last_name = name
           print("")
           out_lines.append("\n")

        string ='{:32} {:1}  {:1}'.format('_'.join(fname.split('_')[0:-1]) , out.decode('utf-8'), time_per_burst)
        print( string ); out_lines.append(string)
 
        if name == "run_04_fullBurst_geo2rdr":
           test_lines.append(string)

        num_nodes_list.append(num_nodes)
        wall_time_list.append(wall_time)
        reserved_time_list.append(reserved_time)
        elapsed_time_list.append(elapsed_time)
       
    reserved_time_sum = putils.sum_time(reserved_time_list)
    elapsed_time_sum = putils.sum_time(elapsed_time_list)
    total_time = putils.sum_time( [reserved_time_sum, elapsed_time_sum] )

    service_units =  calculate_service_units(num_nodes_list, elapsed_time_list)

    if os.path.exists('run_files/rerun.log'):
        file = open('run_files/rerun.log',mode='r')
        rerun_log = file.read()
        print('\n' + rerun_log); out_lines.append('\n' + rerun_log)

    string = '\nTotal reserved (pending), elapsed time: ' + reserved_time_sum +  ' ' + elapsed_time_sum
    print (string); out_lines.append(string)
    string ='Total time:                             ' + total_time
    print (string); out_lines.append(string)
    string ='Service units:                          ' +  str(round(service_units,1))
    print (string); out_lines.append(string)
    string =' '
    print (string); out_lines.append(string)
    
    home_dir = os.getenv('HOME')
    save_job_run_times_summary(home_dir + '/job_summaries', out_lines, inps.project_name)

    save_job_run_times_summary(home_dir + '/job_summaries', test_lines, inps.project_name)
    return None


##########################################################################

def calculate_service_units(num_nodes_list, elapsed_time_list):
    """ calculates the service units billed """
    """ SUs billed (node-hours) = (# nodes) x (job duration in wall clock hours) x (charge rate per node-hour) """

    #for item1 in num_nodes_list and item2 in elapsed_time_list:
    seconds_sum = 0
    for num_nodes, elapsed_time in zip(num_nodes_list, elapsed_time_list):
        hours, minutes, seconds = elapsed_time.split(':')
        elapsed_time_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        seconds_sum = seconds_sum +int( num_nodes) * elapsed_time_seconds

    service_units = seconds_sum / 3600 
    return service_units

##########################################################################

def save_job_run_times_summary(summary_dir, content, project_name):
    """ saves job run times summary at given location """

    if not os.path.exists(summary_dir):
         os.mkdir(summary_dir)
         Path(summary_dir + '/summary.0').touch()

    summary_files = glob.glob(summary_dir + '/summary*')
    summary_files = natsorted(summary_files)
    last_file = summary_files[-1]
    last_number = os.path.basename(last_file).split('.')[1]

    new_number = int(last_number) + 1
    new_file = summary_dir + '/summary.' + str(new_number) + '.' +  project_name

    with open(new_file, 'w') as f:
        for line in content:
            f.write(str(line) + '\n')

    return 


##########################################################################

if __name__ == "__main__":
    main()
