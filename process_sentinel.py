#! /usr/bin/env python3 
###############################################################################
#   
# Project: process_sentinel.py
# Purpose: runs H Fattahi's sentinelStack code
# Author: Falk Amelung
# Created: 1/2018
#
###############################################################################
# Backwards compatibility for Python 2
from __future__ import print_function

import os
import sys
import glob
import time
import argparse
import shutil
import subprocess
import json
from collections import namedtuple

import h5py
import logging

#import my_logger
import __init__

#print(os.path.abspath("./PySAR"))
#sys.path.append(os.path.abspath("./PySAR"))

import pysar
from pysar.utils import utils
from pysar.utils import readfile
from pysar.defaults.auto_path import autoPath

import messageRsmas
from _process_utilities import email_pysar_results
from _process_utilities import email_insarmaps_results
from _process_utilities import submit_job
from _process_utilities import submit_insarmaps_job
from _process_utilities import check_error_files_sentinelstack

logger = logging.getLogger("process_sentinel")

###############################################################################
TEMPLATE = '''# vim: set filetype=cfg:
##------------------------ sentinelStack_template.txt ------------------------##
## 1. sentinelStack options
sentinelStack.slcDir         = auto  #[SLC]
sentinelStack.orbitDir       = auto  #[orbits]
sentinelStack.auxDir         = auto  #[/nethome/swdowinski/S1aux/]
sentinelStack.orbitDir       = auto  #[/nethome/swdowinski/S1orbits/]
sentinelStack.boundingBox    = None  #[ '-1 0.15 -91.7 -90.9'] required
sentinelStack.subswath       = None  #[1 / 2 / '1 2' / '1 2 3']  required
sentinelStack.workflow       = auto  #[interferogram / offset / slc / correlation] auto for interferogram
sentinelStack.numConnections = auto  #[5] auto for 3
sentinelStack.coregistration = auto  #[NESD / geometry], auto for NESD
sentinelStack.azimuthLooks   = auto  #[1 / 2 / 3 / ...], auto for 5
sentinelStack.rangeLooks     = auto  #[1 / 2 / 3 / ...], auto for 15
sentinelStack.filtStrength   = auto  #[0.0-0.8] auto for 0.3
sentinelStack.excludeDate    = auto  #[20080520,20090817 / no], auto for no
sentinelStack.unwMethod      = auto  #[snaphu ice], auto for snaphu
sentinelStack.ProcessingMethod = auto #[sbas, squeesar, ps]
'''

EXAMPLE = '''example:
  process_sentinelStack.py  DIR/TEMPLATEFILE [options] [--bsub]

  Sentinel InSAR processing using sentinelStack and RSMAS processing scripts

  Process directory is /projects/scratch/insarlab/famelung. Can be adjusted e.g. with TESTBENCH1,2,3 alias
  options given on command line overrides the templatefile (not verified)

  --startprocess       skips data downloading using SSARA
  --startpysar         skips InSAR processing (needs a 'merged' directory)
  --startinsarmaps     skips pysar  processing (needs a PYSAR directory)
  --startjobstats      skips insarmaps processing (summarizes job statistics)
  --stopsara           stops after ssara
  --stopprocess        stops after process
  --stoppysar          stops after time series analysis
  --stopinsarmaps      stops after insarmaps upload
  --startssara         [default]

  --insarmaps          append after other options to upload to insarmaps.miami.edu
  --bsub               submits job using bsub (and send email when done)
  --nomail             suppress emailing imagefiles of results (default is emailing)
  --restart            removes project directory before starting download

  --latest             use earthdef.caltech SVN version (3rdpary/sentinelstack) (default: source/sentinelStack)

    e.g:  process_rsmas.pl $SAMPLESDIR/WellquakeT399EnvD2.template

  e.g.:  process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startssara
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopssara
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startprocess
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopprocess
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startpysar
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stoppysar
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startinsarmaps  : for ingestion into insarmaps
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopinsarmaps

  # Generate template file:
         process_sentinelStack.py -g
         process_sentinelStack.py $SAMPLESDIR/GalapagosT128SenVVD.template -g

         cleanopt in TEMPLATEFILE controls file removal [default=0]
             cleanopt = 0 :  none
             cleanopt = 1 :  after sentinelStack: configs, baselines, stack, coreg_slaves, misreg, orbits, coarse_interferograms, ESD, interferograms
             cleanopt = 2 :  after pysarApp.py --load_data: 'merged'
             cleanopt = 3 :  after pysarApp.py --load_data: 'SLC'
             cleanopt = 4 :  everything including PYSAR 

  --------------------------------------------
  Open sentinelStack_template.txt file for details.
  --------------------------------------------
'''

