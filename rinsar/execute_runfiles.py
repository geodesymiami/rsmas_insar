#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import argparse
import subprocess
from rinsar.objects import message_rsmas
from rinsar.utils.process_utilities import create_or_update_template
from rinsar.utils.process_utilities import get_config_defaults, walltime_adjust
from rinsar.utils.process_utilities import remove_zero_size_or_length_files, read_run_list
import rinsar.create_batch as cb

##############################################################################
EXAMPLE = """example:
  execute_runfiles.py LombokSenAT156VV.template 
"""

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('start', nargs='?', type=int,
                        help='starting run file number (default = 1).\n')
    parser.add_argument('stop', nargs='?', type=int,
                        help='stopping run file number.\n')
    parser.add_argument('--submit', dest='submit_flag', action='store_true', help='submits job')

    return parser


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps

##############################################################################


def main(iargs=None):
    inps = command_line_parse(iargs)
    inps = create_or_update_template(inps)
    os.chdir(inps.work_dir)

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_file_name = 'execute_runfiles'
        work_dir = os.getcwd()
        job_name = inps.customTemplateFile.split(os.sep)[-1].split('.')[0]
        wall_time = '36:00'

        cb.submit_script(job_name, job_file_name, sys.argv[:], work_dir, wall_time)
        sys.exit(0)

    run_file_list = read_run_list(inps.work_dir)

    if inps.start is None:
        if 'run_0_' in run_file_list[0]:
            inps.start = 1
        else:
            inps.start = 0
    else:
        if not 'run_0_' in run_file_list[0]:
            inps.start = inps.start - 1

    if inps.stop is None:
        inps.stop = len(run_file_list)

    config = get_config_defaults(config_file='job_defaults.cfg')

    run_file_list = run_file_list[inps.start:inps.stop + 1]

    for item in run_file_list:
        step_name = '_'
        step_name = step_name.join(item.split('_')[3::])
        try:
            memorymax = config[step_name]['memory']
        except:
            memorymax = config['DEFAULT']['memory']

        try:
            if config[step_name]['adjust'] == 'True':
                walltimelimit = walltime_adjust(config[step_name]['walltime'])
            else:
                walltimelimit = config[step_name]['walltime']
        except:
            walltimelimit = config['DEFAULT']['walltime']

        queuename = os.getenv('QUEUENAME')

        jobs = cb.submit_batch_jobs(batch_file=item, out_dir=os.path.join(inps.work_dir, 'run_files'),
                                    memory=memorymax, walltime=walltimelimit, queue=queuename)

    return None


###########################################################################################

if __name__ == "__main__":
    main()
