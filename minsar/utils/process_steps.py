#! /usr/bin/env python3
###############################################################################
#
# Project: process_rsmas.py
# Author: Sara Mirzaee
# Created: 10/2018
#
###############################################################################

import os
import argparse
import shutil
import minsar
import minsar.utils.process_utilities as putils
from minsar.utils.process_utilities import remove_directories, create_or_update_template
from minsar.utils.process_utilities import get_project_name, get_work_directory
from pysar.utils import readfile, utils as ut
from minsar.objects.auto_defaults import PathFind

pathObj = PathFind()
####################################################################

STEP_LIST = [
    'download',
    'process']

STEP_HELP = """Command line options for steps processing with names are chosen from the following list:
{}
In order to use either --start or --dostep, it is necessary that a
previous run was done using one of the steps options to process at least
through the step immediately preceding the starting step of the current run.
""".format(STEP_LIST[0:2])

EXAMPLE = """example: 
  process_rsmas.py  <customTemplateFile>            #run with default and custom templates
  process_rsmas.py  <customTemplateFile>  --submit  #submit as job
  process_rsmas.py  -h / --help                       #help
  process_rsmas.py -g                                 #generate default template (if it does not exist)
  process_rsmas.py -H                                 #print    default template options
  # Run with --start/stop/dostep options
  process_rsmas.py GalapagosSenDT128.template --dostep download    #run at step 'download' only
  process_rsmas.py GalapagosSenDT128.template --end    process  #end after step 'process'
"""


###############################################################################


def create_process_rsmas_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(description='Process Rsmas Routine InSAR Time Series Analysis',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument(
        '--dir',
        dest='work_dir',
        help='topsStack working directory, default is:\n'
             'a) current directory, or\n'
             'b) $SCRATCHDIR/projectName, if meets the following 2 requirements:\n'
             '    2) environmental variable $SCRATCHDIR exists\n'
             '    3) input custom template with basename same as projectName\n')

    parser.add_argument('-H', dest='print_template', action='store_true',
                        help='print the default template file and exit.')
    parser.add_argument(
        '--remove_project_dir',
        dest='remove_project_dir',
        action='store_true',
        help='remove directory before download starts')
    parser.add_argument(
        '--submit',
        dest='submit_flag',
        action='store_true',
        help='submits job')
    parser.add_argument(
        '--walltime',
        dest='wall_time',
        type=str,
        default='48:00',
        help='walltime, e.g. 2:00 (default: 48:00)')

    step = parser.add_argument_group('steps processing (start/end/dostep)', STEP_HELP)
    step.add_argument('--start', dest='startStep', metavar='STEP', default=STEP_LIST[0],
                      help='start processing at the named step, default: {}'.format(STEP_LIST[0]))
    step.add_argument('--end', dest='endStep', metavar='STEP', default=STEP_LIST[-1],
                      help='end processing at the named step, default: {}'.format(STEP_LIST[-1]))
    step.add_argument('--dostep', dest='doStep', metavar='STEP',
                      help='run processing at the named step only')
    return parser


##########################################################################


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    """Command line parser."""
    parser = create_process_rsmas_parser()
    inps = parser.parse_args(args=iargs)
    inps = create_or_update_template(inps)
    inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    # invalid input of custom template
    if inps.customTemplateFile:
        if not os.path.isfile(inps.customTemplateFile):
            raise FileNotFoundError(inps.customTemplateFile)

    if inps.remove_project_dir:
        remove_directories(directories_to_delete=[inps.work_dir])

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)

    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)
 
    # check input --start/end/dostep
    for key in ['startStep', 'endStep', 'doStep']:
        value = vars(inps)[key]
        if value and value not in STEP_LIST:
            msg = 'Input step not found: {}'.format(value)
            msg += '\nAvailable steps: {}'.format(STEP_LIST)
            raise ValueError(msg)

    # ignore --start/end input if --dostep is specified
    if inps.doStep:
        inps.startStep = inps.doStep
        inps.endStep = inps.doStep

    # get list of steps to run
    idx0 = STEP_LIST.index(inps.startStep)
    idx1 = STEP_LIST.index(inps.endStep)
    if idx0 > idx1:
        msg = 'input start step "{}" is AFTER input end step "{}"'.format(inps.startStep, inps.endStep)
        raise ValueError(msg)
    inps.runSteps = STEP_LIST[idx0:idx1 + 1]

    print('Run routine processing with {} on steps: {}'.format(os.path.basename(__file__), inps.runSteps))
    if len(inps.runSteps) == 1:
        print('Remaining steps: {}'.format(STEP_LIST[idx0 + 1:]))

    print('-' * 50)
    return inps


###############################################################################


class RsmasInsar:
    """ Routine processing workflow for time series analysis of small baseline InSAR stacks
    """

    def __init__(self, inps):
        self.customTemplateFile = inps.customTemplateFile
        self.work_dir = inps.work_dir
        self.project_name = inps.project_name
        self.cwd = os.path.abspath(os.getcwd())
        clean_list = pathObj.isce_clean_list()
        for item in clean_list[0:int(inps.template['cleanopt'])]:
            for directory in item:
                if os.path.isdir(os.path.join(self.work_dir, directory)):
                    shutil.rmtree(os.path.join(self.work_dir, directory))
        return

    def run_download_data(self, step_name):
        """ Downloading following data by creating and running run files in pre_run_files folder:
        1- images
        2- DEM
        """
        minsar.create_runfiles.main([self.customTemplateFile, '--step', 'download'])
        minsar.execute_runfiles.main([self.customTemplateFile, '0', '0'])
        return

    def run_process(self, step_name):
        """ Process images from unpacking to making interferograms
        1. create run_files
        2. execute run_files
        """
        minsar.create_runfiles.main([self.customTemplateFile, '--step', 'process'])
        minsar.execute_runfiles.main([self.customTemplateFile])
        return

    def run(self, steps=STEP_LIST):
        # run the chosen steps
        for sname in steps:
            
            print('\n\n******************** step - {} ********************'.format(sname))

            if sname == 'download':
                self.run_download_data(sname)

            elif sname == 'process':
                self.run_process(sname)

        # message
        msg = '\n###############################################################'
        msg += '\nNormal end of Process Rsmas routine InSAR processing workflow!'
        msg += '\n##############################################################'
        print(msg)
        return
