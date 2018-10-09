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
import _process_utilities as putils

###############################################################################


def main(argv):
    start_time = time.time()
    inps = putils.command_line_parse()

    #########################################
    # Initiation
    #########################################

    putils.step_dir(inps, argv)

    #########################################
    # Submit job
    #########################################
    putils.submit_job(sys.argv[:], inps)

    #########################################
    # Read Template Options
    #########################################

    putils.step_template(inps)

    #########################################
    # startssara: Getting Data
    #########################################

    putils.step_ssara(inps)

    #########################################
    # startprocess: create run files
    #########################################

    putils.step_runfiles(inps)

    #########################################
    # startprocess: Execute run files
    #########################################

    putils.step_process(inps)
    # You can separately run this step and execute run files by:
    # "execute_rsmas_run_files.py templatefile starting_run stopping_run"
    # Example for running run 1 2o 4:
    # execute_rsmas_run_files.py $TE/template 1 4

    #########################################
    # running pysar
    #########################################

    putils.step_pysar(inps, start_time)

    #########################################
    # ingesting into insarmaps
    #########################################

    putils.step_insarmaps(inps)

    putils.log_end_message()

if __name__ == '__main__':
    main(sys.argv[:])

