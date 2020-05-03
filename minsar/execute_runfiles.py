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
from minsar.job_submission import JOB_SUBMIT

import warnings
# warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore")

##############################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='execute_runfiles')

    os.chdir(inps.work_dir)

    time.sleep(putils.pause_seconds(inps.wait_time))

    inps.out_dir = os.path.join(inps.work_dir, 'run_files')
    job_obj = JOB_SUBMIT(inps)

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'execute_runfiles'
        job_file_name = job_name
        if job_name in sys.argv[0]:
            job_obj.submit_script(job_name, job_file_name, sys.argv[:])
        else:
            Command = [os.path.join(os.path.dirname(sys.argv[0]), 'execute_runfiles.py'),
                       inps.custom_template_file]
            job_obj.submit_script(job_name, job_file_name, Command)
        sys.exit(0)

    run_file_list = putils.read_run_list(inps.work_dir)

    if inps.end_run == 0:
        inps.end_run = len(run_file_list)

    if not inps.start_run == 0:
        inps.start_run = inps.start_run - 1

    if inps.step:
       inps.start_run = inps.step - 1
       inps.end_run = inps.step

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    run_file_list = run_file_list[inps.start_run:inps.end_run]

    for item in run_file_list:

        putils.remove_last_job_running_products(run_file=item)

        job_status = job_obj.submit_batch_jobs(batch_file=item)

        if job_status:

            putils.remove_zero_size_or_length_error_files(run_file=item)
            putils.rerun_job_if_exit_code_140(run_file=item, inps_dict=inps)
            putils.raise_exception_if_job_exited(run_file=item)
            putils.concatenate_error_files(run_file=item, work_dir=inps.work_dir)
            putils.move_out_job_files_to_stdout(run_file=item)

            date_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d:%H%M%S')
            print(date_str + ' * Job {} completed'.format(item))

    date_str = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d:%H%M%S')
    print(date_str + ' * all jobs from {} to {} have been completed'.format(os.path.basename(run_file_list[0]),
                                                                            os.path.basename(run_file_list[-1])))

    return None


###########################################################################################

if __name__ == "__main__":
    main()
