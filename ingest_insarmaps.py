#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################


import os
import subprocess
import sys
import glob
import shutil
import argparse
from rsmas_logging import loglevel
import messageRsmas

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

from _processSteps import create_or_update_template
from _process_utilities  import get_work_directory, get_project_name, send_logger


logger  = send_logger()


##############################################################################
EXAMPLE = """example:
  ingest_insarmaps.py LombokSenAT156VV.template 
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

    hdfeos_file = glob.glob(inps.work_dir + '/PYSAR/S1*.he5')
    hdfeos_file.append(glob.glob(inps.work_dir +'/PYSAR/SUBSET_*/S1*.he5'))
    hdfeos_file = hdfeos_file[0]

    json_folder = inps.work_dir + '/PYSAR/JSON'
    mbtiles_file = json_folder + '/' + os.path.splitext(os.path.basename(hdfeos_file))[0] + '.mbtiles'

    if os.path.isdir(json_folder):
        logger.log(loglevel.INFO, 'Removing directory: {}'.format(json_folder))
        shutil.rmtree(json_folder)

    command1 = 'hdfeos5_2json_mbtiles.py ' + hdfeos_file + ' ' + json_folder + ' |& tee out_insarmaps.log'
    command2 = 'json_mbtiles2insarmaps.py -u ' + password.insaruser + ' -p ' + password.insarpass + ' --host ' + \
               'insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder ' + \
               json_folder + ' --mbtiles_file ' + mbtiles_file + ' |& tee -a out_insarmaps.log'

    with open(inps.work_dir + '/PYSAR/run_insarmaps', 'w') as f:
        f.write(command1 + '\n')
        f.write(command2 + '\n')


    out_file = 'out_insarmaps'
    logger.log(loglevel.INFO, command1)
    messageRsmas.log(command1)
    command1 = '('+command1+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    status = subprocess.Popen(command1, shell=True).wait()
    if status is not 0:
        logger.log(loglevel.ERROR, 'ERROR in hdfeos5_2json_mbtiles.py')
        raise Exception('ERROR in hdfeos5_2json_mbtiles.py')


    # TODO: Change subprocess call to get back error code and send error code to logger
    logger.log(loglevel.INFO, command2)
    messageRsmas.log(command2)
    command2 = '('+command2+' | tee -a '+out_file+'.o) 3>&1 1>&2 2>&3 | tee -a '+out_file+'.e'
    status = subprocess.Popen(command2, shell=True).wait()
    if status is not 0:
        logger.log(loglevel.ERROR, 'ERROR in json_mbtiles2insarmaps.py')
        raise Exception('ERROR in json_mbtiles2insarmaps.py')


    logger.log(loglevel.INFO, "-----------------Done ingesting insarmaps-------------------")
