#! /usr/bin/env python3
###############################################################################
#
# Project: process_rsmas.py
# Author: Sara Mirzaee
# Created: 10/2018
#
###############################################################################

import os
import sys

import argparse
import time
import shutil
import subprocess
from rsmas_logging import rsmas_logger, loglevel
import _process_utilities as putils
sys.path.insert(0, os.getenv('SSARAHOME'))
from pysar.utils import readfile, utils
import messageRsmas

logger  = putils.send_logger()

####################################################################

EXAMPLE = '''example:
  process_rsmas.py  DIR/TEMPLATEFILE [options] [--bsub]

  InSAR processing using ISCE Stack and RSMAS processing scripts

  Process directory is /projects/scratch/insarlab/$USER. Can be adjusted e.g. with TESTBENCH1,2,3 alias
  options given on command line overrides the templatefile (not verified)

  --startmakerun       skips data downloading using SSARA
  --startprocess       skips data downloading and making run files
  --startpysar         skips InSAR processing (needs a 'merged' directory)
  --startinsarmaps     skips pysar  processing (needs a PYSAR directory)
  --startjobstats      skips insarmaps processing (summarizes job statistics)
  --stopsara           stops after ssara
  --stopmakerun        stops after making run files
  --stopprocess        stops after process
  --stoppysar          stops after time series analysis
  --stopinsarmaps      stops after insarmaps upload
  --startssara         [default]

  --insarmaps          append after other options to upload to insarmaps.miami.edu
  --bsub               submits job using bsub (and send email when done)
  --nomail             suppress emailing imagefiles of results (default is emailing)
  --restart            removes project directory before starting download


  e.g.:  process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startssara
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopssara
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startmakerun
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopmakerun
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startprocess
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopprocess
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startpysar
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stoppysar
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startinsarmaps  : for ingestion into insarmaps
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopinsarmaps


  # You can separately run processing step and execute run files by:
    "execute_rsmas_run_files.py templatefile starting_run stopping_run"
    Example for running run 1 to 4:
    execute_rsmas_run_files.py $TE/template 1 4

  # Generate template file:
         process_rsmas.py -g
         process_rsmas.py $SAMPLESDIR/GalapagosT128SenVVD.template -g

         cleanopt in TEMPLATEFILE controls file removal [default=0]
             cleanopt = 0 :  none
             cleanopt = 1 :  after sentinelStack: configs, baselines, stack, coreg_slaves, misreg, orbits, coarse_interferograms, ESD, interferograms
             cleanopt = 2 :  after pysarApp.py --load_data: 'merged'
             cleanopt = 3 :  after pysarApp.py --load_data: 'SLC'
             cleanopt = 4 :  everything including PYSAR 

  --------------------------------------------
  Open TopsStack_template.txt file for details.
  --------------------------------------------
'''

###############################################################################


def create_process_rsmas_parser(EXAMPLE):
    """ Creates command line argument parser object. """

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
        '--startmakerun',
        dest='startmakerun',
        action='store_true',
        help='make sentinel run files using topsStack package')
    parser.add_argument(
        '--stopmakerun',
        dest='stopmakerun',
        action='store_true',
        help='exit after making sentinel run files')
    parser.add_argument(
        '--startprocess',
        dest='startprocess',
        action='store_true',
        help='process using sentinel topsStack package')
    parser.add_argument(
        '--stopprocess',
        dest='stopprocess',
        action='store_true',
        help='exit after running sentinel topsStack')
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

##########################################################################


