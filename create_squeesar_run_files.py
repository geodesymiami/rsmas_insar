#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import subprocess
import sys
import glob

import argparse
from rsmas_logging import loglevel
import messageRsmas

from _processSteps import create_or_update_template, create_or_copy_dem
from _process_utilities  import get_work_directory, get_project_name
from _process_utilities  import _remove_directories, send_logger

logger  = send_logger()

##############################################################################
EXAMPLE = """example:
  create_squeesar_run_files.py LombokSenAT156VV.template 
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

    temp_list = ['run_files_SQ', 'configs_SQ']
    _remove_directories(temp_list)

    print('inps:\n', inps)

    inps.cropbox = '"{} {} {} {}"'.format(inps.custom_template['lat_south'], inps.custom_template['lat_north'],
                                        inps.custom_template['lon_west'], inps.custom_template['lon_east'])

    command = 'stackSentinel_squeesar.py'

    items = ['squeesar.plmethod','squeesar.patch_size','squeesar.range_window','squeesar.azimuth_window']
    inpspar = []
    defaultval = ['sequential_EMI','200','21','15']


    for item,idef in zip(items,defaultval):
        try:
            inpspar.append(inps.custom_template[item])
        except:
            inpspar.append(idef)

    inps.plmethod = inpspar[0]
    inps.patch_size = inpspar[1]
    inps.range_window = inpspar[2]
    inps.azimuth_window = inpspar[3]
    inps.slcDir = inps.work_dir+'/merged/SLC'


    prefixletters = ['-customTemplateFile', '-slc_directory', '-working_directory',
                     '-patchsize', '-plmethod', '-range_window', '-azimuth_window', '-cropbox',
                     '-exclude_dates', '-azimuth_looks', '-range_looks', '-unw_method',
                     '-text_cmd']
    
    inpsvalue = ['custom_template_file', 'slcDir', 'workingDir', 'patch_size', 'plmethod',
                 'range_window', 'azimuth_window', 'cropbox', 'excludeDate', 'azimuthLooks', 'rangeLooks',
                 'unwMethod', 'textCmd']



    for value, pref in zip(inpsvalue, prefixletters):
        keyvalue = eval('inps.' + value)
        if keyvalue is not None:
            command = command + ' -' + str(pref) + ' ' + str(keyvalue)

    print(command)
    
    out_file = 'out_squeesar_create_runfiles'
    command = '('+command+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    
    logger.log(loglevel.INFO, command)
    messageRsmas.log(command)
    


    status = subprocess.Popen( command, shell=True).wait()
    if status is not 0: 
        logger.log(loglevel.ERROR, 'ERROR making run_files using {}'.format(script))
        raise Exception('ERROR making run_files using {}'.format(script))


    run_file_list = glob.glob(inps.work_dir + '/run_files_SQ/run_*')
    with open(inps.work_dir + '/run_files_list_sq', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    logger.log(loglevel.INFO, "-----------------Done making Run files-------------------")
