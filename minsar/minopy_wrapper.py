#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import time
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar import email_results
from minopy import minopyApp
import contextlib

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='minopy_wrapper')

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_obj = JOB_SUBMIT(inps)
        job_name = 'minopy_wrapper'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)

    os.chdir(inps.work_dir)

    try:
        with open('out_minopy.o', 'w') as f:
            with contextlib.redirect_stdout(f):
                smallbaselineApp.main([inps.custom_template_file, '--dir', pathObj.mintpydir])
    except:
        with open('out_minopy.e', 'w') as g:
            with contextlib.redirect_stderr(g):
                smallbaselineApp.main([inps.custom_template_file, '--dir', pathObj.mintpydir])

    inps.mintpy_dir = os.path.join(inps.work_dir, pathObj.mintpydir)
    putils.set_permission_dask_files(directory=inps.mintpy_dir)

    # Email Minopy results
    if inps.email:
        email_results.main([inps.custom_template_file, '--minopy'])

    return None

###########################################################################################


if __name__ == "__main__":
    main()


