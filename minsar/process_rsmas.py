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
import argparse
import minsar
import minsar.workflow
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
from minsar.objects.auto_defaults import PathFind

pathObj = PathFind()
step_list, step_help = pathObj.process_rsmas_help()
###############################################################################

EXAMPLE = """example:
      process_rsmas.py  <customTemplateFile>              # run with default and custom templates
      process_rsmas.py  <customTemplateFile>  --submit    # submit as job
      process_rsmas.py  -h / --help                       # help 
      process_rsmas.py  -H                                # print    default template options
      # Run with --start/stop/step options
      process_rsmas.py GalapagosSenDT128.template --step  download        # run the step 'download' only
      process_rsmas.py GalapagosSenDT128.template --start download        # start from the step 'download' 
      process_rsmas.py GalapagosSenDT128.template --stop  ifgrams         # end after step 'interferogram'
    """


def process_rsmas_cmd_line_parse(iargs=None):
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(description='Process Rsmas Routine InSAR Time Series Analysis',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser = putils.add_common_parser(parser)
    parser = putils.add_process_rsmas(parser)
    inps = parser.parse_args(args=iargs)
    inps = putils.create_or_update_template(inps)

    return inps


def main(iargs=None):

    start_time = time.time()

    inps = process_rsmas_cmd_line_parse(iargs)

    template_file = pathObj.auto_template

    # print default template
    if inps.print_template:
        raise SystemExit(open(template_file, 'r').read())

    inps = check_directories_and_inputs(inps)

    command_line = os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1:])
    message_rsmas.log(inps.work_dir, '##### NEW RUN #####')
    message_rsmas.log(inps.work_dir, command_line)

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    job_file_name = 'process_rsmas'
    if inps.wall_time == 'None':
        inps.wall_time = config[job_file_name]['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job = js.submit_script(inps.project_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)
        # run_operations.py needs this print statement for now.
        # This is not for debugging purposes.
        # DO NOT REMOVE.
        print(job)

    else:
        time.sleep(wait_seconds)

        objInsar = RsmasInsar(inps)
        objInsar.run(steps=inps.runSteps)

    # Timing
    m, s = divmod(time.time() - start_time, 60)
    print('\nTotal time: {:02.0f} mins {:02.1f} secs'.format(m, s))
    return

###########################################################################################


def check_directories_and_inputs(inputs):

    inps = inputs

    # invalid input of custom template
    if inps.customTemplateFile:
        if not os.path.isfile(inps.customTemplateFile):
            raise FileNotFoundError(inps.customTemplateFile)

    if inps.remove_project_dir:
        putils.remove_directories(directories_to_delete=[inps.work_dir])

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)

    os.chdir(inps.work_dir)

    inps.slc_dir = os.path.join(inps.work_dir, 'SLC')
    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)

    # check input --start/end/step
    for key in ['startStep', 'endStep', 'step']:
        value = vars(inps)[key]
        if value and value not in step_list:
            msg = 'Input step not found: {}'.format(value)
            msg += '\nAvailable steps: {}'.format(step_list)
            raise ValueError(msg)

    # ignore --start/end input if --step is specified
    if inps.step:
        inps.startStep = inps.step
        inps.endStep = inps.step

    # get list of steps to run
    idx0 = step_list.index(inps.startStep)
    idx1 = step_list.index(inps.endStep)

    if idx0 > idx1:
        msg = 'input start step "{}" is AFTER input end step "{}"'.format(inps.startStep, inps.endStep)
        raise ValueError(msg)
    inps.runSteps = step_list[idx0:idx1 + 1]

    print('Run routine processing with {} on steps: {}'.format(os.path.basename(__file__), inps.runSteps))
    if len(inps.runSteps) == 1:
        print('Remaining steps: {}'.format(step_list[idx0 + 1:]))

    print('-' * 50)

    return inps

###########################################################################################


class RsmasInsar:
    """ Routine processing workflow for time series analysis of small baseline InSAR stacks
    """

    def __init__(self, inps):
        self.customTemplateFile = inps.customTemplateFile
        self.work_dir = inps.work_dir
        self.project_name = inps.project_name
        self.template = inps.template

        if 'demMethod' in inps.template and inps.template['demMethod'] == 'boundingBox':
            self.dem_flag = '--boundingBox'
        else:
            self.dem_flag = '--ssara'

        if inps.template['processingMethod'] == 'smallbaseline':
            self.method = 'mintpy'
        else:
            self.method = 'minopy'

        return

    def run_download_data(self):
        """ Downloading images using download_rsmas.py script.
        """

        clean_list = pathObj.isce_clean_list()
        for item in clean_list[0:int(self.template['cleanopt'])]:
            for directory in item:
                if os.path.isdir(os.path.join(self.work_dir, directory)):
                    shutil.rmtree(os.path.join(self.work_dir, directory))

        minsar.download_rsmas.main([self.customTemplateFile])
        return

    def run_download_dem(self):
        """ Downloading DEM using dem_rsmas.py script.
        """
        minsar.dem_rsmas.main([self.customTemplateFile, self.dem_flag])
        return

    def run_interferogram(self):
        """ Process images from unpacking to making interferograms using ISCE
        1. create run_files
        2. execute run_files
        """
        minsar.create_runfiles.main([self.customTemplateFile])
        minsar.execute_runfiles.main([self.customTemplateFile])
        return

    def run_mintpy(self):
        """ Process smallbaseline using MintPy or non-linear inversion using MiNoPy and email results
        """
        if self.method == 'mintpy':
            minsar.smallbaseline_wrapper.main([self.customTemplateFile, '--email'])
        else:
            import minsar.minopy_wrapper as minopy_wrapper
            minopy_wrapper.main([self.customTemplateFile])
        return

    def run_insarmaps(self):
        """ prepare outputs for insarmaps website.
        """
        minsar.ingest_insarmaps.main([self.customTemplateFile, '--email'])
        return

    def run_geocode(self):
        """ create ortho/geo-rectified products.
        """
        minsar.export_ortho_geo.main([self.customTemplateFile])
        return

    def run(self, steps=step_list):
        # run the chosen steps
        for sname in steps:

            print('\n\n******************** step - {} ********************'.format(sname))

            if sname == 'download':
                self.run_download_data()

            elif sname == 'dem':
                self.run_download_dem()

            elif sname == 'ifgrams':
                self.run_interferogram()

            elif sname == 'mintpy':
                self.run_mintpy()

            elif sname == 'insarmaps':
                self.run_insarmaps()

            elif sname == 'geocode':
                self.run_geocode()

        # message
        msg = '\n###############################################################'
        msg += '\nNormal end of Process Rsmas routine InSAR processing workflow!'
        msg += '\n##############################################################'
        print(msg)
        return

###########################################################################################


if __name__ == '__main__':
    main()
