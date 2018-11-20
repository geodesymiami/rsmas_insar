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

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

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
from _process_utilities import set_default_options
from _process_utilities import create_custom_template
from _process_utilities import create_default_template
from _process_utilities import _remove_directories

from _process_utilities import create_or_copy_dem
from _process_utilities import call_ssara
from _process_utilities import call_pysar
from _process_utilities import run_insar_maps
from _process_utilities import get_project_name
from _process_utilities import get_work_directory
from _process_utilities import create_stack_sentinel_run_files

from _process_utilities import get_memory_defaults
from _process_utilities import email_pysar_results
from _process_utilities import email_insarmaps_results

from _process_utilities import remove_zero_size_or_length_files
from _process_utilities import check_error_files_sentinelstack
from _process_utilities import remove_zero_size_or_length_files
from _process_utilities import remove_error_files_except_first
from _process_utilities import concatenate_error_files
from _processSteps import submit_job

logger = logging.getLogger("process_sentinel")

###############################################################################
TEMPLATE = '''# vim: set filetype=cfg:
##------------------------ sentinelStack_template.txt ------------------------##
## 1. sentinelStack options
sentinelStack.demDir         = auto  #[DEM]
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
sentinelStack.processingMethod = auto #[sbas, squeesar, ps]
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
  --stoppysarload      stops after time series analysis
  --stopinsarmaps      stops after insarmaps upload
  --startssara         [default]

  --insarmaps          append after other options to upload to insarmaps.miami.edu
  --bsub               submits job using bsub (and send email when done)
  --nomail             suppress emailing imagefiles of results (default is emailing)
  --remove_project_dir removes project directory before starting download

  --latest             use earthdef.caltech SVN version (3rdpary/sentinelstack) (default: source/sentinelStack)

    e.g:  process_rsmas.pl $SAMPLESDIR/WellquakeT399EnvD2.template

  e.g.:  process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startssara
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopssara
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startprocess
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopprocess
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startpysar
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stoppysar
         process_sentinelStack.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stoppysarload
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
        '--stoppysarload',
        dest='stoppysarload',
        action='store_true',
        help='exit after loading into pysar')
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
        '--remove_project_dir',
        dest='remove_project_dir',
        action='store_true',
        help='remove directory before download starts')
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

####################################################################################

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
    logger.debug('stoppysarload:  %s', inps.stoppysarload)

    return inps

####################################################################################

def submit_isce_jobs(run_file_list, cwd, subswath, custom_template_file, memoryuse):
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
        status = subprocess.Popen(cmd,  shell=True).wait()
        if status is not 0:
            logger.error('ERROR submitting jobs using createBatch.pl')
            raise Exception('ERROR submitting jobs using createBatch.pl')

    sswath = subswath.strip('\'').split(' ')[0]
    xml_file = glob.glob('master/*.xml')[0]

####################################################################################

def main(argv):
    start_time = time.time()
    inps = command_line_parse()
    
    #########################################
    # Initiation
    #########################################

    inps.project_name = get_project_name(custom_template_file=inps.custom_template_file)

    inps.work_dir = get_work_directory(inps.work_dir, inps.project_name)
    
    if inps.remove_project_dir:
        _remove_directories(directories_to_delete=[inps.work_dir])

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
        inps.wall_time='48:00'
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
    inps.template = template

    #########################################
    # Default options
    #########################################

    set_default_options(inps)

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
    # startssara: Getting Data
    #########################################
    if inps.flag_ssara:
        if not os.path.isdir(inps.slcDir):
            os.mkdir(inps.slcDir)
        if inps.slcDir is not inps.work_dir+'/SLC' and not os.path.isdir(inps.work_dir+'/SLC'):  
            os.symlink(inps.slcDir,inps.work_dir+'/SLC')

        call_ssara(inps.custom_template_file, inps.slcDir)

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
                                      custom_template_file= inps.custom_template_file)
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
        submit_isce_jobs(run_file_list,
                         inps.cwd, inps.subswath,
                         inps.custom_template_file,
                         memoryUse)
        remove_zero_size_or_length_files(directory='run_files')
        concatenate_error_files(directory='run_files',out_name='out_stackSentinel_errorfiles.e')
        remove_error_files_except_first(directory='run_files')

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
                  custom_template_file=inps.custom_template_file,flag_load_and_stop=inps.stoppysarload)

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

