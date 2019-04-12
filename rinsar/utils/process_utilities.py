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
from pysar.utils import utils
from pysar.utils import readfile
from rinsar.objects.rsmas_logging import RsmasLogger, loglevel
import shutil
from collections import namedtuple
from rinsar.objects.dataset_template import Template

from pysar.defaults.auto_path import autoPath
from rinsar.objects import message_rsmas
###############################################################################

logfile_name = os.getenv('OPERATIONS') + '/LOGS/process_rsmas.log'
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
'''
#### More options to be added if required:
#sentinelStack.pairList                    = auto         # [file] file containing pairs to process in each line. auto for None
#sentinelStack.overridePairs               = auto         # [yes, no] override program-generated pairs with the files on the list. auto for no
#sentinelStack.cleanUp                     = auto         # [False, True] Remove fine*int burst fines. auto for False
#sentinelStack.layoverMask                 = auto         # [False, True] Generate layover mask and remove from filtered phase. auto for False
#sentinelStack.waterMask                   = auto         # [False, True] Generate water mask and remove from filtered phase. auto for False
#sentinelStack.virtualFiles                = auto         # [False, True] writing only vrt of merged files (Default: True)
#sentinelStack.forceOverride               = auto         # Force new acquisition override. auto for no


##########################################################################


def send_logger():
    return logger

##########################################################################


def get_project_name(custom_template_file):
    """ Restores project name from custom template file. """

    project_name = None
    if custom_template_file:
        custom_template_file = os.path.abspath(custom_template_file)
        project_name = os.path.splitext(
            os.path.basename(custom_template_file))[0]
        logger.log(loglevel.DEBUG, 'Project name: {}'.format(project_name))

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

def _remove_directories(directories_to_delete):
    """ Removes given existing directories. """

    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    return None
  
##########################################################################

def create_or_update_template(inps):
    """ Creates a default template file and/or updates it.
        returns the values in 'inps'
    """
    print('\n*************** Template Options ****************')
    # write default template
    inps.template_file = create_default_template()
    templateObj = Template(inps.customTemplateFile)
    inps.custom_template = templateObj.get_options()
    inps.template = inps.custom_template
    # Read and update default template with custom input template
    #if not inps.template_file == inps.customTemplateFile:
    #    inps.template = templateObj.update_options_from_file(inps.template_file)

    set_default_options(inps)

    if 'cleanopt' not in inps.custom_template:
        inps.custom_template['cleanopt'] = '0'

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
  
##########################################################################


def create_custom_template(custom_template_file, work_dir):
    """ Creates or restores custom template file. """
  
    if custom_template_file:
        # Copy custom template file to work directory
        if utils.run_or_skip(
                os.path.basename(
                    custom_template_file),
                custom_template_file,
                check_readable=False) == 'run':
            shutil.copy2(custom_template_file, work_dir)

        # Read custom template
        logger.log(loglevel.INFO, 'read custom template file: {}'.format(custom_template_file))
        return readfile.read_template(custom_template_file)
    else:
        return dict()  

##########################################################################


def set_default_options(inps):
    """ Sets default values for template file. """
    
    inps.orbitDir = '$SENTINEL_ORBITS'
    inps.auxDir = '$SENTINEL_AUX'
    
    TemplateTuple = namedtuple(typename='TemplateTuple',
                               field_names=['key', 'inps_name', 'default_value'])

    # Processing methods added by Sara 2018  (values can be: 'sbas', 'squeesar', 'ps'), ps is not
    # implemented yet
    required_template_vals = \
        [TemplateTuple('sentinelStack.subswath', 'subswath', None),
         TemplateTuple('sentinelStack.boundingBox', 'boundingBox', None),
         ]
    optional_template_vals = \
        [TemplateTuple('sentinelStack.slcDir', 'slcDir', inps.work_dir + '/SLC'),
         TemplateTuple('sentinelStack.workingDir', 'workingDir', inps.work_dir),
         TemplateTuple('sentinelStack.master', 'masterDir', None),
         TemplateTuple('sentinelStack.numConnections', 'numConnections', 3),
         TemplateTuple('sentinelStack.numOverlapConnections', 'numOverlapConnections', 3),
         TemplateTuple('sentinelStack.textCmd', 'textCmd', '\'\''),
         TemplateTuple('sentinelStack.excludeDate', 'excludeDate', None),
         TemplateTuple('sentinelStack.includeDate', 'includeDate', None),
         TemplateTuple('sentinelStack.azimuthLooks', 'azimuthLooks', 3),
         TemplateTuple('sentinelStack.rangeLooks', 'rangeLooks', 9),
         TemplateTuple('sentinelStack.filtStrength', 'filtStrength', 0.5),
         TemplateTuple('sentinelStack.esdCoherenceThreshold', 'esdCoherenceThreshold', 0.85),
         TemplateTuple('sentinelStack.snrMisregThreshold', 'snrThreshold', 10),
         TemplateTuple('sentinelStack.unwMethod', 'unwMethod', 'snaphu'),
         TemplateTuple('sentinelStack.polarization', 'polarization', 'vv'),
         TemplateTuple('sentinelStack.coregistration', 'coregistration', 'NESD'),
         TemplateTuple('sentinelStack.workflow', 'workflow', 'interferogram'),
         TemplateTuple('sentinelStack.startDate', 'startDate', None),
         TemplateTuple('sentinelStack.stopDate', 'stopDate', None),
         TemplateTuple('sentinelStack.useGPU', 'useGPU', False),
         TemplateTuple('sentinelStack.processingMethod', 'processingMethod', 'sbas'),
         TemplateTuple('sentinelStack.demMethod', 'demMethod', 'bbox'),
         ]
        
        # TemplateTuple('sentinelStack.pairList', 'ilist', None),
        # TemplateTuple('sentinelStack.overridePairs', 'ilistonly', 'no'),
        # TemplateTuple('sentinelStack.cleanUp', 'cleanup', False),
        # TemplateTuple('sentinelStack.layoverMask', 'layovermsk', False),
        # TemplateTuple('sentinelStack.waterMask', 'watermsk', False),
        # TemplateTuple('sentinelStack.virtualFiles', 'useVirtualFiles', True),
        # TemplateTuple('sentinelStack.forceOverride', 'force', 'no')
          
    # Iterate over required and template values, adding them to `inps`
    for template_val in required_template_vals:
        set_inps_value_from_template(inps, template_key=template_val.key,
                                     inps_name=template_val.inps_name, REQUIRED=True)

    for template_val in optional_template_vals:
        set_inps_value_from_template(inps, template_key=template_val.key,
                                     inps_name=template_val.inps_name,
                                     default_value=template_val.default_value)
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

    if not REQUIRED:
        # Set default value
        inps_dict[inps_name] = default_value
        if template_key in inps.template:
            value = inps.template[template_key]
            if value == default_name:
                # If default name is also set in `template`,
                # set the default value.
                inps_dict[inps_name] = default_value
            else:
                inps_dict[inps_name] = value
    else:
        if template_key in inps.template:
            inps_dict[inps_name] = inps.template[template_key]
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

##########################################################################

def get_job_defaults():
    """ Sets an optimized memory value for each job. """

    import configparser

    config_dir = os.path.expandvars('${RSMAS_INSAR}/rinsar/defaults')
    config_file = os.path.join(config_dir, 'job_defaults.cfg')
    if not os.path.isfile(config_file):
        raise ValueError('job config file NOT found, it should be: {}'.format(config_file))

    config = configparser.ConfigParser(delimiters='=')
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

##########################################################################

def clean_list():
    """ Creates default directory clean list based on cleanopt in template file. """
    """FA 3/19: add workflow as argument, convert to module located in defaults directory """
    
    cleanlist = []
    cleanlist.append([''])
    cleanlist.append(['stack', 'coreg_slaves', 'misreg', 'orbits',
                   'coarse_interferograms', 'ESD', 'interferograms',
                   'slaves', 'geom_master', 'DEM'])
    cleanlist.append(['merged', 'master', 'baselines', 'configs'])
    cleanlist.append(['SLC'])
    cleanlist.append(['PYSAR', 'run_files'])
    
    return cleanlist

###############################################################################

def file_len(fname):
    """Calculate the number of lines in a file."""
    with open(fname, 'r') as file:
        return len(file.readlines())

##########################################################################

def remove_zero_size_or_length_files(directory):
    """Removes files with zero size or zero length (*.e files in run_files)."""
    
    error_files  = glob.glob(directory + '/*.e')
    sort_nicely(error_files)
    for item in error_files:
        if os.path.getsize(item) == 0:       # remove zero-size files
            os.remove(item)
        elif file_len(item) == 0:
            os.remove(item)                  # remove zero-line files
    return None


def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ int(c) if c.isdigit() else c for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)

