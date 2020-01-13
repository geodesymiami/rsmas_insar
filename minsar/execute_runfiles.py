#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import time
import datetime
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
import contextlib
import subprocess
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

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

    run_file_list = putils.read_run_list(inps.work_dir)

    if inps.end_run == 0:
        inps.end_run = len(run_file_list)

    if not inps.start_run == 0:
        inps.start_run = inps.start_run - 1

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    run_file_list = run_file_list[inps.start_run:inps.end_run]

    supported_schedulers = ['LSF', 'PBS', 'SLURM']

    if os.getenv('JOBSCHEDULER') in supported_schedulers:

        for item in run_file_list:
            step_name = '_'
            step_name = step_name.join(item.split('_')[3::])
            try:
                memorymax = config[step_name]['memory']
            except:
                memorymax = config['DEFAULT']['memory']

            try:
                # FA 26 Dec commented out as it seemed wrong
                #if config[step_name]['adjust'] == 'True':
                #    walltimelimit = putils.walltime_adjust(inps, config[step_name]['walltime'])
                #else:
                #    walltimelimit = config[step_name]['walltime']
                walltimelimit = config[step_name]['walltime']
            except:
                walltimelimit = config['DEFAULT']['walltime']

            queuename = os.getenv('QUEUENAME')

            putils.remove_last_job_running_products(run_file=item)

            if os.getenv('JOBSCHEDULER') in ['SLURM', 'sge']:

                js.submit_job_with_launcher(batch_file=item, work_dir=os.path.join(inps.work_dir, 'run_files'),
                                            memory=memorymax, walltime=walltimelimit, queue=queuename)

            else:

                jobs = js.submit_batch_jobs(batch_file=item, out_dir=os.path.join(inps.work_dir, 'run_files'),
                                            work_dir=inps.work_dir, memory=memorymax, walltime=walltimelimit,
                                            queue=queuename)

            putils.remove_zero_size_or_length_error_files(run_file=item)
            putils.rerun_job_if_exit_code_140(run_file=item)
            putils.raise_exception_if_job_exited(run_file=item)
            putils.concatenate_error_files(run_file=item, work_dir=inps.work_dir)
            putils.move_out_job_files_to_stdout(run_file=item)

            date_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d:%H%M%S')
            print(date_str + ' * Job {} completed'.format(item))

        date_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d:%H%M%S')
        print(date_str + ' * all jobs from {} to {} have been completed'.format(os.path.basename(run_file_list[0]),
                                                                                os.path.basename(run_file_list[-1])))

    else:
        for item in run_file_list:
            with open(item, 'r') as f:
                command_lines = f.readlines()
                for command_line in command_lines:
                    os.system(command_line)

    return None


###########################################################################################

if __name__ == "__main__":
    main()
