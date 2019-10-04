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
import shutil
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
      process_rsmas.py  <custom_template_file>              # run with default and custom templates
      process_rsmas.py  <custom_template_file>  --submit    # submit as job
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
    template_file = pathObj.auto_template
    # print default template
    if inps.print_template:
        raise SystemExit(open(template_file, 'r').read())
    inps = putils.create_or_update_template(inps)

    return inps


def main(iargs=None):

    start_time = time.time()

    inps = process_rsmas_cmd_line_parse(iargs)

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
    if inps.custom_template_file:
        if not os.path.isfile(inps.custom_template_file):
            raise FileNotFoundError(inps.custom_template_file)

    if inps.remove_project_dir:
        putils.remove_directories(directories_to_delete=[inps.work_dir])

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)

    os.chdir(inps.work_dir)

    inps.slc_dir = os.path.join(inps.work_dir, 'SLC')
    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)

    # check input --start/end/step
    for key in ['start_step', 'end_step', 'step']:
        value = vars(inps)[key]
        if value and value not in step_list:
            msg = 'Input step not found: {}'.format(value)
            msg += '\nAvailable steps: {}'.format(step_list)
            raise ValueError(msg)

    # ignore --start/end input if --step is specified
    if inps.step:
        inps.start_step = inps.step
        inps.end_step = inps.step

    # get list of steps to run
    idx0 = step_list.index(inps.start_step)
    idx1 = step_list.index(inps.end_step)

    if idx0 > idx1:
        msg = 'input start step "{}" is AFTER input end step "{}"'.format(inps.start_step, inps.end_step)
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
        self.custom_template_file = inps.custom_template_file
        self.work_dir = inps.work_dir
        self.project_name = inps.project_name
        self.template = inps.template
        self.image_products_flag = inps.template['image_products_flag']
        self.insarmaps_flag = inps.template['insarmaps_flag']

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

        minsar.download_rsmas.main([self.custom_template_file])
        return

    def run_download_dem(self):
        """ Downloading DEM using dem_rsmas.py script.
        """
        minsar.dem_rsmas.main([self.custom_template_file, self.dem_flag])
        return

    def run_interferogram(self):
        """ Process images from unpacking to making interferograms using ISCE
        1. create run_files
        2. execute run_files
        """
        try:
            minsar.create_runfiles.main([self.custom_template_file])
        except:
            print('Skip creating run files ...')
        minsar.execute_runfiles.main([self.custom_template_file])
        return

    def run_timeseries(self):
        """ Process smallbaseline using MintPy or non-linear inversion using MiNoPy and email results
        """
        if self.method == 'mintpy':
            minsar.smallbaseline_wrapper.main([self.custom_template_file, '--email'])
        else:
            import minsar.minopy_wrapper as minopy_wrapper
            minopy_wrapper.main([self.custom_template_file])
        return

    def run_insarmaps(self):
        """ prepare outputs for insarmaps website.
        """
        if self.insarmaps_flag:
            minsar.ingest_insarmaps.main([self.custom_template_file, '--email'])
        else:
            print('insarmaps step is off (insarmaps_flag in template is False)')
        return

    def run_image_products(self):
        """ create ortho/geo-rectified products.
        """
        if self.image_products_flag == 'True':
            minsar.export_ortho_geo.main([self.custom_template_file])
        else:
            print('imageProducts step is off (image_products_flag in template is False)')
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

            elif sname == 'timeseries':
                self.run_timeseries()

            elif sname == 'insarmaps':
                self.run_insarmaps()

            elif sname == 'imageProducts':
                self.run_image_products()

        # message
        msg = '\n###############################################################'
        msg += '\nNormal end of Process Rsmas routine InSAR processing workflow!'
        msg += '\n##############################################################'
        print(msg)
        return

###########################################################################################


if __name__ == '__main__':
    main()