UM_FILE_STRUCT = '''
    scratch/                 # $SCRATCHDIR defined in environmental variable
        GalapagosT128SenVVD/ # my_projectName, same as the basename of template file
            DEM/             # DEM file(s) (for topographic phase and geocode)
            merged/          # processing results merged/geom_master merged/interferograms merged/SLC
'''

##########################################################################


def create_process_sentinel_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s 0.1')
    parser.add_argument('custom_template_file', nargs='?',
        help='custom template with option settings.\n')
    parser.add_argument(
        '--dir',
        dest='work_dir',
        help='sentinelStack working directory, default is:\n'
             'a) current directory, or\n'
             'b) $SCRATCHDIR/projectName, if meets the following 3 requirements:\n'
             '    1) miami_path = True in pysar/__init__.py\n'
             '    2) environmental variable $SCRATCHDIR exists\n'
             '    3) input custom template with basename same as projectName\n')
    parser.add_argument(
        '-g', '--generateTemplate',
        dest='generate_template',
        action='store_true',
        help='Generate default template (and merge with custom template), then exit.')
    parser.add_argument(
        '--stopssara',
        dest='stopssara',
        action='store_true',
        help='exit after running ssara_federated_query in SLC directory')
    parser.add_argument(
        '--startprocess',
        dest='startprocess',
        action='store_true',
        help='process using sentinelstack package')
    parser.add_argument(
        '--stopprocess',
        dest='stopprocess',
        action='store_true',
        help='exit after running sentineStack')
    parser.add_argument(
        '--startpysar',
        dest='startpysar',
        action='store_true',
        help='run pysar')
    parser.add_argument(
        '--stoppysar',
        dest='stoppysar',
        action='store_true',
        help='exit after running pysar')
    parser.add_argument(
        '--startinsarmaps',
        dest='startinsarmaps',
        action='store_true',
        help='ingest into insarmaps')
    parser.add_argument(
        '--stopinsarmaps',
        dest='stopinsarmaps',
        action='store_true',
        help='exit after ingesting into insarmaps')
    parser.add_argument(
        '--insarmaps',
        dest='flag_insarmaps',
        action='store_true',
        help='ingest into insarmaps')
    parser.add_argument(
        '--latest',
        dest='flag_latest_version',
        action='store_true',
        help='use sentinelStack version from caltech svn')
    parser.add_argument(
        '--nomail',
        dest='flag_mail',
        action='store_false',
        help='mail results')
    parser.add_argument(
        '--bsub',
        dest='bsub_flag',
        action='store_true',
        help='submits job using bsub')

    return parser


