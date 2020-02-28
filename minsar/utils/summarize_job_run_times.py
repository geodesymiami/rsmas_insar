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
import argparse
from minsar.objects.rsmas_logging import loglevel
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from natsort import natsorted

##############################################################################

def main(iargs=None):
    """
    summarize job durations
    """

    inps = putils.cmd_line_parse(iargs, script='summarize_job_run_times.py')

    os.chdir(inps.work_dir)

    run_stdout_files = glob.glob(inps.work_dir + '/run_files/run_*.o')
    
    if len(run_stdout_files) == 0:
        run_stdout_files = glob.glob(inps.work_dir + '/run_files/stdout_run_*/run_*.o')
    run_stdout_files = natsorted(run_stdout_files)
   
    job_id_list = []

   
    bursts = glob.glob(inps.work_dir + '/geom_master/*/hgt*rdr')
    text = 'Number of bursts: ' + str(len(bursts))
    print('{:32} {:1}'.format( text , "  NNodes  Timelimit   Reserved    Elapsed"))

    for fname in run_stdout_files:
        job_id = os.path.basename(fname).split('.o')[0].split('_')[-1]
        
        command = 'sacct --format=NNodes,Timelimit,reserved,elapsed -j ' + job_id
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True )
        stdout, stderr = process.communicate()
        
        out = stdout.splitlines()[2]
        print('{:32} {:1}'.format('_'.join(os.path.basename(fname).split('_')[0:-1]) , out.decode('utf-8')))

    return None

if __name__ == "__main__":
    main()
