#!/usr/bin/env python3
########################
# Author: Falk Amelung
#######################

import os
import sys
import glob
import time
import shutil
import argparse
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar.objects.unpack_sensors import Sensors

pathObj = PathFind()

###########################################################################################
def create_parser():
    parser = argparse.ArgumentParser(description='create jobfile to run save_hdf5.py for data in radar coordinates\n')

    parser = putils.add_common_parser(parser)
    parser.add_argument(dest='processing_dir', default=None, help='miaplpy network_* directory with data for hdf5 file\n')

    return parser

def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    print(inps)
    return inps


def main(iargs=None):

    inps = cmd_line_parse()
    inps.work_dir = os.getcwd()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    inps.num_data = 1
    inps.prefix = 'tops'   # in create_runfiles.py it was just there

    job_obj = JOB_SUBMIT(inps)

    dir = inps.work_dir +  '/' + inps.processing_dir
    dir = dir.rstrip(os.path.sep)
    
    
    # make run file:
    run_files_dirname = "run_files"
    run_dir = os.path.join(inps.work_dir, run_files_dirname)

    job_name = 'save_hdfeos5_radar_coord'
    job_file_name = job_name

    cmd1 = 'save_hdfeos5.py timeseries_demErr.h5 --tc temporalCoherence.h5 --asc avgSpatialCoh.h5 -m ../maskPS.h5 -g inputs/geometryRadar.h5 -t smallbaselineApp.cfg --suffix PS &'
    cmd2 = 'save_hdfeos5.py timeseries_demErr.h5 --tc temporalCoherence.h5 --asc avgSpatialCoh.h5 -m maskTempCoh.h5 -g inputs/geometryRadar.h5 -t smallbaselineApp.cfg --suffix PSDS &'

    command = ['cd ' + dir + '\n' + cmd1 + '\n' + cmd2 + '\nwait']
    job_obj.submit_script(job_name, job_file_name, command, writeOnly='True')

    return None

###########################################################################################


if __name__ == "__main__":
    main()
