#! /usr/bin/env python3
###############################################################################
#
# Project: Utilities for process_rsmas.py
# Author: Falk Amelung and Sara Mirzaee
# Created: 10/2018
#
###############################################################################

from __future__ import print_function
import os
import glob
import subprocess
import configparser
from pysar.utils import utils
from pysar.utils import readfile
from natsort import natsorted
from rinsar.objects.rsmas_logging import RsmasLogger, loglevel
import shutil
from collections import namedtuple
from rinsar.objects.dataset_template import Template

from pysar.defaults.auto_path import autoPath
from rinsar.objects import message_rsmas

from rinsar.objects.auto_defaults import PathFind
###############################################################################
pathObj = PathFind()
logfile_name = pathObj.logdir + '/process_rsmas.log'
logger = RsmasLogger(file_name=logfile_name)

###############################################################################
TEMPLATE = '''
##------------------------ stackSentinel_template.txt ------------------------##
## 1. stackSentinel options

sentinelStack.slcDir                      = auto         # [SLCs dir]
sentinelStack.orbitDir                    = auto         # [$SENTINEL_ORBITS]
sentinelStack.auxDir                      = auto         # [$SENTINEL_AUX]
sentinelStack.workingDir                  = auto         # [/projects/scratch/insarlab/$USER/projname]
sentinelStack.demDir                      = auto         # [DEM file dir]
sentinelStack.master                      = auto         # [Master acquisition]
sentinelStack.numConnections              = auto         # [5] auto for 3
sentinelStack.numOverlapConnections       = auto         # [N of overlap Ifgrams for NESD. Default : 3]
sentinelStack.subswath                    = None         # [List of swaths. Default : '1 2 3']
sentinelStack.boundingBox                 = None         # [ '-1 0.15 -91.7 -90.9'] required
sentinelStack.textCmd                     = auto         # [eg: source ~/.bashrc]
sentinelStack.excludeDates                = auto         # [20080520,20090817 / no], auto for no
sentinelStack.includeDates                = auto         # [20080520,20090817 / no], auto for all
sentinelStack.azimuthLooks                = auto         # [1 / 2 / 3 / ...], auto for 5
sentinelStack.rangeLooks                  = auto         # [1 / 2 / 3 / ...], auto for 9
sentinelStack.filtStrength                = auto         # [0.0-0.8] auto for 0.3
sentinelStack.esdCoherenceThreshold       = auto         # Coherence threshold for estimating az misreg using ESD. auto for 0.85
sentinelStack.snrMisregThreshold          = auto         # SNR threshold for estimating rng misreg using cross-correlation. auto for 10
sentinelStack.unwMethod                   = auto         # [snaphu icu], auto for snaphu
sentinelStack.polarization                = auto         # SAR data polarization. auto for vv
sentinelStack.coregistration              = auto         # Coregistration options: a) geometry b) NESD. auto for NESD
sentinelStack.workflow                    = auto         # [interferogram / offset / slc / correlation] auto for interferogram
sentinelStack.startDate                   = auto         # [YYYY-MM-DD]. auto for first date available
sentinelStack.stopDate                    = auto         # [YYYY-MM-DD]. auto for end date available
sentinelStack.useGPU                      = auto         # Allow App to use GPU when available [default: False]
sentinelStack.processingMethod            = auto         # [sbas, squeesar, ps]
sentinelStack.demMethod                   = auto         # [bbox, ssara]

#rsmasInsar.processingMethod               = auto         # [smallbaseline, squeesar]
#rsmasInsar.demMethod                      = auto         # [bbox, ssara]

#squeesar.plmethod                         = auto         # [EVD, EMI, PTA, sequential_EVD, sequential_EMI, sequential_PTA]
#squeesar.patch_size                       = auto         # 200
#squeesar.range_window                     = auto         # 21
#squeesar.azimuth_window                   = auto         # 15
#squeesar.cropbox                          = auto         # [ '-1 0.15 -91.7 -90.9'] required [SNEW]

'''

##########################################################################


def send_logger():
    return logger

##########################################################################


def _remove_directories(directories_to_delete):
    """ Removes given existing directories. """

    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    return None


