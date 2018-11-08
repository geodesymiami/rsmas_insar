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
import sys
import glob
import time
import subprocess
sys.path.insert(0, os.getenv('SSARAHOME'))
from pysar.utils import utils
from pysar.utils import readfile
import argparse
import shutil
import logging
from collections import namedtuple
import password_config as password
from pysar.defaults.auto_path import autoPath
import messageRsmas
###############################################################################
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_formatter = logging.Formatter("%(levelname)s - %(message)s")

# process_rsmas.log File Logging
fileHandler = logging.FileHandler(os.getenv('SCRATCHDIR')+'/process_rsmas.log', 'a+', encoding=None)
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(std_formatter)

# command line logging
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
streamHandler.setFormatter(std_formatter)

logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

###############################################################################

TEMPLATE = '''# vim: set filetype=cfg:
##------------------------ TopsStack_template.txt ------------------------##
## 1. topsStack options

sentinelStack.slcDir                      = auto         # [SLCs dir]
sentinelStack.orbitDir                    = auto         # [/nethome/swdowinski/S1orbits/]
sentinelStack.auxDir                      = auto         # [/nethome/swdowinski/S1aux/]
sentinelStack.workingDir                  = auto         # [/projects/scratch/insarlab/$USER/projname]
sentinelStack.demDir                      = auto         # [DEM file dir]
sentinelStack.master                      = auto         # [Master acquisition]
sentinelStack.numConnections              = auto         # [5] auto for 3
sentinelStack.numOverlapConnections       = auto         # [N of overlap Ifgrams for NESD. Default : 3]
sentinelStack.swathNum                    = None         # [List of swaths. Default : '1 2 3']
sentinelStack.boundingBox                        = None         # [ '-1 0.15 -91.7 -90.9'] required
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
sentinelStack.demMethos                   = auto         # [bbox, ssara]
'''


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
            logger.error('%s is required', template_key)
            raise Exception('ERROR: {0} is required'.format(template_key))


##########################################################################


def set_default_options(inps):
    inps.orbitDir = '/nethome/swdowinski/S1orbits/'
    inps.auxDir = '/nethome/swdowinski/S1aux/'

    # FA: needs fix so that it fails if no subswath is given (None). Same for
    # boundingBox

    # TemplateTuple is a named tuple that takes in parameters to parse from
    # the `template` dictionary
    # 'key' refers to the value in `template`
    # 'inps_name' refers to the name to assign in `inps`
    # 'default_value': The value to assign in `inps` by default
    TemplateTuple = namedtuple(typename='TemplateTuple',
                               field_names=['key', 'inps_name', 'default_value'])

    # Required values have no default value so the last slot is left empty
    # Processing methods added by Sara 2018  (values can be: 'sbas', 'squeesar', 'ps'), ps is not
    # implemented yet
    required_template_vals = \
        [TemplateTuple('sentinelStack.swathNum', 'subswath', None),
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
         TemplateTuple('sentinelStack.demMethod', 'demMethod', 'bbox')
         ]
    print(inps.template)
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


def call_ssara(custom_template_file, slcDir):
    out_file = os.getcwd() + '/' + 'out_download.log'
    download_command = '{python_download_script} ' + custom_template_file + ' |& tee ' + out_file
    command = 'ssh pegasus.ccs.miami.edu ' \
              '\"s.cgood;' \
              'cd ' + slcDir + '; ' + \
              os.getenv('PARENTDIR') + \
              '/sources/rsmas_isce/' + download_command + '\"'

    # Run download script on both scripts
    os.chdir(slcDir)
    for download_file in ['download_ssara_rsmas.py', 'download_asfserial_rsmas.py']:
        messageRsmas.log(command.format(python_download_script = download_file))
        messageRsmas.log(download_command)
        subprocess.Popen(command.format(python_download_script = download_file), shell=True).wait()
    os.chdir('..')


##########################################################################


