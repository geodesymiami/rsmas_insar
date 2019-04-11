#! /usr/bin/env python3
###############################################################################
#
# Project: process_rsmas.py
# Author: Sara Mirzaee
# Created: 10/2018
#
###############################################################################
# Backwards compatibility for Python 2
from __future__ import print_function

import os
import sys
import time
from rinsar.objects import messageRsmas
from rinsar.utils.process_steps import RsmasInsar, command_line_parse
from rinsar.utils.process_utilities import get_work_directory, get_project_name
import rinsar.create_batch as cb
###############################################################################

def main(iargs=None):
    start_time = time.time()
    inps = command_line_parse(iargs)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'process_rsmas'
        wall_time = '48:00'

        project_name = get_project_name(inps.customTemplateFile)
        work_dir = get_work_directory(None, project_name)

        job = cb.submit_script(project_name, job_file_name, sys.argv[:], work_dir, wall_time)

    else:
        command_line = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
        messageRsmas.log('##### NEW RUN #####')
        messageRsmas.log(command_line)

        objInsar = RsmasInsar(inps.customTemplateFile, inps.work_dir)
        objInsar.startup()
        objInsar.run(steps=inps.runSteps)

    # Timing
    m, s = divmod(time.time() - start_time, 60)
    print('\nTotal time: {:02.0f} mins {:02.1f} secs'.format(m, s))
    return


###########################################################################################
if __name__ == '__main__':
    main()