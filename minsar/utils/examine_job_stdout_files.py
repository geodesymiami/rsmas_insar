#!/usr/bin/env python3
# This script summarizes information from job runs
# Author: Falk Amelung
# Created:5/2019
#######################################

import sys
import argparse
import glob
import datetime
from natsort import natsorted
from minsar.objects import message_rsmas


EXAMPLE = """example:
  examine_job_stdout_files.py run_*.o 
"""

inps = None


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Utility to examine job_output files.',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    #parser.add_argument('pattern', nargs='?', help='job_files')
    #parser.add_argument('--pattern', dest='pattern', type=str, default='run_*.o')
    parser.add_argument('pattern', help='jobfiles')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """
    parser = create_parser()
    return parser.parse_args(args)


def run_examine_job_stdout_files(pattern):
    """ generate job output statistics
    """

    files = glob.glob(pattern)
    # need to add for PBS. search_string='Terminated'

    files = natsorted(files)
    list_run_time_obj = []
    list_cpu_time_obj = []
    for file in files:
        with open(file) as fr:
            for line in fr:
               if 'Started at' in line:
                 start_time = line.split('Started at ')[1].rstrip()
                 start_time_obj = datetime.datetime.strptime(start_time,"%c")
               if 'Results reported' in line:
                 end_time = line.split('Results reported on ')[1].rstrip()
                 end_time_obj = datetime.datetime.strptime(end_time,"%c")
               if 'CPU time' in line:
                 toks = line.split('CPU time :')
                 cpu_time = toks[1].strip().split('sec')[0].strip()
                 cpu_time_obj = datetime.timedelta(seconds=int(float(cpu_time)))
                 list_cpu_time_obj.append(cpu_time_obj)

        run_time_obj = end_time_obj - start_time_obj
        list_run_time_obj.append(run_time_obj)
        #print(file + ' Running time: ' + str(run_time_obj))
        #print(file + ' CPU time:     ' + str(cpu_time_obj))

    list_run_time_obj = natsorted(list_run_time_obj, reverse=True)
    list_cpu_time_obj = natsorted(list_cpu_time_obj, reverse=True)
    
    for item in list_run_time_obj[0:3]:
         print(file + ' Running time: ' + str(item))
    print()
    return 

###########################################################################################


if __name__ == '__main__':
    message_rsmas.log(os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))
    inps = command_line_parse(sys.argv[1:])
    #run_examine_job_stdout_files(sys.argv[1:])
    run_examine_job_stdout_files(inps.pattern)