def call_pysar(custom_template, custom_template_file):

    logger.debug('\n*************** running pysar ****************')
    command = 'pysarApp.py ' + custom_template_file + ' --load-data |& tee out_pysar.log'
    messageRsmas.log(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in pysarApp.py --load-data')
        raise Exception('ERROR in pysarApp.py --load-data')

    # clean after loading data for cleanopt >= 2
    if 'All data needed found' in open('out_pysar.log').read():
        cleanlist = clean_list()
        print('Cleaning files:  ' + str(cleanlist[int(custom_template['cleanopt'])]))
        if int(custom_template['cleanopt']) >= 2:
            _remove_directories(cleanlist[int(custom_template['cleanopt'])])

    command = 'pysarApp.py ' + custom_template_file + ' |& tee -a out_pysar.log'
    messageRsmas.log(command)
    # Check the performance, change in subprocess
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in pysarApp.py')
        raise Exception('ERROR in pysarApp.py')

##########################################################################


def get_project_name(custom_template_file):
    project_name = None
    if custom_template_file:
        custom_template_file = os.path.abspath(custom_template_file)
        project_name = os.path.splitext(
            os.path.basename(custom_template_file))[0]
        logger.debug('Project name: ' + project_name)
    return project_name

##########################################################################


def get_work_directory(work_dir, project_name):
    if not work_dir:
        if autoPath and 'SCRATCHDIR' in os.environ and project_name:
            work_dir = os.getenv('SCRATCHDIR') + '/' + project_name
        else:
            work_dir = os.getcwd()
    work_dir = os.path.abspath(work_dir)
    return work_dir

##########################################################################


def run_or_skip(custom_template_file):
    if os.path.isfile(custom_template_file):
        if os.access(custom_template_file, os.R_OK):
            return 'run'
    else:
        return 'skip'

##########################################################################


def create_custom_template(custom_template_file, work_dir):
    if custom_template_file:
        # Copy custom template file to work directory
        if run_or_skip(custom_template_file) == 'run':
            shutil.copy2(custom_template_file, work_dir)

        # Read custom template
        logger.info('read custom template file: %s', custom_template_file)
        return readfile.read_template(custom_template_file)
    else:
        return dict()

##########################################################################


def create_or_copy_dem(work_dir, template, custom_template_file):
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
            messageRsmas.log(command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                logger.error('ERROR while making DEM')
                raise Exception('ERROR while making DEM')

    # select DEM file (with *.wgs84 or *.dem extension, in that order)
    try:
        files1 = glob.glob(work_dir + '/DEM/*.wgs84')[0]
        files2 = glob.glob(work_dir + '/DEM/*.dem')[0]
        dem_file = [files1, files2]
        dem_file = dem_file[0]
    except BaseException:
        logger.error('No DEM file found (*.wgs84 or *.dem)')
        raise Exception('No DEM file found (*.wgs84 or *.dem)')
    return dem_file

##########################################################################


def create_stack_sentinel_run_files(inps, dem_file):
    inps.demDir = dem_file
    suffix = ''
    extraOptions = ''
    if inps.processingMethod == 'squeesar' or inps.processingMethod == 'ps':
        suffix = '-squeesar'
        extraOptions = ' -P ' + inps.processingMethod

    prefixletters = ['s', 'o', 'a', 'w', 'd', 'm', 'c', 'O', 'n', 'b', 'x', 'i', 'z',
                     'r', 'f', 'e', '-snr_misreg_threshold', 'u', 'p', 'C', 'W',
                     '-start_date', '-stop_date', 't']
    inpsvalue = ['slcDir', 'orbitDir', 'auxDir', 'workingDir', 'demDir', 'masterDir',
                 'numConnections', 'numOverlapConnections', 'subswath', 'boundingBox',
                 'excludeDate', 'includeDate', 'azimuthLooks', 'rangeLooks','filtStrength',
                 'esdCoherenceThreshold', 'snrThreshold', 'unwMethod','polarization',
                 'coregistration', 'workflow', 'startDate', 'stopDate', 'textCmd']

    command = 'stackSentinel_rsmas.py' + suffix + extraOptions
    for value, pref in zip(inpsvalue, prefixletters):
        keyvalue = eval('inps.' + value)
        if keyvalue is not None:
            command = command + ' -' + str(pref) + ' ' + str(keyvalue)

    if inps.useGPU == True:
        command = command + ' -useGPU '

    command = command + ' |& tee out_stackSentinel.log '
    # TODO: Change subprocess call to get back error code and send error code to logger
    logger.info(command)
    messageRsmas.log(command)
    process = subprocess.Popen(
        command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error) = process.communicate()
    if process.returncode is not 0 or error or 'Traceback' in output.decode("utf-8"):
        logger.error(
            'Problem with making run_files using stackSentinel.py')
        raise Exception('ERROR making run_files using stackSentinel.py')

    temp_list = glob.glob('run_files/run_*job')
    for item in temp_list:
        os.remove(item)

    run_file_list = glob.glob('run_files/run_*')
    run_file_list.sort(key=lambda x: int(x.split('_')[2]))

    return run_file_list

##########################################################################


def create_default_template():
    template_file = 'TopsStack_template.txt'
    if not os.path.isfile(template_file):
        logger.info('generate default template file: %s', template_file)
        with open(template_file, 'w') as file:
            file.write(TEMPLATE)
    else:
        logger.info('default template file exists: %s', template_file)
    template_file = os.path.abspath(template_file)
    return template_file

##########################################################################


def get_memory_defaults(inps):
    if inps.workflow == 'interferogram':
        memoryuse = ['3700', '3700', '3700', '4000', '3700', '3700', '5000', '3700', '3700', '3700', '6000', '3700']
    elif inps.workflow == 'slc':
        memoryuse = ['3700', '3700', '3700', '4000', '3700', '3700', '5000', '3700', '3700', '5000', '3700', '3700',
                     '3700']
    return memoryuse

##########################################################################


def run_insar_maps(work_dir):
    hdfeos_file = glob.glob(work_dir + '/PYSAR/S1*.he5')
    hdfeos_file.append(
        glob.glob(
            work_dir +
            '/PYSAR/SUBSET_*/S1*.he5'))  # FA: we may need [0]
    hdfeos_file = hdfeos_file[0]

    json_folder = work_dir + '/PYSAR/JSON'
    mbtiles_file = json_folder + '/' + os.path.splitext(os.path.basename(hdfeos_file))[0] + '.mbtiles'

    if os.path.isdir(json_folder):
        logger.info('Removing directory: %s', json_folder)
        shutil.rmtree(json_folder)

    command1 = 'hdfeos5_2json_mbtiles.py ' + hdfeos_file + ' ' + json_folder + ' |& tee out_insarmaps.log'
    command2 = 'json_mbtiles2insarmaps.py -u ' + password.insaruser + ' -p ' + password.insarpass + ' --host ' + \
               'insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder ' + \
               json_folder + ' --mbtiles_file ' + mbtiles_file + ' |& tee -a out_insarmaps.log'

    with open(work_dir + '/PYSAR/run_insarmaps', 'w') as f:
        f.write(command1 + '\n')
        f.write(command2 + '\n')

    ######### submit job  ################### (FA 6/2018: the second call (json_mbtiles*) does not work yet)
    # command_list=['module unload share-rpms65',command1,command2]
    # submit_insarmaps_job(command_list,inps)

    # TODO: Change subprocess call to get back error code and send error code to logger
    status = subprocess.Popen(command1, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in hdfeos5_2json_mbtiles.py')
        raise Exception('ERROR in hdfeos5_2json_mbtiles.py')

    # TODO: Change subprocess call to get back error code and send error code to logger
    status = subprocess.Popen(command2, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in json_mbtiles2insarmaps.py')
        raise Exception('ERROR in json_mbtiles2insarmaps.py')

##########################################################################

def clean_list():
    cleanlist = []
    cleanlist.append([''])
    cleanlist.append(['baselines', 'stack',
                   'coreg_slaves', 'misreg', 'orbits',
                   'coarse_interferograms', 'ESD', 'interferograms',
                   'slaves', 'master', 'geom_master'])
    cleanlist.append(['merged'])
    cleanlist.append(['SLC'])
    cleanlist.append(['PYSAR'])
    return cleanlist

##########################################################################


def submit_insarmaps_job(command_list, inps):

   projectID = 'insarlab'

   f = open(inps.work_dir+'/PYSAR/insarmaps.job', 'w')
   f.write('#! /bin/tcsh\n')
   f.write('#BSUB -J '+inps.project_name+' \n')
   f.write('#BSUB -o z_insarmaps_%J.o\n')
   f.write('#BSUB -e z_insarmaps_%J.e\n')
   f.write('#BSUB -n 1\n' )
   if projectID:
      f.write('#BSUB -P '+projectID+'\n')
   if inps.wall_time:
      f.write('#BSUB -W inps.wall_time\n')
   f.write('#BSUB -q general\n')

   f.write('cd '+inps.work_dir+'/PYSAR\n')
   for item in command_list:
      f.write(item+'\n')
   f.close()

   job_cmd = 'bsub < insarmaps.job'
   print('bsub job submission')
   os.system(job_cmd)
   sys.exit(0)

##########################################################################

def file_has_zero_lines(fname):
    """Returns True if a file is empty."""
    with open(fname) as f:
        for _ in f.readlines():
            return False
    return True

##########################################################################

def remove_zero_size_or_length_files(directory):
    """Removes files with zero size or zero length (*.e files in run_files)."""
    error_files  = glob.glob(directory + '/*.e')
    for item in error_files:
        if os.path.getsize(item) == 0:       # remove zero-size files
            os.remove(item)
        elif file_has_zero_lines(item):
            os.remove(item)                  # remove zero-line files

##########################################################################

def concatenate_error_files(directory,out_name):
    """Concatenate error files to one file (*.e files in run_files)."""
    """FA 11/2018"""
    error_files  = glob.glob(directory + '/*.e')
    with open(out_name, 'w') as outfile:
        for fname in error_files:
            outfile.write('#########################\n')
            outfile.write('#### '+fname+' \n')
            outfile.write('#########################\n')
            with open(fname) as infile:
                outfile.write(infile.read())

##########################################################################

##########################################################################

def check_error_files_sentinelstack(pattern):

    errorFiles  = glob.glob(pattern)

    elist = []
    for item in errorFiles:
        if os.path.getsize(item) == 0:       # remove zero-size error files
            os.remove(item)
        elif file_has_zero_lines(item):
            os.remove(item)                  # remove zero-lines files
        else:
            elist.append(item)

    # skip non-fatal errors
    error_skip_dict = {'FileExistsError: [Errno 17] File exists:': 'merged/geom_master',
                       'RuntimeWarning: Mean of empty slice': 'warnings.warn'}
    for efile in elist:
        with open(efile) as efr:
            for item in error_skip_dict:
                if item in efr.read() and error_skip_dict[item] in efr.read():
                    sys.stderr.write('Skipped error in: '+efile+'\n')
                else:
                    sys.exit('Error file found: '+efile)

##########################################################################


def _remove_directories(directories_to_delete):
    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)

##########################################################################

def email_pysar_results(textStr, custom_template):
    """
       email results
    """
    if 'email_pysar' not in custom_template:
        return

    cwd = os.getcwd()

    fileList1 = ['velocity.png',\
                 'avgSpatialCoherence.png',\
                 'temporalCoherence.png',\
                 'maskTempCoh.png',\
                 'mask.png',\
                 'demRadar_error.png',\
                 'velocityStd.png',\
                 'geo_velocity.png',\
                 'coherence*.png',\
                 'unwrapPhase*.png',\
                 'rms_timeseriesResidual_quadratic.pdf',\
                 'CoherenceHistory.pdf',\
                 'CoherenceMatrix.pdf',\
                 'bl_list.txt',\
                 'Network.pdf',\
                 'geo_velocity_masked.kmz']

    fileList2 = ['timeseries*.png',\
                 'geo_timeseries*.png']

    if os.path.isdir('PYSAR/PIC'):
       prefix='PYSAR/PIC'

    template_file = glob.glob('PYSAR/INPUTS/*.template')[0]

    i = 0
    for fileList in [fileList1, fileList2]:
       attachmentStr = ''
       i = i + 1
       for fname in fileList:
           fList = glob.glob(prefix+'/'+fname)
           for fileName in fList:
               attachmentStr = attachmentStr+' -a '+fileName

       if i==1 and len(template_file)>0:
          attachmentStr = attachmentStr+' -a '+template_file

       mailCmd = 'echo \"'+textStr+'\" | mail -s '+cwd+' '+attachmentStr+' '+custom_template['email_pysar']
       command = 'ssh pegasus.ccs.miami.edu \"cd '+cwd+'; '+mailCmd+'\"'
       print(command)
       status = subprocess.Popen(command, shell=True).wait()
       if status is not 0:
          sys.exit('Error in email_pysar_results')

###############################################################################

def email_insarmaps_results(custom_template):
    """
       email link to insarmaps.miami.edu
    """
    if 'email_insarmaps' not in custom_template:
      return

    cwd = os.getcwd()

    hdfeos_file = glob.glob('./PYSAR/S1*.he5')
    hdfeos_file = hdfeos_file[0]
    hdfeos_name = os.path.splitext(os.path.basename(hdfeos_file))[0]

    textStr = 'http://insarmaps.miami.edu/start/-0.008/-78.0/8"\?"startDataset='+hdfeos_name

    mailCmd = 'echo \"'+textStr+'\" | mail -s Miami_InSAR_results:_'+os.path.basename(cwd)+' '+custom_template['email_insarmaps']
    command = 'ssh pegasus.ccs.miami.edu \" '+mailCmd+'\"'

    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
       sys.exit('Error in email_insarmaps_results')

