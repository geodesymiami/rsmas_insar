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
import rain
import rain.utils.process_utilities as putils
from rain.utils.process_utilities import _remove_directories, clean_list
from rain.utils.process_utilities import get_project_name, get_work_directory
from pysar.utils import readfile, utils as ut

####################################################################

STEP_LIST = [
    'download',
    'proc_image',
    'timeseries',
]

STEP_HELP = """Command line options for steps processing with names are chosen from the following list:
{}
In order to use either --start or --dostep, it is necessary that a
previous run was done using one of the steps options to process at least
through the step immediately preceding the starting step of the current run.
""".format(STEP_LIST[0:3])

EXAMPLE = """example: 
  process_rsmas.py  <customTemplateFile>            #run with default and custom templates
  process_rsmas.py  <customTemplateFile>  --submit  #submit as job
  process_rsmas.py  -h / --help                       #help
  process_rsmas.py -g                                 #generate default template (if it does not exist)
  process_rsmas.py -H                                 #print    default template options
  # Run with --start/stop/dostep options
  process_rsmas.py GalapagosSenDT128.template --dostep download    #run at step 'download' only
  process_rsmas.py GalapagosSenDT128.template --end    proc_image  #end after step 'proc_image'
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
        help='sentinelStack working directory, default is:\n'
             'a) current directory, or\n'
             'b) $SCRATCHDIR/projectName, if meets the following 2 requirements:\n'
             '    2) environmental variable $SCRATCHDIR exists\n'
             '    3) input custom template with basename same as projectName\n')
    parser.add_argument(
        '-g', '--generateTemplate',
        dest='generate_template',
        action='store_true',
        help='Generate default template (and merge with custom template), then exit.')
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

    inps.project_name = get_project_name(inps.customTemplateFile)
    inps.work_dir = get_work_directory(None, inps.project_name)
    inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    if inps.remove_project_dir:
        _remove_directories(directories_to_delete=[inps.work_dir])

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)

    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)

    template_file = os.path.join(os.getenv('PARENTDIR'), 'rain/defaults/rsmas_insar_template.txt')
    # generate default template
    if inps.generate_template:
        dest_file = os.path.join(os.getcwd(), os.path.basename(template_file))
        if not os.path.isfile(dest_file):
            print('copy default template file {} to the current directory'.format(template_file))
            shutil.copy2(template_file, os.getcwd())
        else:
            print('default template file exists in current directory: {}, skip.'.format(dest_file))
        raise SystemExit()

    # print default template
    if inps.print_template:
        raise SystemExit(open(template_file, 'r').read())

    if not inps.customTemplateFile and not os.path.isfile(os.path.basename(template_file)):
        parser.print_usage()
        print(EXAMPLE)
        msg = "ERROR: no template file found! It requires:"
        msg += "\n  1) input a custom template file, OR"
        msg += "\n  2) there is a default template 'pysarApp_template.txt' in current directory."
        print(msg)
        raise SystemExit()

    # invalid input of custom template
    if inps.customTemplateFile:
        if not os.path.isfile(inps.customTemplateFile):
            raise FileNotFoundError(inps.customTemplateFile)
        elif os.path.basename(inps.customTemplateFile) == os.path.basename(template_file):
            # ignore if pysarApp_template.txt is input as custom template
            inps.customTemplateFile = None

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

    def __init__(self, customTemplateFile=None, work_dir=None):
        self.customTemplateFile = customTemplateFile
        self.work_dir = work_dir
        self.cwd = os.path.abspath(os.getcwd())
        return

    def startup(self):
        """The starting point of the workflow. It runs everytime.
        It 1) grab project name if given
           2) grab and go to work directory
           3) get and read template(s) options
        """
        # 1. Get projectName
        self.project_name = putils.get_project_name(self.customTemplateFile)
        print('Project name:', self.project_name)

        # 2. Go to the work directory
        # 2.1 Get work_dir
        self.work_dir = putils.get_work_directory(None, self.project_name)

        # 3. Read templates
        # 3.1 Get default template file
        lfile = os.path.join(os.getenv('PARENTDIR'), 'rain/defaults/rsmas_insar_template.txt')  # latest version
        cfile = os.path.join(self.work_dir, 'rsmas_insar_template.txt')  # current version
        if not os.path.isfile(cfile):
            print('copy default template file {} to work directory'.format(lfile))
            shutil.copy2(lfile, self.work_dir)
        else:
            # cfile is obsolete if any key is missing
            ldict = readfile.read_template(lfile)
            cdict = readfile.read_template(cfile)
            if any([key not in cdict.keys() for key in ldict.keys()]):
                print('obsolete default template detected, update to the latest version.')
                shutil.copy2(lfile, self.work_dir)
                # keep the existing option value from obsolete template file
                template_file = ut.update_template_file(cfile, cdict)
        self.templateFile = cfile

        # 3.2 read (custom) template files into dicts
        self._read_template()
        return

    def _read_template(self):
        # read custom template, to:
        # 1) update default template
        # 2) add metadata to ifgramStack file and HDF-EOS5 file
        self.customTemplate = None
        if self.customTemplateFile:
            cfile = self.customTemplateFile

            # Read custom template
            print('read custom template file:', cfile)
            cdict = readfile.read_template(cfile)

            # correct some loose type errors
            standardValues = {'def': 'auto', 'default': 'auto',
                              'y': 'yes', 'on': 'yes', 'true': 'yes',
                              'n': 'no', 'off': 'no', 'false': 'no'
                              }
            for key, value in cdict.items():
                if value in standardValues.keys():
                    cdict[key] = standardValues[value]

            if 'cleanopt' not in cdict.keys():
                cdict['cleanopt'] = '0'

            self.customTemplate = dict(cdict)

            # Update default template file based on custom template
            print('update default template based on input custom template')
            self.templateFile = ut.update_template_file(self.templateFile, self.customTemplate)

        print('read default template file:', self.templateFile)
        self.template = readfile.read_template(self.templateFile)
        self.template = ut.check_template_auto_value(self.template)

        return

    def run_download_data(self, step_name):
        """ Downloading following data by creating and running run files in pre_run_files folder:
        1- images
        2- DEM
        """
        rain.create_runfiles.main([self.customTemplateFile, '--step', 'preprocess'])
        rain.execute_pre_runfiles.main([self.customTemplateFile])
        return

    def run_process_images(self, step_name):
        """ Process images from unpacking to making interferograms
        1. create run_files
        2. execute run_files
        """
        rain.create_runfiles.main([self.customTemplateFile, '--step', 'mainprocess'])
        rain.execute_runfiles.main([self.customTemplateFile])
        return

    def run_timeseries_and_insarmaps(self, step_name):
        """ Do the
        1 - create post_run_files
        1 - inversion either via small baseline or squeesar
        2 - corrections with PySAR
        """
        rain.create_runfiles.main([self.customTemplateFile, '--step', 'postprocess'])
        rain.execute_post_runfiles.main([self.customTemplateFile])
        return

    def run(self, steps=STEP_LIST):
        # run the chosen steps
        for sname in steps:
            status = 0
            print('\n\n******************** step - {} ********************'.format(sname))

            if sname == 'download':
                self.run_download_data(sname)

            elif sname == 'proc_image':
                self.run_process_images(sname)

            elif sname == 'timeseries':
                self.run_timeseries_and_insarmaps(sname)

        # message
        msg = '\n###############################################################'
        msg += '\nNormal end of Process Rsmas routine InSAR processing workflow!'
        msg += '\n##############################################################'
        print(msg)
        return
