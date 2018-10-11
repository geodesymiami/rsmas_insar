#!/usr/bin/env python3

import os
import sys
import logging
import argparse
import subprocess
import _process_utilities as putils
sys.path.insert(0, os.getenv('SSARAHOME'))
from pysar.utils import readfile
from pysar.utils import utils

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_formatter = logging.Formatter("%(levelname)s - %(message)s")
# process_rsmas.log File Logging
fileHandler = logging.FileHandler(os.getenv('SCRATCHDIR')+'/process_rsmas.log', 'a+', encoding=None)
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(std_formatter)

# command line logging
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
streamHandler.setFormatter(std_formatter)

logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

##############################################################################


def get_run_files():

    logfile = os.path.join(inps.work_dir, 'out_stackSentinel.log')
    run_file_list = []
    with open(logfile, 'r') as f:
        new_f = f.readlines()
        f.seek(0)
        for line in new_f:
            if '/run_files/' in line:
                 run_file_list.append('run_files/'+line.split('/')[-1][:-1])
    return run_file_list

##############################################################################


def get_template_values(inps):

    # write default template
    inps.template_file = putils.create_default_template()

    inps.custom_template = putils.create_custom_template(
        custom_template_file=inps.custom_template_file,
        work_dir=inps.work_dir)

    if not inps.template_file == inps.custom_template:
        inps.template_file = utils.update_template_file(
            inps.template_file, inps.custom_template)

    inps.template = readfile.read_template(inps.template_file)

    putils.set_default_options(inps)

##############################################################################


def submit_isce_jobs(run_file_list, cwd, memoryuse):
    for item in run_file_list:
        memorymax = str(memoryuse[int(item.split('_')[2]) - 1])
        if os.getenv('QUEUENAME') == 'debug':
            walltimelimit = '0:30'
        else:
            walltimelimit = '4:00'  # run_1 (master) for 2 subswaths took 2:20 minutes

        if len(memoryuse) == 13:
            if item.split('_')[2] == '10':
                walltimelimit = '60:00'
        cmd = 'createBatch.pl ' + cwd + '/' + item + ' memory=' + memorymax + ' walltime=' + walltimelimit
        # FA 7/18: need more memory for run_7 (resample) only
        # FA 7/18: Should hardwire the memory requirements for the different workflows into a function and use those

        # TODO: Change subprocess call to get back error code and send error code to logger

        status = subprocess.Popen(cmd, shell=True).wait()
        if status is not 0:
            logger.error('ERROR submitting jobs using createBatch.pl')
            raise Exception('ERROR submitting jobs using createBatch.pl')

##############################################################################

class inpsvar:
    pass

##############################################################################


if __name__ == "__main__":


    inps = inpsvar()

    try:
        inps.custom_template_file = sys.argv[1]
        inps.start = int(sys.argv[2])
        inps.stop = int(sys.argv[3])
    except:
        print('')

    inps.projName = putils.get_project_name(inps.custom_template_file)
    inps.work_dir = os.getenv('SCRATCHDIR') + '/' + inps.projName
    run_file_list = get_run_files()

    try:
        inps.start
    except:
        inps.start = 1
    try:
        inps.stop
    except:
        inps.stop = len(run_file_list)


    get_template_values(inps)
    logger.info("Executing Runfiles %s", str(inps.start) + ' to ' + str(inps.stop))


    memoryuse = putils.get_memory_defaults(inps.workflow)
    submit_isce_jobs(run_file_list[inps.start - 1:inps.stop], inps.work_dir, memoryuse)
    logger.info("-----------------Done Executing Run files-------------------")