##########################################################################


def get_project_name(custom_template_file):
    """ Restores project name from custom template file. """

    project_name = None
    if custom_template_file:
        project_name = os.path.splitext(
            os.path.basename(custom_template_file))[0]
    return project_name


##########################################################################


def get_work_directory(work_dir, project_name):
    """ Sets the working directory under project name. """

    if not work_dir:
        if autoPath and 'SCRATCHDIR' in os.environ and project_name:
            work_dir = os.getenv('SCRATCHDIR') + '/' + project_name
        else:
            work_dir = os.getcwd()
    work_dir = os.path.abspath(work_dir)

    return work_dir


##########################################################################

def create_or_update_template(inps):
    """ Creates a default template file and/or updates it.
        returns the values in 'inps'
    """
    print('\n*************** Template Options ****************')
    # write default template
    
    inps.project_name = get_project_name(inps.customTemplateFile)
    inps.work_dir = get_work_directory(None, inps.project_name)

    inps.template_file = create_default_template()
    templateObj = Template(inps.customTemplateFile)
    inps.custom_template = templateObj.get_options()

    for key in inps.custom_template:
        inps.custom_template[key] = os.path.expandvars(inps.custom_template[key])

    pathObj.set_isce_defaults(inps)

    inps.template = inps.custom_template

    set_default_options(inps, pathObj)

    del inps.template, inps.custom_template

    return inps


##########################################################################

def create_default_template():
    """ Creates default template file. """

    template_file = 'stackSentinel_template.txt'
    if not os.path.isfile(template_file):
        logger.log(loglevel.INFO, 'generate default template file: {}'.format(template_file))
        with open(template_file, 'w') as file:
            file.write(TEMPLATE)
    else:
        logger.log(loglevel.INFO, 'default template file exists: {}'.format(template_file))
    template_file = os.path.abspath(template_file)

    return template_file
  
#########################################################################


def set_default_options(inps, pathObj):
    """ Sets default values for template file. """
    
    inps.orbitDir = pathObj.orbitdir
    inps.auxDir = pathObj.auxdir

    config_def = get_config_defaults(config_file='template_defaults.cfg')

    default_template_dict = {}
    for each_section in config_def.sections():
        for (each_key, each_val) in config_def.items(each_section):
            default_template_dict.update({each_key: os.path.expandvars(each_val)})

    required_template_vals = pathObj.required_template_options

    for template_key in required_template_vals:
        if not template_key in inps.custom_template:
            logger.log(loglevel.ERROR, '{} is required'.format(template_key))
            raise Exception('ERROR: {0} is required'.format(template_key))


    for template_val in default_template_dict:
        set_inps_value_from_template(inps, template_key=template_val,
                                     inps_name=template_val,
                                     default_value=default_template_dict[template_val])
    return inps

##########################################################################


def set_inps_value_from_template(inps, template_key,
                                 inps_name, default_name='auto',
                                 default_value=None, REQUIRED=False):
    """
    Processes a template parameter and adds it to the inps namespace.
    Options for setting both default values and required parameters
    :param inps: The parsed input namespace
    :param template: The parsed dictionary (namespace)
    :param template_key: The desired key in `template`
    :param inps_name: The parameter name to assign in `inps`
    :param default_name: 'auto' is the normal placeholder
    :param default_value: Default value to assign in `inps`
    :param REQUIRED: Throws error if REQUIRED is True
    :return: None
    """

    # Allows you to refer to and modify `inps` values
    inps_dict = vars(inps)


    key_name = inps_name.split('.')
    try:
        key_name = key_name[1]
    except:
        key_name = key_name[0]

    if default_value == 'None':
        default_value = None


    if not REQUIRED:
        # Set default value
        if not key_name in inps:
            if template_key in inps.custom_template:
                inps_dict[key_name] = inps.custom_template[template_key].strip("'")
            else:
                inps_dict[key_name] = default_value

    else:
        if template_key in inps.template:
            inps_dict[key_name] = inps.template[template_key].strip("'")
        else:
            logger.log(loglevel.ERROR, '{} is required'.format(template_key))
            raise Exception('ERROR: {0} is required'.format(template_key))

