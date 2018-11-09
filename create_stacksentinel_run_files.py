#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import logging
import os
import subprocess
import sys
import glob

import argparse
from rsmas_logging import rsmas_logger, loglevel
import messageRsmas

from _processSteps import create_or_update_template, create_or_copy_dem
from _process_utilities  import get_work_directory, get_project_name
from _process_utilities  import set_default_options, _remove_directories

sys.path.insert(0, os.getenv('SENTINEL_STACK'))
sys.path.insert(0, os.getenv('SQUEESAR'))

logfile_name = os.getenv('OPERATIONS') + '/LOGS/create_stacksentinel_run_files.log'
logger = rsmas_logger(file_name=logfile_name)


##############################################################################
EXAMPLE = """example:
  create_stacksentinel_run_files.py LombokSenAT156VV.template 
"""

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('custom_template_file', nargs='?',
                        help='custom template with option settings.\n')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args)
    
    return inps



if __name__ == "__main__":

    inps = command_line_parse(sys.argv[1:])
    inps.project_name = get_project_name(inps.custom_template_file)
    inps.work_dir = get_work_directory(None, inps.project_name)
    inps = create_or_update_template(inps)
    os.chdir(inps.work_dir)


    try:
        files1 = glob.glob(inps.work_dir + '/DEM/*.wgs84')[0]
        files2 = glob.glob(inps.work_dir + '/DEM/*.dem')[0]
        dem_file = [files1, files2]
        dem_file = dem_file[0]
    except:
        dem_file = create_or_copy_dem(work_dir=inps.work_dir,
                                             template=inps.template,
                                             custom_template_file=inps.custom_template_file)

    inps.demDir = dem_file
    script = 'stackSentinel.py'
    extraOptions = ''
    if inps.processingMethod == 'squeesar' or inps.processingMethod == 'ps':
        script = 'stackSentinel_squeesar.py'
        extraOptions = '--processingmethod' + inps.processingMethod

    prefixletters = ['-slc_directory', '-orbit_directory', '-aux_directory', '-working_directory', 
                     '-dem', '-master_date', '-num_connections', '-num_overlap_connections', 
                     '-swath_num', '-bbox', '-exclude_dates', '-include_dates', '-azimuth_looks',
                     '-range_looks', '-filter_strength', '-esd_coherence_threshold', '-snr_misreg_threshold', 
                     '-unw_method', '-polarization', '-coregistration', '-workflow',
                     '-start_date', '-stop_date', '-text_cmd', '-useGPU', '-use_virtual_files',
                     'ilist', 'clean_up', 'layover_msk', 'water_msk']
    
    inpsvalue = ['slcDir', 'orbitDir', 'auxDir', 'workingDir', 'demDir', 'masterDir',
                 'numConnections', 'numOverlapConnections', 'subswath', 'boundingBox',
                 'excludeDate', 'includeDate', 'azimuthLooks', 'rangeLooks', 'filtStrength',
                 'esdCoherenceThreshold', 'snrThreshold', 'unwMethod', 'polarization',
                 'coregistration', 'workflow', 'startDate', 'stopDate', 'textCmd', 'useGPU',
                 'useVirtualFiles', 'ilist', 'cleanup', 'layovermsk', 'watermsk']

    command = script + extraOptions

    for value, pref in zip(inpsvalue, prefixletters):
        keyvalue = eval('inps.' + value)
        if keyvalue is not None:
            command = command + ' -' + str(pref) + ' ' + str(keyvalue)
            
    if inps.ilistonly == 'yes': 
        command = command + ' -ilistonly'
    if inps.force == 'yes': 
        command = command + ' --force'
    
    out_file = 'out_stackSentinel_create_runfiles'
    command = '('+command+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    
    logger.log(loglevel.INFO, command)
    messageRsmas.log(command)
    
    temp_list = ['run_files', 'configs', 'orbits']
    _remove_directories(temp_list)

    #process = subprocess.Popen( command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #(error, output) = process.communicate()    # FA 11/18: changed order (was output,error) because of stream redirecting
    #if process.returncode is not 0 or error or 'Traceback' in output.decode("utf-8"):
    status = subprocess.Popen( command, shell=True).wait()
    if status is not 0: 
        logger.log(loglevel.ERROR, 'ERROR making run_files using {}'.format(script))
        raise Exception('ERROR making run_files using {}'.format(script))


    run_file_list = glob.glob(inps.work_dir + '/run_files/run_*')
    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    logger.log(loglevel.INFO, "-----------------Done making Run files-------------------")
