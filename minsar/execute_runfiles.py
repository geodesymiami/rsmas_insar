#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import argparse
import time
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js

##############################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='execute_runfiles')

    os.chdir(inps.work_dir)
    
    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    job_file_name = 'execute_runfiles'
    job_name = job_file_name

    if inps.wall_time == 'None':
        inps.wall_time = config[job_file_name]['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:

        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)
        sys.exit(0)

    time.sleep(wait_seconds)

    command_line = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
    message_rsmas.log(inps.work_dir, command_line)

    run_file_list = putils.read_run_list(inps.work_dir)

    if inps.endrun == 0:
        inps.endrun = len(run_file_list)

    if not inps.startrun == 0:
        inps.startrun = inps.startrun - 1

    run_file_list = run_file_list[inps.startrun:inps.endrun]

    for item in run_file_list:
        step_name = '_'
        step_name = step_name.join(item.split('_')[3::])
        try:
            memorymax = config[step_name]['memory']
        except:
            memorymax = config['DEFAULT']['memory']

        try:
            if config[step_name]['adjust'] == 'True':
                walltimelimit = putils.walltime_adjust(inps, config[step_name]['walltime'])
            else:
                walltimelimit = config[step_name]['walltime']
        except:
            walltimelimit = config['DEFAULT']['walltime']

        queuename = os.getenv('QUEUENAME')

        putils.remove_last_job_running_products(run_file=item)

        jobs = js.submit_batch_jobs(batch_file=item, out_dir=os.path.join(inps.work_dir, 'run_files'),
                                    work_dir=inps.work_dir, memory=memorymax, walltime=walltimelimit,
                                    queue=queuename)

        putils.remove_zero_size_or_length_error_files(run_file=item)
        putils.raise_exception_if_job_exited(run_file=item)
        putils.concatenate_error_files(run_file=item, work_dir=inps.work_dir)
        putils.move_out_job_files_to_stdout(run_file=item)

    return None


###########################################################################################

if __name__ == "__main__":
    main()