##########################################################################


def create_or_copy_dem(work_dir, template, custom_template_file):
    """ Downloads a DEM file or copies an existing one."""

    # if inps.flag_dem:
    dem_dir = work_dir + '/DEM'
    if os.path.isdir(dem_dir) and len(os.listdir(dem_dir)) == 0:
        os.rmdir(dem_dir)

    if not os.path.isdir(dem_dir):
        if 'sentinelStack.demDir' in list(template.keys()) and template['sentinelStack.demDir'] != str('auto'):
            shutil.copytree(template['sentinelStack.demDir'], dem_dir)
        else:
            # TODO: Change subprocess call to get back error code and send error code to logger
            command = 'dem_rsmas.py ' + custom_template_file
            print(command)
            message_rsmas.log(command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                raise Exception('ERROR while making DEM')
    return dem_dir

##########################################################################


def get_config_defaults(config_file='job_defaults.cfg'):
    """ Sets an optimized memory value for each job. """

    config_dir = pathObj.defaultdir
    config_file = os.path.join(config_dir, config_file)
    if not os.path.isfile(config_file):
        raise ValueError('job config file NOT found, it should be: {}'.format(config_file))

    config = configparser.ConfigParser(delimiters='=')
    config.optionxform = str
    config.read(config_file)

    return config


##########################################################################


def run_or_skip(custom_template_file):
    """ Checks if the custom template file exists. """

    if os.path.isfile(custom_template_file):
        if os.access(custom_template_file, os.R_OK):
            return 'run'
    else:
        return 'skip'

###############################################################################


def file_len(fname):
    """Calculate the number of lines in a file."""
    with open(fname, 'r') as file:
        return len(file.readlines())

##########################################################################


def remove_zero_size_or_length_files(directory):
    """Removes files with zero size or zero length (*.e files in run_files)."""
    
    error_files = glob.glob(directory + '/*.e')
    error_files = natsorted(error_files)
    for item in error_files:
        if os.path.getsize(item) == 0:       # remove zero-size files
            os.remove(item)
        elif file_len(item) == 0:
            os.remove(item)                  # remove zero-line files
    return None

############################################################################


def get_slc_list(ssaraopt, slcdir):
    """returns the number of images from ssara command and decides to download new data or not"""

    ssara_opt = ssaraopt.split(' ')
    ssara_call = ['ssara_federated_query-cj.py'] + ssara_opt + ['--print']
    ssara_output = subprocess.check_output(ssara_call)
    ssara_output_array = ssara_output.decode('utf-8').split('\n')
    ssara_output_filtered = ssara_output_array[5:len(ssara_output_array) - 1]

    files_to_check = []
    for entry in ssara_output_filtered:
        files_to_check.append(os.path.join(slcdir, entry.split(',')[-1].split('/')[-1]))

    if os.path.isdir(slcdir):
        SAFE_files = natsorted(glob.glob(os.path.join(slcdir, 'S1*_IW_SLC*')))
    else:
        SAFE_files = []

    if len(SAFE_files) == 0 or not SAFE_files == files_to_check:
        download_flag = True
    else:
        download_flag = False

    return files_to_check, download_flag

############################################################################


def make_run_list(work_dir):
    """ exports run files to a list: run_file_list. """

    run_list = glob.glob(os.path.join(work_dir, pathObj.rundir) + '/run_*')
    run_test = glob.glob(os.path.join(work_dir, pathObj.rundir) + '/run_*')
    for item in run_test:
        test = item.split('/')[-1]
        if test.endswith('.e') or test.endswith('.o') or test.endswith('.job'):
            run_list.remove(item)
    run_list = natsorted(run_list)
    return run_list

############################################################################


def read_run_list(work_dir):
    """ reads from run_file_list. """

    runfiles = os.path.join(work_dir, 'run_files_list')
    run_file_list = []
    with open(runfiles, 'r') as f:
        new_f = f.readlines()
    for line in new_f:
        run_file_list.append('run_files/' + line.split('/')[-1][:-1])

    return run_file_list

