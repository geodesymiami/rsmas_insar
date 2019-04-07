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
from _process_utilities import get_work_directory, get_project_name, send_logger, _remove_directories
import _processSteps as prs
import create_batch as cb
from rsmas_logging import loglevel

logger_process_rsmas = send_logger()

###############################################################################


def process(inps):

    #########################################
    # Initiation
    #########################################
    start_time = time.time()

    inps.project_name = get_project_name(inps.custom_template_file)
    inps.work_dir = get_work_directory(None, inps.project_name)
    inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    if inps.remove_project_dir:
        _remove_directories(directories_to_delete=[inps.work_dir])
    
    if not os.path.isdir(inps.work_dir):
        if os.path.isfile(inps.work_dir):
            os.remove(inps.work_dir)
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)

    #  Read and update template file:
    inps = prs.create_or_update_template(inps)
    if not inps.processingMethod or inps.workflow == 'interferogram':
        inps.processingMethod = 'sbas'

    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)

    command_line = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
    logger_process_rsmas.log(loglevel.INFO, '##### NEW RUN #####')
    logger_process_rsmas.log(loglevel.INFO, command_line)

    #########################################
    # startssara: Getting Data
    #########################################

    # running download scripts:
    #     download_ssara_rsmas.py $TE/template
    #     downlaod_asfserial_rsmas.py $TE/template
    prs.call_ssara(inps.flag_ssara, inps.custom_template_file, inps.slc_dir)
    logger_process_rsmas.log(loglevel.INFO, "Finished call_ssara")

    #########################################
    # startmakerun: create run files
    #########################################

    # create or copy DEM
    # running the script:
    #     dem_rsmas.py $TE/template
    prs.create_or_copy_dem(inps, inps.work_dir, inps.template, inps.custom_template_file)
    logger_process_rsmas.log(loglevel.INFO, "Finished create_or_copy_dem")

    # Check for DEM and create sentinel run files
    # running the script:
    #     create_stacksentinel_run_files.py $TE/template
    prs.create_runfiles(inps)
    logger_process_rsmas.log(loglevel.INFO, "Finished create_run_files")

    #########################################
    # startprocess: Execute run files
    #########################################

    # Running the script:
    #    execute_stacksentinel_run_files.py $TE/template starting_run stopping_run
    #    Example for running run 1 to 4:
    #    execute_stacksentinel_run_files.py $TE/template 1 4
    prs.process_runfiles(inps)
    logger_process_rsmas.log(loglevel.INFO, "Finished process_run_files")

    #########################################
    # startpysar: running PySAR and email results
    #########################################

    if inps.processingMethod == 'squeesar':
        # Run squeesar script:
        #    create_squeesar_run_files.py $TE/template
        #    execute_squeesar_run_files.py $TE/template
        prs.process_time_series(inps)
    else:
        # Run PySAR script:
        #    pysarApp.py $TE/template
        prs.run_pysar(inps, start_time)

    logger_process_rsmas.log(loglevel.INFO, "Finished processing_method")

    # Run ingest insarmaps script and email results
    #    ingest_insarmaps.py $TE/template
    prs.run_ingest_insarmaps(inps)
    logger_process_rsmas.log(loglevel.INFO, "Finished ingest_insarmaps")

    logger_process_rsmas.log(loglevel.INFO, "ingest_insarmaps")

    logger_process_rsmas.log(loglevel.INFO, 'End of process_rsmas')


if __name__ == "__main__":

    inps = prs.command_line_parse()
    
    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'process_rsmas'
        wall_time = '48:00'

        project_name = get_project_name(inps.custom_template_file)
        work_dir = get_work_directory(None, project_name)

        job = cb.submit_script(project_name, job_file_name, sys.argv[:], work_dir, wall_time)

        # run_operations.py needs this print statement for now.
        # This is not for debugging purposes.
        # DO NOT REMOVE.
        print(job)
    else:
        process(inps)
