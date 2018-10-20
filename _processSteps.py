import os
import sys
import logging
import argparse
import time
import subprocess
import _process_utilities as putils
sys.path.insert(0, os.getenv('SSARAHOME'))
from pysar.utils import readfile
from pysar.utils import utils
import messageRsmas

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


def create_processRsmas_parser(EXAMPLE):
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
    """

    :return: returns inputs from the command line as a parsed object
    """
    parser = create_processRsmas_parser(EXAMPLE)

    inps = parser.parse_args()
    if inps.custom_template_file and os.path.basename(
            inps.custom_template_file) == 'TopsStack_template.txt':
        inps.custom_template_file = None

    # option processing. Same as in process_sentinelStack.pl. Can run every portion individually
    # need --insarmaps option so that it is run
    inps.startssara = True
    inps.flag_ssara = False
    inps.flag_makerun = False
    inps.flag_process = False
    inps.flag_pysar = False  # inps.flag_insarmaps is True only if --insarmaps

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

    logger.debug('flag_ssara:     %s', inps.flag_ssara)
    logger.debug('flag_makerun:   %s', inps.flag_makerun)
    logger.debug('flag_process:   %s', inps.flag_process)
    logger.debug('flag_pysar:     %s', inps.flag_pysar)
    logger.debug('flag_insarmaps: %s', inps.flag_insarmaps)
    logger.debug('flag_mail:      %s', inps.flag_mail)
    logger.debug('flag_latest_version:   %s', inps.flag_latest_version)
    logger.debug('stopssara:      %s', inps.stopssara)
    logger.debug('stopmakerun:    %s', inps.stopmakerun)
    logger.debug('stopprocess:    %s', inps.stopprocess)
    logger.debug('stoppysar:      %s', inps.stoppysar)

    return inps

###############################################################################


def submit_job(argv, inps):

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

       #f.write('#BSUB -W 2:00\n')
       #f.write('#BSUB -R rusage[mem=3700]\n')
       #f.write('#BSUB -R span[hosts=1]\n')
       f.write('cd '+inps.work_dir+'\n')
       f.write(command_line)
       f.close()

       if inps.bsub_flag:
          job_cmd = 'bsub -P insarlab < process.job'
          print('bsub job submission')
          os.system(job_cmd)
          sys.exit(0)

##########################################################################


def step_dir(inps, argv):
    inps.project_name = putils.get_project_name(
        custom_template_file=inps.custom_template_file)

    inps.work_dir = putils.get_work_directory(inps.work_dir, inps.project_name)

    # Change directory to work directory
    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)
    os.chdir(inps.work_dir)
    logger.debug("Go to work directory: " + inps.work_dir)

    command_line = os.path.basename(
        argv[0]) + ' ' + ' '.join(argv[1:len(argv)])
    messageRsmas.log('##### NEW RUN #####')
    messageRsmas.log(command_line)

    return inps

###############################################################################


def step_template(inps):

    print('\n*************** Template Options ****************')
    # write default template
    inps.template_file = putils.create_default_template()

    inps.custom_template = putils.create_custom_template(
        custom_template_file=inps.custom_template_file,
        work_dir=inps.work_dir)

    # Update default template with custom input template
    logger.info('update default template based on input custom template')
    if not inps.template_file == inps.custom_template:
        inps.template_file = utils.update_template_file(
            inps.template_file, inps.custom_template)

    if inps.generate_template:
        logger.info('Exit as planned after template file generation.')
        print('Exit as planned after template file generation.')
        return

        logger.info('read default template file: ' + inps.template_file)
    inps.template = readfile.read_template(inps.template_file)

    putils.set_default_options(inps)

    if 'cleanopt' not in inps.custom_template:
        inps.custom_template['cleanopt'] = '0'

    return inps

###############################################################################


def step_ssara(inps):
    if inps.flag_ssara:
        if not os.path.isdir(inps.slcDir):
            os.mkdir(inps.slcDir)
        if inps.slcDir is not inps.work_dir + '/SLC' and not os.path.isdir(inps.work_dir + '/SLC'):
            os.symlink(inps.slcDir, inps.work_dir + '/SLC')

        putils.call_ssara(inps.custom_template_file, inps.slcDir)

    if inps.stopssara:
        logger.debug('Exit as planned after ssara')
        sys.exit(0)

    return inps

###############################################################################
def step_runfiles(inps):
    if inps.flag_makerun:
        os.chdir(inps.work_dir)
        temp_list = ['run_files', 'configs']
        putils._remove_directories(temp_list)

        dem_file = putils.create_or_copy_dem(work_dir=inps.work_dir,
                                      template=inps.template,
                                      custom_template_file=inps.custom_template_file)

        inps.run_file_list = putils.create_stack_sentinel_run_files(inps, dem_file)

    if inps.stopmakerun:
        logger.info('Exit as planned after making sentinel run files ')
        sys.exit(0)

    return inps

#################################################################################


def step_process(inps):
    if inps.flag_process:
        command = 'execute_rsmas_run_files.py ' + inps.custom_template_file
        messageRsmas.log(command)
        # Check the performance, change in subprocess
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.error('ERROR in execute_rsmas_run_files.py')
            raise Exception('ERROR in execute_rsmas_run_files.py')


        if int(inps.custom_template['cleanopt']) >= 1:
            _remove_directories(cleanlist[1])

    if inps.stopprocess:
        logger.info('Exit as planned after processing')
        sys.exit(0)

    return inps

###############################################################################


def step_pysar(inps, start_time):

    if inps.flag_pysar:
        putils._remove_directories(['PYSAR'])  # remove once PYSAR properly recognizes new files
        putils.call_pysar(custom_template=inps.custom_template,
                   custom_template_file=inps.custom_template_file)

        # Record runtime and email results
        time_diff = time.time() - start_time
        minutes, seconds = divmod(time_diff, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = 'Time used: {0}02d hours {0}02d mins {0}02d secs'.format(
            hours, minutes, seconds)

        putils.email_pysar_results(time_str, inps.custom_template)

    if inps.stoppysar:
        logger.debug('Exit as planned after pysar')
        sys.exit(0)

    return


###############################################################################


def step_insarmaps(inps):
    if inps.flag_insarmaps:
        putils.run_insar_maps(inps.work_dir)

        putils.email_insarmaps_results(inps.custom_template)

    # clean
    if int(inps.custom_template['cleanopt']) == 4:
        shutil.rmtree(cleanlist[4])

    if inps.stopinsarmaps:
        logger.debug('Exit as planned after insarmaps')
        return

##########################################################################


def log_end_message():
    logger.debug('\n###############################################')
    logger.info('End of process_rsmas')
    logger.debug('#################################################')

###############################################################################

#test change