def command_line_parse():
    """

    :return: returns inputs from the command line as a parsed object
    """
    parser = create_process_sentinel_parser()

    inps = parser.parse_args()
    if inps.custom_template_file and os.path.basename(
            inps.custom_template_file) == 'sentinelStack_template.txt':
        inps.custom_template_file = None

    # option processing. Same as in process_rsmas.pl. Can run every portion individually
    # need --insarmaps option so that it is run
    inps.startssara = True
    inps.flag_ssara = False
    inps.flag_process = False
    inps.flag_pysar = False    # inps.flag_insarmaps is True only if --insarmaps

    if inps.startprocess:
        inps.flag_process = True
        inps.flag_pysar = True
        inps.startssara = False
    if inps.startpysar:
        inps.flag_pysar = True
        inps.startssara = False
    if inps.startinsarmaps:
        inps.startssara = False
        inps.flag_insarmaps = True
    if inps.startssara:
        inps.flag_ssara = True
        inps.flag_process = True
        inps.flag_pysar = True

    logger.debug('flag_ssara:     %s', inps.flag_ssara)
    logger.debug('flag_process:   %s', inps.flag_process)
    logger.debug('flag_pysar:     %s', inps.flag_pysar)
    logger.debug('flag_insarmaps: %s', inps.flag_insarmaps)
    logger.debug('flag_mail:      %s', inps.flag_mail)
    logger.debug('flag_latest_version:   %s', inps.flag_latest_version)
    logger.debug('stopssara:      %s', inps.stopssara)
    logger.debug('stopprocess:    %s', inps.stopprocess)
    logger.debug('stoppysar:      %s', inps.stoppysar)

    return inps


def _remove_directories(directories_to_delete):
    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)


def set_inps_value_from_template(inps, template, template_key,
                                 inps_name, default_name = 'auto', 
                                 default_value = None, REQUIRED = False):
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
        if template_key in template:
            value = template[template_key]
            if value == default_name:
                # If default name is also set in `template`,
                # set the default value.
                inps_dict[inps_name] = default_value
            else:
                inps_dict[inps_name] = value
    else:
        if template_key in template:
            inps_dict[inps_name] = template[template_key]
        else:
            logger.error('%s is required', template_key)
            raise Exception('ERROR: {0} is required'.format(template_key))
   

def set_default_options(inps, template):

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
            field_names= ['key', 'inps_name', 'default_value'])

    # Required values have no default value so the last slot is left empty
    # Processing methods added by Sara 20/2018  (values can be: 'sbas', 'squeesar', 'ps'), ps is not
    # implemented yet
    required_template_vals = \
        [ TemplateTuple('sentinelStack.subswath', 'subswath', None),
          TemplateTuple('sentinelStack.boundingBox', 'boundingBox', None)
        ]
    optional_template_vals = \
        [ TemplateTuple('sentinelStack.slcDir', 'slcDir', inps.work_dir + '/SLC'),
          TemplateTuple('sentinelStack.workflow', 'workflow', 'interferogram'),
          TemplateTuple('sentinelStack.azimuthLooks', 'azimuthLooks', 3),
          TemplateTuple('sentinelStack.filtStrength', 'filtStrength', 0.5),
          TemplateTuple('sentinelStack.rangeLooks', 'rangeLooks', 15),
          TemplateTuple('sentinelStack.numConnections', 'numConnections', 3),
          TemplateTuple('sentinelStack.excludeDate', 'excludeDate', None),
          TemplateTuple('sentinelStack.unwMethod', 'unwMethod', 'icu'),
          TemplateTuple('sentinelStack.coregistration', 'coregistration', 'NESD'),
          TemplateTuple('sentinelStack.ProcessingMethod', 'ProcessingMethod', 'sbas')
          # #FA 3/18: was not taken into account in DEM generation: may need to check wherther
          # key = 'sentinelStack.dem_dir' # sentinelStack.dem_dir is False
          # TemplateTuple('sentinelStack.dem_dir', 'dem_dir', 'False')
        ]
    print(template)
    # Iterate over required and template values, adding them to `inps`
    for template_val in required_template_vals:
        set_inps_value_from_template(inps, template, template_key= template_val.key,
                                     inps_name= template_val.inps_name, REQUIRED= True)

    for template_val in optional_template_vals:
        set_inps_value_from_template(inps, template, template_key=template_val.key,
                                     inps_name = template_val.inps_name,
                                     default_value= template_val.default_value)

