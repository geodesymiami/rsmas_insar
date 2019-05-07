#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os, sys
import subprocess
import glob
from natsort import natsorted
import argparse
from rinsar.objects.rsmas_logging import loglevel
from rinsar.objects import message_rsmas
from rinsar.objects.auto_defaults import PathFind
from rinsar.utils.stack_run import CreateRun, run_download
from rinsar.objects.auto_defaults import correct_for_isce_naming_convention
from rinsar.utils.process_utilities import create_or_update_template
from rinsar.utils.process_utilities import make_run_list, send_logger

logger = send_logger()
pathObj = PathFind()
##############################################################################
EXAMPLE = """example:
  create_runfiles.py LombokSenAT156VV.template 
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('-s', '--step', dest='step', type=str, default='download',
                        help='Processing step: (download, process) -- Default : download')

    return parser


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps


###########################################################################################

def main(iargs=None):

    inps = command_line_parse(iargs)
    inps = create_or_update_template(inps)
    correct_for_isce_naming_convention(inps)

    os.chdir(inps.work_dir)
    
    if inps.step == 'download':
        run_download(inps)
    else:
        try:
            dem_file = glob.glob('DEM/*.wgs84')[0]
            inps.dem = dem_file
        except:
            print('DEM not exists!')
            sys.exit(1)

        runObj = CreateRun(inps)
        runObj.run_stack_workflow()
        if inps.workflow in ['interferogram', 'slc']:
            runObj.run_post_stack()

    run_file_list = make_run_list(inps.work_dir)

    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    logger.log(loglevel.INFO, "-----------------Done making Run files-------------------")

###########################################################################################


if __name__ == "__main__":
    main()
