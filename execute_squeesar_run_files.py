#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
from rsmas_logging import loglevel
import argparse
import subprocess
from _process_utilities import get_project_name, send_logger
from _process_utilities import remove_zero_size_or_length_files, concatenate_error_files
from _process_utilities import remove_error_files_except_first
from _processSteps import create_or_update_template

logger_exec_run = send_logger()

##############################################################################
EXAMPLE = """example:
  execute_squeesar_run_files.py LombokSenAT156VV.template 
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('custom_template_file', nargs='?',
                        help='custom template with option settings.\n')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args)

    return inps


def get_run_files():
    """ Reads squeesar runfiles to a list. """

    runfiles = os.path.join(inps.work_dir, 'run_files_list_sq')
    run_file_list = []
    with open(runfiles, 'r') as f:
        new_f = f.readlines()
        for line in new_f:
            run_file_list.append('run_files_SQ/' + line.split('/')[-1][:-1])

    return run_file_list


def set_memory_defaults():
    """ Sets an optimized memory value for each job. """

    memoryuse = {'crop_merged_slc': '6000',
                 'create_patch': '3700',
                 'phase_linking': '3700',
                 'generate_interferogram_and_coherence': '3700',
                 'unwrap': '3700',
                 'corrections_and_velocity"': '8000'}

    return memoryuse


def submit_isce_jobs(run_file_list, cwd, memoryuse):
    """ Submits stackSentinel runfile jobs. """

    for item in run_file_list:
        item_memory = '_'
        item_memory = item_memory.join(item.split('_')[3::])
        try:
            memorymax = str(memoryuse[item_memory])
        except:
            memorymax = '3700'

        if os.getenv('QUEUENAME') == 'debug':
            walltimelimit = '0:30'
        else:
            walltimelimit = '4:00'

        queuename = os.getenv('QUEUENAME')

        cmd = 'create_batch.py ' + cwd + '/' + item + ' --memory=' + memorymax + ' --walltime=' + walltimelimit + \
               ' --queuename ' + queuename + ' --outdir "run_files_SQ"'
        print('command:', cmd)
        status = subprocess.Popen(cmd, shell=True).wait()
        if status is not 0:
            logger_exec_run.log(loglevel.ERROR, 'ERROR submitting {} using createBatch.pl'.format(item))
            raise Exception('ERROR submitting {} using create_batch.py'.format(item))

        job_folder = cwd + '/' + item + '_out_jobs'
        print('jobfolder:', job_folder)


    return None


##############################################################################
class inpsvar:
    pass


if __name__ == "__main__":

    inps = inpsvar()

    try:
        inps.custom_template_file = sys.argv[1]
        inps.start = int(sys.argv[2])
        inps.stop = int(sys.argv[3])
    except:
        print('')

    inps.project_name = get_project_name(inps.custom_template_file)
    inps.work_dir = os.getenv('SCRATCHDIR') + '/' + inps.project_name
    inps = create_or_update_template(inps)
    run_file_list = get_run_files()

    try:
        inps.start
    except:
        inps.start = 1
    try:
        inps.stop
    except:
        inps.stop = len(run_file_list)

    logger_exec_run.log(loglevel.INFO, "Executing Runfiles {} to {}".format(inps.start, inps.stop))

    memoryuse = set_memory_defaults()

    submit_isce_jobs(run_file_list[inps.start - 1:inps.stop], inps.work_dir, memoryuse)

    remove_zero_size_or_length_files(directory='run_files')

    concatenate_error_files(directory='run_files', out_name='out_stack_sentinel_errorfiles.e')

    remove_error_files_except_first(directory='run_files')

    logger_exec_run.log(loglevel.INFO, "-----------------Done Executing Run files-------------------")


