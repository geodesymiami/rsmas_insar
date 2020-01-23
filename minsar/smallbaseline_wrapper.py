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
import minsar.job_submission as js
from minsar import email_results
from mintpy import smallbaselineApp
import contextlib

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='smallbaseline_wrapper')

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'smallbaseline_wrapper'
        job_file_name = job_name
        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir)
        sys.exit(0)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    os.chdir(inps.work_dir)

    try:
        with open('out_mintpy.o', 'w') as f:
            with contextlib.redirect_stdout(f):
                smallbaselineApp.main([inps.custom_template_file])
    except:
        with open('out_mintpy.e', 'w') as g:
            with contextlib.redirect_stderr(g):
                smallbaselineApp.main([inps.custom_template_file])

    inps.mintpy_dir = os.path.join(inps.work_dir, pathObj.mintpydir)
    putils.set_permission_dask_files(directory=inps.mintpy_dir)

    # Email Mintpy results
    if inps.email:
        email_results.main([inps.custom_template_file, '--mintpy'] )

    return None

###########################################################################################


if __name__ == "__main__":
    main()