def command_line_parse():
    """ Parses command line agurments into inps variable. """

    parser = create_process_rsmas_parser(EXAMPLE)

    inps = parser.parse_args()
    if inps.custom_template_file and os.path.basename(
            inps.custom_template_file) == 'stackSentinel_template.txt':
        inps.custom_template_file = None


    inps.startssara = True
    inps.flag_ssara = False
    inps.flag_makerun = False
    inps.flag_process = False
    inps.flag_pysar = False
    inps.stoppysarload = False
    
    if inps.startmakerun:
        inps.flag_makerun = True
        inps.flag_process = True
        inps.flag_pysar = True
        inps.startssara = False

    if inps.startprocess:
        inps.flag_process = True
        inps.flag_pysar = True
        inps.flag_makerun = False
        inps.startssara = False
        
    if inps.startpysar:
        inps.flag_pysar = True
        inps.flag_process = False
        inps.flag_makerun = False
        inps.startssara = False
        
    if inps.startinsarmaps:
        inps.startssara = False
        inps.flag_process = False
        inps.flag_makerun = False
        inps.flag_insarmaps = True
        
    if inps.startssara:
        inps.flag_ssara = True
        inps.flag_makerun = True
        inps.flag_process = True
        inps.flag_pysar = True

    logger.log(loglevel.DEBUG, 'flag_ssara:     {}'.format(inps.flag_ssara))
    logger.log(loglevel.DEBUG, 'flag_makerun:   {}'.format(inps.flag_makerun))
    logger.log(loglevel.DEBUG, 'flag_process:   {}'.format(inps.flag_process))
    logger.log(loglevel.DEBUG, 'flag_pysar:     {}'.format(inps.flag_pysar))
    logger.log(loglevel.DEBUG, 'flag_insarmaps: {}'.format(inps.flag_insarmaps))
    logger.log(loglevel.DEBUG, 'flag_mail:      {}'.format(inps.flag_mail))
    logger.log(loglevel.DEBUG, 'flag_latest_version:   {}'.format(inps.flag_latest_version))
    logger.log(loglevel.DEBUG, 'stopssara:      {}'.format(inps.stopssara))
    logger.log(loglevel.DEBUG, 'stopmakerun:    {}'.format(inps.stopmakerun))
    logger.log(loglevel.DEBUG, 'stopprocess:    {}'.format(inps.stopprocess))
    logger.log(loglevel.DEBUG, 'stoppysar:      {}'.format(inps.stoppysar))
    logger.log(loglevel.DEBUG, 'stoppysarload:  {}'.format(inps.stoppysarload))

    return inps

###############################################################################


def submit_job(argv, inps):
    """ Submits process_rsmas.py as a job. """

    if inps.bsub_flag:

       command_line = os.path.basename(argv[0])
       i = 1
       while i < len(argv):
             if argv[i] != '--bsub':
                command_line = command_line + ' ' + sys.argv[i]
             i = i + 1
       command_line = command_line + '\n'

       projectID = 'insarlab'

       f = open(inps.work_dir+'/process.job', 'w')
       f.write('#! /bin/tcsh\n')
       f.write('#BSUB -J '+inps.project_name+' \n')
       f.write('#BSUB -B -u '+os.getenv('NOTIFICATIONEMAIL')+'\n')
       f.write('#BSUB -o z_processSentinel_%J.o\n')
       f.write('#BSUB -e z_processSentinel_%J.e\n')
       f.write('#BSUB -n 1\n' )
       if projectID:
          f.write('#BSUB -P '+projectID+'\n')
       f.write('#BSUB -q '+os.getenv('QUEUENAME')+'\n')
       if inps.wall_time:
          f.write('#BSUB -W ' + inps.wall_time + '\n')

       f.write('cd '+inps.work_dir+'\n')
       f.write(command_line)
       f.close()

       if inps.bsub_flag:
          job_cmd = 'bsub -P insarlab < process.job'
          logger.log(loglevel.INFO, 'bsub job submission')
          os.system(job_cmd)
          sys.exit(0)

    return None

###############################################################################


def create_or_update_template(inps):
    """ Creates a default template file and/or updates it.
        returns the values in 'inps'
    """

    print('\n*************** Template Options ****************')
    # write default template
    inps.template_file = putils.create_default_template()

    inps.custom_template = putils.create_custom_template(
        custom_template_file=inps.custom_template_file,
        work_dir=inps.work_dir)

    # Update default template with custom input template
    logger.log(loglevel.INFO, 'update default template based on input custom template')
    if not inps.template_file == inps.custom_template:
        inps.template_file = utils.update_template_file(inps.template_file, inps.custom_template)


    logger.log(loglevel.INFO, 'read default template file: ' + inps.template_file)
    inps.template = readfile.read_template(inps.template_file)

    putils.set_default_options(inps)

    if 'cleanopt' not in inps.custom_template:
        inps.custom_template['cleanopt'] = '0'

    return inps


###############################################################################


