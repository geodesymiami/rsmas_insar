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
from minsar import email_results
from mintpy import smallbaselineApp

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='smallbaseline_wrapper')

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

        if inps.wall_time == 'None':
            inps.wall_time = config[job_file_name]['walltime']

        job_name = job_file_name

        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, inps.wall_time)
        sys.exit(0)

    os.chdir(inps.work_dir)

    smallbaselineApp.main([inps.customTemplateFile])

    # Email Mintpy results
    if inps.email:
        email_results.main([inps.customTemplateFile])

    return None

###########################################################################################


if __name__ == "__main__":
    main()


