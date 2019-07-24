#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import argparse
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
import time
import minsar.job_submission as js

pathObj = PathFind()
##############################################################################
EXAMPLE = """example:
  smallbaseline_wrapper.py LombokSenAT156VV.template 
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('--submit', dest='submit_flag', action='store_true', help='submits job')

    return parser


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps


###########################################################################################

def main(iargs=None):

    inps = command_line_parse(iargs)
    inps = putils.create_or_update_template(inps)

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_file_name = 'smallbaseline_wrapper'
        inps.wall_time = config[job_file_name]['walltime']
        job_name = inps.customTemplateFile.split(os.sep)[-1].split('.')[0]

        js.submit_script(job_name, job_file_name, sys.argv[:], inp.work_dir, inps.wall_time)
        sys.exit(0)

    os.chdir(inps.work_dir)

    # make a job for smallbaseline, run and wait for result

    command_mintpy = 'smallbaselineApp.py ' + inps.customTemplateFile

    job_name = 'run_smallbaseline'

    job_file_name = 'run_smallbaseline'

    walltime = config['smallbaseline']['walltime']

    memory = config['smallbaseline']['memory']

    putils.remove_last_job_running_products(run_file=job_file_name)

    js.write_single_job_file(job_name, job_file_name, command_mintpy, inps.work_dir, email_notif=False, scheduler=None,
                          memory=memory, walltime=walltime, queue=None)

    job_number = js.submit_single_job("{0}.job".format(job_file_name), inps.work_dir, scheduler=None)

    files = "{}_{}.o".format(job_file_name, job_number)
    i = 0
    wait_time_sec = 60
    total_wait_time_min = 0

    if os.path.isfile("{0}.o".format(job_file_name)):
        print("Job #{} of {} complete (output file {})".format(i + 1, 1, files))
    else:
        print("Waiting for job #{} of {} (output file {}) after {} minutes".format(i + 1, 1, files,
                                                                                   total_wait_time_min))
        total_wait_time_min += wait_time_sec / 60
        time.sleep(wait_time_sec)

    putils.remove_zero_size_or_length_error_files(run_file=job_file_name)
    putils.raise_exception_if_job_exited(run_file=job_file_name)
    putils.concatenate_error_files(run_file=job_file_name, work_dir=inps.work_dir)
    putils.move_out_job_files_to_stdout(run_file=job_file_name)


    # Email results

    command_email = 'email_results.py ' + inps.customTemplateFile

    os.system(command_email)

###########################################################################################


if __name__ == "__main__":
    main()


