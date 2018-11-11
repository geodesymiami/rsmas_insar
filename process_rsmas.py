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

from _process_utilities  import get_work_directory, get_project_name, send_logger
import _processSteps as prs
from rsmas_logging import loglevel

logger  = send_logger()

###############################################################################


if __name__ == "__main__":

    #########################################
    # Initiation
    #########################################

    start_time = time.time()
    inps = prs.command_line_parse()


    inps.project_name = get_project_name(inps.custom_template_file)
    inps.work_dir = get_work_directory(None, inps.project_name)
    inps.slc_dir = os.path.join(inps.work_dir,'SLC')

    #  Read and update template file:
    inps = prs.create_or_update_template(inps)

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)

    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)

    command_line = os.path.basename(inps.custom_template_file)
    logger.log(loglevel.INFO, '##### NEW RUN #####')
    logger.log(loglevel.INFO, 'process_rsmas.py ' + command_line)
    
    #########################################
    # Submit job
    #########################################
    if inps.bsub_flag:
        inps.wall_time='48:00'
    prs.submit_job(sys.argv[:], inps)

    #########################################
    # startssara: Getting Data
    #########################################

    # running download scripts:
    #     download_ssara_rsmas.py $TE/template
    #     downlaod_asfserial_rsmas.py $TE/template

    prs.call_ssara(inps.flag_ssara, inps.custom_template_file, inps.slc_dir)

    #########################################
    # startmakerun: create run files
    #########################################

    # create or copy DEM
    # running the script:
    #     dem_rsmas.py $TE/template

    prs.create_or_copy_dem(inps.work_dir, inps.template, inps.custom_template_file)

    # Check for DEM and create sentinel run files
    # running the script:
    #     create_stacksentinel_run_files.py $TE/template

    prs.create_runfiles(inps)

    #########################################
    # startprocess: Execute run files
    #########################################

    # Running the script:
    #    execute_stacksentinel_run_files.py $TE/template starting_run stopping_run
    #    Example for running run 1 to 4:
    #    execute_stacksentinel_run_files.py $TE/template 1 4

    prs.process_runfiles(inps)

    #########################################
    # startpysar: running PySAR and email results
    #########################################

    # Run PySAR script:
    #    pysarApp.py $TE/template

    prs.run_pysar(inps, start_time)

    # Run ingest insarmaps script and email results
    #    ingest_insarmaps.py $TE/template

    prs.run_ingest_insarmaps(inps)

    logger.log(loglevel.INFO, 'End of process_rsmas')