def call_ssara(flag_ssara, custom_template_file, slc_dir):
    """ Downloads data with ssara and asfserial scripts. """

    if flag_ssara:
        out_file = os.getcwd() + '/' + 'out_download_ssara'
        command = 'download_ssara_rsmas.py ' + custom_template_file
        messageRsmas.log(command)
        command = '('+command+' > '+out_file+'.o) >& '+out_file+'.e'
        command_ssh = 'ssh pegasus.ccs.miami.edu \"s.cgood;cd ' + slc_dir + '; ' +  command + '\"'
        status = subprocess.Popen(command_ssh, shell=True).wait()
        print('Exit status from download_ssara_rsmas.py:',status)

        out_file = os.getcwd() + '/' + 'out_download_asfserial'
        command = 'download_asfserial_rsmas.py ' + custom_template_file
        messageRsmas.log(command)
        command = '('+command+' > '+out_file+'.o) >& '+out_file+'.e'
        command_ssh = 'ssh pegasus.ccs.miami.edu \"s.cgood;cd ' + slc_dir + '; ' +  command + '\"'
        status = subprocess.Popen(command_ssh, shell=True).wait()
        print('Exit status from download_asfserial_rsmas.py:',status)
    
    return None

###############################################################################


def create_or_copy_dem(work_dir, template, custom_template_file):
    """ Downloads a DEM file or copies an existing one."""

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
                logger.log(loglevel.ERROR, 'ERROR while making DEM')
                raise Exception('ERROR while making DEM')

    return None

#################################################################################


def create_runfiles(inps):
    """ Calls the script to create stackSentinel runfiles and configs."""

    if inps.flag_makerun:
        os.chdir(inps.work_dir)
        command = 'create_stacksentinel_run_files.py ' + inps.custom_template_file
        messageRsmas.log(command)
        # Check the performance, change in subprocess
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.log(loglevel.ERROR, 'ERROR in create_stacksentinel_run_files.py')
            raise Exception('ERROR in create_stacksentinel_run_files.py')
        if inps.stopmakerun:
            logger.log(loglevel.INFO, 'Exit as planned after making sentinel run files ')
            sys.exit(0)

    return inps

#################################################################################


def process_runfiles(inps):
    """ Calls the script to execute stackSentinel runfiles."""

    if inps.flag_process:
        command = 'execute_stacksentinel_run_files.py ' + inps.custom_template_file
        messageRsmas.log(command)
        # Check the performance, change in subprocess
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.log(loglevel.ERROR, 'ERROR in execute_stacksentinel_run_files.py')
            raise Exception('ERROR in execute_stacksentinel_run_files.py')


        if int(inps.custom_template['cleanopt']) >= 1:
            _remove_directories(cleanlist[1])

    if inps.stopprocess:
        logger.log(loglevel.INFO, 'Exit as planned after processing')
        sys.exit(0)

    return inps

###############################################################################


def run_pysar(inps, start_time):
    """ Calls the pysarAPP to load data and run time series analysis."""

    if inps.flag_pysar:

        if os.path.isdir('PYSAR'):
            shutil.rmtree('PYSAR')

        putils.call_pysar(custom_template=inps.custom_template,
                   custom_template_file=inps.custom_template_file,
                         flag_load_and_stop=inps.stoppysarload)

        # Record runtime and email results
        time_diff = time.time() - start_time
        minutes, seconds = divmod(time_diff, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = 'Time used: {0}02d hours {0}02d mins {0}02d secs'.format(
            hours, minutes, seconds)

        putils.email_pysar_results(time_str, inps.custom_template)

    if inps.stoppysar:
        logger.log(loglevel.DEBUG, 'Exit as planned after pysar')
        sys.exit(0)

    return


###############################################################################


def run_ingest_insarmaps(inps):
    """ Calls the script of ingest insarmaps and emails the results."""

    if inps.flag_insarmaps:

        command = 'ingest_insarmaps.py ' + inps.custom_template_file
        messageRsmas.log(command)
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.log(loglevel.ERROR, 'ERROR in ingest_insarmaps.py')
            raise Exception('ERROR in ingest_insarmaps.py')

        putils.email_insarmaps_results(inps.custom_template)

    # clean
    if int(inps.custom_template['cleanopt']) == 4:
        shutil.rmtree(cleanlist[4])

    if inps.stopinsarmaps:
        ogger.log(loglevel.DEBUG, 'Exit as planned after insarmaps')

    return None


