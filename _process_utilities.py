#! /usr/bin/env python3
###############################################################################
#
# Project: Utilitiels for process_rsmas.py
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

logger = logging.getLogger("process_sentinel")
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
sentinelStack.bbox                        = None         # [ '-1 0.15 -91.7 -90.9'] required
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

EXAMPLE = '''example:
  process_rsmas.py  DIR/TEMPLATEFILE [options] [--bsub]

  InSAR processing using ISCE Stack and RSMAS processing scripts

  Process directory is /projects/scratch/insarlab/$USER. Can be adjusted e.g. with TESTBENCH1,2,3 alias
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


  e.g.:  process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startssara
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopssara
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startprocess
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopprocess
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startpysar
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stoppysar
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --startinsarmaps  : for ingestion into insarmaps
         process_rsmas.py  $SAMPLESDIR/GalapagosT128SenVVD.template --stopinsarmaps

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


def step_dir(inps, argv):
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

    return inps

###############################################################################


def step_template(inps):

    print('\n*************** Template Options ****************')
    # write default template
    inps.template_file = create_default_template()

    inps.custom_template = create_custom_template(
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

    set_default_options(inps)

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

        call_ssara(inps.custom_template_file, inps.slcDir)

    if inps.stopssara:
        logger.debug('Exit as planned after ssara')
        sys.exit(0)

    return inps

###############################################################################


def step_process(inps):
    if inps.flag_process:

        os.chdir(inps.work_dir)

        cleanlist = clean_list()

        print(inps.template)

        dem_file = create_or_copy_dem(work_dir=inps.work_dir,
                                      template=inps.template,
                                      custom_template_file=inps.custom_template_file)

        #temp_list = ['run_files', 'configs']
        #_remove_directories(temp_list)

        run_file_list = create_stack_sentinel_run_files(inps, dem_file)
        inps.cwd = os.getcwd()

        # submit jobs
        #########################################
        memory_use = get_memory_defaults(inps)
        submit_isce_jobs(run_file_list,
                         inps.cwd, inps.subswath,
                         memory_use)

        if int(inps.custom_template['cleanopt']) >= 1:
            _remove_directories(cleanlist[1])

    if inps.stopprocess:
        logger.info('Exit as planned after processing')
        return
###############################################################################


def step_pysar(inps, start_time):

    if inps.flag_pysar:
        _remove_directories(['PYSAR'])  # remove once PYSAR properly recognizes new files
        call_pysar(custom_template=inps.custom_template,
                   custom_template_file=inps.custom_template_file)

        # Record runtime and email results
        time_diff = time.time() - start_time
        minutes, seconds = divmod(time_diff, 60)
        hours, minutes = divmod(minutes, 60)
        time_str = 'Time used: {0}02d hours {0}02d mins {0}02d secs'.format(
            hours, minutes, seconds)

        email_pysar_results(time_str, inps.custom_template)

    if inps.stoppysar:
        logger.debug('Exit as planned after pysar')
        return

###############################################################################


def step_insarmaps(inps):
    if inps.flag_insarmaps:
        run_insar_maps(inps.work_dir)

        email_insarmaps_results(inps.custom_template)

    # clean
    if int(inps.custom_template['cleanopt']) == 4:
        shutil.rmtree(cleanlist[4])

    if inps.stopinsarmaps:
        logger.debug('Exit as planned after insarmaps')
        return

###############################################################################


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

    template_file = glob.glob('PYSAR/*.template')[0]

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

##########################################################################


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


def file_len(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])

##########################################################################


def check_error_files_sentinelstack(pattern):
    errorFiles  = glob.glob(pattern)

    elist = []
    for item in errorFiles:
        if os.path.getsize(item) == 0:       # remove zero-size error files
            os.remove(item)
        elif file_len(item) == 0:
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
    inps.flag_process = False
    inps.flag_pysar = False  # inps.flag_insarmaps is True only if --insarmaps

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

##########################################################################


def _remove_directories(directories_to_delete):
    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)

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
         TemplateTuple('sentinelStack.bbox', 'boundingBox', None),
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
    download_command = 'download_ssara_rsmas.py ' + custom_template_file + ' |& tee ' + out_file
    command = 'ssh pegasus.ccs.miami.edu \"s.cgood;cd ' + slcDir + '; ' + os.getenv(
        'PARENTDIR') + '/sources/rsmas_isce/' + download_command + '\"'
    messageRsmas.log(command)
    messageRsmas.log(download_command)
    os.chdir(slcDir)
    status = subprocess.Popen(command, shell=True).wait()
    os.chdir('..')

    download_command = 'download_asfserial_rsmas.py ' + custom_template_file + ' |& tee ' + out_file
    command = 'ssh pegasus.ccs.miami.edu \"s.cgood;cd ' + slcDir + '; ' + os.getenv(
        'PARENTDIR') + '/sources/rsmas_isce/' + download_command + '\"'
    messageRsmas.log(command)
    messageRsmas.log(download_command)
    os.chdir(slcDir)
    status = subprocess.Popen(command, shell=True).wait()
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
        print('Cleaning files:  ' + cleanlist[int(custom_template['cleanopt'])])
        if int(custom_template['cleanopt']) >= 2:
            _remove_directories(cleanlist[int(custom_template['cleanopt'])])

    command = 'pysarApp.py ' + custom_template_file + ' |& tee -a out_pysar.log'
    messageRsmas.log(command)
    # Check the performance, change in subprocess
    status = subprocess.Popen(command, shell=True)
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


def submit_isce_jobs(run_file_list, cwd, subswath, memoryuse):
    for item in run_file_list:
        memorymax = str(memoryuse[int(item.split('_')[2]) - 1])
        if os.getenv('QUEUENAME') == 'debug':
            walltimelimit = '0:30'
        else:
            walltimelimit = '4:00'  # run_1 (master) for 2 subswaths took 2:20 minutes

        if len(memoryuse) == 13:
            if item.split('_')[2] == '10':
                walltimelimit = '60:00'
        cmd = 'createBatch.pl ' + cwd + '/' + item + ' memory=' + memorymax + ' walltime=' + walltimelimit
        # FA 7/18: need more memory for run_7 (resample) only
        # FA 7/18: Should hardwire the memory requirements for the different workflows into a function and use those

        # TODO: Change subprocess call to get back error code and send error code to logger
        status = 0
    #status = subprocess.Popen(cmd, shell=True).wait()
    #if status is not 0:
    #       logger.error('ERROR submitting jobs using createBatch.pl')
    #        raise Exception('ERROR submitting jobs using createBatch.pl')

    #sswath = subswath.strip('\'').split(' ')[0]
    #print('sswath: ', subswath)

    xml_file = glob.glob('master/*.xml')[0]

    #command = 'prep4timeseries.py -i merged/interferograms/ -x ' + xml_file + ' -b baselines/ -g merged/geom_master/ '
    #messageRsmas.log(command)

    # TODO: Change subprocess call to get back error code and send error code to logger
    #status = subprocess.Popen(command, shell=True).wait()
    #if status is not 0:
    #    logger.error('ERROR in prep4timeseries.py')
    #    raise Exception('ERROR in prep4timeseries.py')

        # FA 3/2018 check_error_files_sentinelstack('run_files/run_*.e')      # exit if
        # non-zero-size or non-zero-lines run*e files are found

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
    cleanlist.append(['configs', 'baselines', 'stack',
                   'coreg_slaves', 'misreg', 'orbits',
                   'coarse_interferograms', 'ESD', 'interferograms',
                   'slaves', 'master', 'geom_master'])
    cleanlist.append(['merged'])
    cleanlist.append(['SLC'])
    cleanlist.append(['PYSAR'])
    return cleanlist

##########################################################################


def log_end_message():
    logger.debug('\n###############################################')
    logger.info('End of process_rsmas')
    logger.debug('#################################################')

##########################################################################
