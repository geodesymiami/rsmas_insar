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

###############################################################################

def main(iargs=None):
    start_time = time.time()
    inps = command_line_parse(iargs)

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