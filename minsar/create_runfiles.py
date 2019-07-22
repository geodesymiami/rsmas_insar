#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import argparse
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun, run_download
from minsar.utils.process_utilities import create_or_update_template
from minsar.utils.process_utilities import make_run_list

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

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    os.chdir(inps.work_dir)
    
    if inps.step == 'download':
        run_download(inps)
    else:
        try:
            dem_file = glob.glob('DEM/*.wgs84')[0]
            inps.template['topsStack.demDir'] = dem_file
        except:
            print('DEM not exists!')
            sys.exit(1)

        pathObj.correct_for_isce_naming_convention(inps)
        runObj = CreateRun(inps)
        runObj.run_stack_workflow()
        if inps.template['workflow'] in ['interferogram', 'slc']:
            runObj.run_post_stack()

    run_file_list = make_run_list(inps.work_dir)

    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

###########################################################################################


if __name__ == "__main__":
    main()