def call_ssara(custom_template, slcDir):
        out_file = '../out_ssara.log' 
        ssara_command = 'ssara_rsmas.py ' + \
            custom_template['ssaraopt'] + \
            ' --print --parallel=10 --asfResponseTimeout=360 --download |& tee ' + out_file
        command = 'ssh pegasus.ccs.miami.edu \"s.cgood;cd ' + slcDir + '; ' + \
            os.getenv('PARENTDIR') + '/sources/rsmas_isce/' + \
            ssara_command + '\"'
        ''' os.getenv('PARENTDIR') + '/sources/rsmas_isce/' + \     #FA 8/2018: use ssara_rsmas.py which uses ASF's ssara_federated_query-cj.py until Scott's ssara is fixed '''

        messageRsmas.log(command)
        os.chdir('..')
        messageRsmas.log(command)
        os.chdir(slcDir)

        status = subprocess.Popen(command, shell=True).wait()

def call_pysar(custom_template, custom_template_file):

    # TODO: Change subprocess call to get back error code and send error code to logger
    logger.debug('\n*************** running pysar ****************')
    command = 'pysarApp.py ' + custom_template_file + \
        ' --load-data |& tee out_pysar.log'
    messageRsmas.log(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in pysarApp.py --load-data')
        raise Exception('ERROR in pysarApp.py --load-data')

    # clean after loading data for cleanopt >= 2
    if 'All data needed found' in open('out_pysar.log').read():
        print('Cleaning files:   cleanopt= ' +
              str(custom_template['cleanopt']))
        if int(custom_template['cleanopt']) >= 2:
            _remove_directories(['merged'])
        if int(custom_template['cleanopt']) >= 3:
            _remove_directories(['SLC'])

    command = 'pysarApp.py ' + custom_template_file+' |& tee -a out_pysar.log'
    messageRsmas.log(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in pysarApp.py')
        raise Exception('ERROR in pysarApp.py')


def get_environment_from_source_file(source_file):

    get_environment_command = 'source {source_file} ; ' \
                              'python -c "import os, json; ' \
                              'print(json.dumps(dict(os.environ)))"'\
        .format(source_file= source_file)

    shell_command = str('cd ' + os.getenv('PARENTDIR') + '; ' + get_environment_command)

    process = subprocess.Popen(
            shell_command, shell=True, executable='/bin/csh', 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, error) = process.communicate()
    if process.returncode != 0 or error:
        print("ERROR: {0}".format(error))
        raise Exception("sourcing {source_file} failed.".format(source_file=source_file))
    return json.loads(output.decode('utf-8'))
    #return json.loads(output)


def get_isce_environment(flag_latest_version):
    if flag_latest_version:        # load from 3rdparty/sentinelstack
        source_file = 'cshrc_isce_latest'
    else:
        # load from source/sentinelstack  (9/17 version)
        source_file = 'cshrc_isce'

    return get_environment_from_source_file(source_file)


def get_project_name(custom_template_file):
    project_name = None
    if custom_template_file:
        custom_template_file = os.path.abspath(custom_template_file)
        project_name = os.path.splitext(
            os.path.basename(custom_template_file))[0]
        logger.debug('Project name: ' + project_name)
    return project_name


def get_work_directory(work_dir, project_name):
    if not work_dir:
        if autoPath and 'SCRATCHDIR' in os.environ and project_name:
            work_dir = os.getenv('SCRATCHDIR') + '/' + project_name
        else:
            work_dir = os.getcwd()
    work_dir = os.path.abspath(work_dir)
    return work_dir


def create_custom_template(custom_template_file, work_dir):
    if custom_template_file:
        # Copy custom template file to work directory
        if utils.update_file(
                os.path.basename(
                    custom_template_file),
                custom_template_file,
                check_readable=False):
            shutil.copy2(custom_template_file, work_dir)

        # Read custom template
        logger.info('read custom template file: %s', custom_template_file) 
        return readfile.read_template(custom_template_file)
    else:
        return dict()


def create_or_copy_dem(work_dir, template, custom_template_file, isce_env):
    dem_dir = work_dir + '/DEM'
    if os.path.isdir(dem_dir) and len(os.listdir(dem_dir)) == 0:
        os.rmdir(dem_dir)

    
    if not os.path.isdir(dem_dir):
        if 'sentinelStack.dem_dir' in list(template.keys()):
            shutil.copytree(template['sentinelStack.dem_dir'], dem_dir)
        else:
            # TODO: Change subprocess call to get back error code and send error code to logger
            cmd = 'dem_rsmas.py ' + custom_template_file
            status = subprocess.Popen(cmd, env=isce_env, shell=True).wait()
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


def create_stack_sentinel_run_files(inps, dem_file):
    suffix  = ''
    extraOptions = ''
    if inps.ProcessingMethod is 'squeesar' or inps.ProcessingMethod is 'ps':
       suffix       = 'squeesar'
       extraOptions = ' -P ' + inps.ProcessingMethod
    command = 'stackSentinel'+suffix+'.py -n ' + str(inps.subswath) + ' -b ' + inps.boundingBox + \
              ' -c ' + str(inps.numConnections) + \
              ' -z ' + str(inps.azimuthLooks) + ' -r ' + str(inps.rangeLooks) + \
              ' -f ' + str(inps.filtStrength) + ' -W ' + inps.workflow + \
              ' -u ' + inps.unwMethod + ' -C ' + inps.coregistration + \
              ' -s ' + inps.slcDir + ' -d ' + dem_file + extraOptions + \
              ' -o ' + inps.orbitDir + ' -a ' + inps.auxDir +' -t \'\' |& tee out_stackSentinel.log '

    if inps.excludeDate is not None:
        command = command + ' -x ' + inps.excludeDate

    # TODO: Change subprocess call to get back error code and send error code to logger
    logger.info(command)
    messageRsmas.log(command)
    status = subprocess.Popen(command, env=inps.isce_env, shell=True).wait()
    if status is not 0:
        logger.error(
            'Problem with making run_files using stackSentinel.py')
        raise Exception('ERROR making run_files using stackSentinel.py')

    temp_list = glob.glob('run_files/run_*job')
    for item in temp_list:
        os.remove(item)

    run_file_list = glob.glob('run_files/run_*')
    run_file_list.sort(key=lambda x: int(x.split('_')[2]))

    return run_file_list


def create_default_template():
    template_file = 'sentinelStack_template.txt'
    if not os.path.isfile(template_file):
        logger.info('generate default template file: %s', template_file)
        with open(template_file, 'w') as file:
            file.write(TEMPLATE)
    else:
        logger.info('default template file exists: %s', template_file)
    template_file = os.path.abspath(template_file)
    return template_file


def get_memory_defaults(inps):
    if inps.workflow == 'interferogram':
        memoryuse = ['3700', '3700', '3700', '4000', '3700', '3700', '5000', '3700', '3700', '3700', '3700', '3700']
    elif inps.workflow == 'slc':
        memoryuse = ['3700', '3700', '3700', '4000', '3700', '3700', '5000', '3700', '3700', '5000', '3700', '3700',
                     '3700']
    return memoryuse


def submit_isce_jobs(isce_env, run_file_list, cwd, subswath, custom_template_file, memoryuse):
    for item in run_file_list:
        memorymax = str(memoryuse[int(item.split('_')[2]) - 1])
        if os.getenv('QUEUENAME')=='debug':
           walltimelimit = '0:30'
        else:
           walltimelimit = '4:00'    # run_1 (master) for 2 subswaths took 2:20 minutes

        if len(memoryuse) == 13:
            if item.split('_')[2] == '10':
                walltimelimit = '60:00'
        cmd = 'createBatch.pl ' + cwd + '/' + item + ' memory=' + memorymax + ' walltime=' + walltimelimit
        # FA 7/18: need more memory for run_7 (resample) only
        # FA 7/18: Should hardwire the memory requirements for the different workflows into a function and use those
        # TODO: Change subprocess call to get back error code and send error code to logger
        status=0
        status = subprocess.Popen(cmd, env=isce_env, shell=True).wait()
        if status is not 0:
            logger.error('ERROR submitting jobs using createBatch.pl')
            raise Exception('ERROR submitting jobs using createBatch.pl')

    sswath = subswath.strip('\'').split(' ')[0]
    xml_file = glob.glob('master/*.xml')[0]

    command = 'prep4timeseries.py -i merged/interferograms/ -x ' + xml_file + \
              ' -b baselines/ -g merged/geom_master/ '
    messageRsmas.log(command)
    # TODO: Change subprocess call to get back error code and send error code to logger
    status = subprocess.Popen(command, env=isce_env, shell=True).wait()
    if status is not 0:
        logger.error('ERROR in prep4timeseries.py')
        raise Exception('ERROR in prep4timeseries.py')

        # FA 3/2018 check_error_files_sentinelstack('run_files/run_*.e')      # exit if
        # non-zero-size or non-zero-lines run*e files are found


def run_insar_maps(work_dir):
    hdfeos_file = glob.glob(work_dir + '/PYSAR/S1*.he5')
    hdfeos_file.append(
        glob.glob(
            work_dir +
            '/PYSAR/SUBSET_*/S1*.he5'))  # FA: we may need [0]
    hdfeos_file = hdfeos_file[0]

    json_folder = work_dir + '/PYSAR/JSON'
    mbtiles_file = json_folder + '/' + \
                   os.path.splitext(os.path.basename(hdfeos_file))[0] + '.mbtiles'

    if os.path.isdir(json_folder):
        logger.info('Removing directory: %s', json_folder)
        shutil.rmtree(json_folder)

    command1 = 'hdfeos5_2json_mbtiles.py ' + hdfeos_file + ' ' + json_folder + ' |& tee out_insarmaps.log'
    command2 = 'json_mbtiles2insarmaps.py -u insaradmin -p Insar123 --host ' + \
               'insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder ' + \
               json_folder + ' --mbtiles_file ' + mbtiles_file + ' |& tee -a out_insarmaps.log'

    with open(work_dir + '/PYSAR/run_insarmaps', 'w') as f:
        f.write(command1 + '\n')
        f.write(command2 + '\n')

    ######### submit job  ################### (FA 6/2018: the second call (json_mbtiles*) does not work yet)
    #command_list=['module unload share-rpms65',command1,command2]
    #submit_insarmaps_job(command_list,inps)

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


def main(argv):
    start_time = time.time()
    inps = command_line_parse()
    
    #########################################
    # Initiation
    #########################################

    inps.project_name = get_project_name(
        custom_template_file=inps.custom_template_file)

    inps.work_dir = get_work_directory(inps.work_dir, inps.project_name)

    # Change directory to work directory
    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)
    logger.debug("Go to work directory: " + inps.work_dir)

    command_line = os.path.basename(
        argv[0]) + ' ' + ' '.join(argv[1:len(argv)])
    messageRsmas.log('##### NEW RUN #####')
    messageRsmas.log(command_line)

    #########################################
    # Submit job
    #########################################
    if inps.bsub_flag:
        submit_job(sys.argv[:], inps)

    #########################################
    # Read Template Options
    #########################################
    print('\n*************** Template Options ****************')
    # write default template
    inps.template_file = create_default_template()

    # TODO: If `custom_template` is not created, empty dict is created to avoid
    # error that occur below when `custom_template` is referenced. Is this the
    # desired functionality?
    custom_template = create_custom_template(
        custom_template_file=inps.custom_template_file,
        work_dir=inps.work_dir)

    # Update default template with custom input template
    logger.info('update default template based on input custom template')
    inps.template_file = utils.update_template_file(
        inps.template_file, custom_template)

    if inps.generate_template:
        logger.info('Exit as planned after template file generation.')
        print('Exit as planned after template file generation.')
        return

    logger.info('read default template file: ' + inps.template_file)
    template = readfile.read_template(inps.template_file)

    #########################################
    # Default options
    #########################################

    set_default_options(inps, template)

    ######  directories for cleaning ########
    # TODO: Idea: create a `inps.directories_to_delete` and delete at the end
    clean_list2 = ['configs', 'baselines', 'stack',
                   'coreg_slaves', 'misreg', 'orbits',
                   'coarse_interferograms', 'ESD', 'interferograms',
                   'slaves', 'master', 'geom_master']
    clean_list3 = ['merged']

    if 'cleanopt' not in custom_template:
        custom_template['cleanopt'] = '0'

    #########################################
    # Get the environment for ISCE (can be ommitted once it is part of the regular installation)
    #########################################
    inps.isce_env = get_isce_environment(inps.flag_latest_version)

    #########################################
    # startssara: Getting Data
    #########################################
    if inps.flag_ssara:
        if not os.path.isdir(inps.slcDir):
            os.mkdir(inps.slcDir)
        if inps.slcDir is not inps. work_dir+'/SLC':  
            os.symlink(inps.slcDir,inps.work_dir+'/SLC')
        os.chdir(inps.slcDir)

        call_ssara(custom_template, inps.slcDir)

    if inps.stopssara:
        logger.debug('Exit as planned after ssara')
        sys.exit(0)

    #########################################
    # startprocess: create run files and process
    #########################################
    if inps.flag_process:
        os.chdir(inps.work_dir)

        dem_file = create_or_copy_dem(work_dir= inps.work_dir,
                                      template= template,
                                      custom_template_file= inps.custom_template_file,
                                      isce_env= inps.isce_env)
        # Clean up files
        # temp_list = clean_list1 + clean_list2 + clean_list3 + ['PYSAR']
        temp_list =['run_files']
        _remove_directories(temp_list)

        run_file_list = create_stack_sentinel_run_files(inps, dem_file)
        inps.cwd = os.getcwd()

        #########################################
        # submit jobs
        #########################################
        memoryUse = get_memory_defaults(inps)
        submit_isce_jobs(inps.isce_env, run_file_list,
                         inps.cwd, inps.subswath,
                         inps.custom_template_file,
                         memoryUse)

        if int(custom_template['cleanopt']) >=1:
            _remove_directories(clean_list1)

    if inps.stopprocess:
        logger.info('Exit as planned after processing')
        return

    #########################################
    # running pysar
    #########################################
    if inps.flag_pysar:
        _remove_directories(['PYSAR'])       # remove once PYSAR properly recognizes new files
        call_pysar(custom_template=custom_template,
                  custom_template_file=inps.custom_template_file)

        # Record runtime and email results
        time_diff = time.time() - start_time
        minutes, seconds = divmod(time_diff, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = 'Time used: {0}02d hours {0}02d mins {0}02d secs'.format(
            hours, minutes, seconds)

        email_pysar_results(time_str,custom_template)

    if inps.stoppysar:
        logger.debug('Exit as planned after pysar')
        return

    #########################################
    # ingesting into insarmaps
    #########################################
    if inps.flag_insarmaps:
        run_insar_maps(inps.work_dir)

        email_insarmaps_results(custom_template)

    # clean
    if int(custom_template['cleanopt']) == 4:
        shutil.rmtree('PYSAR')

    if inps.stopinsarmaps:
        logger.debug('Exit as planned after insarmaps')
        return

    logger.debug('\n###############################################')
    logger.info('End of process_sentinelStack')
    logger.debug('#################################################')


if __name__ == '__main__':
    main(sys.argv[:])

