#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os, sys
import subprocess
import glob

import argparse
from rain.objects.rsmas_logging import loglevel
from rain.objects import messageRsmas

from rain.utils.process_utilities import create_or_update_template, create_or_copy_dem
from rain.utils.process_utilities import get_work_directory, get_project_name
from rain.utils.process_utilities import _remove_directories, send_logger

logger = send_logger()

##############################################################################
EXAMPLE = """example:
  create_stacksentinel_run_files.py LombokSenAT156VV.template 
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('-s', '--step', dest='step', type=str, default='preprocess',
                        help='Processing step: (preprocess, mainprocess, postprocess) -- Default : preprocess')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args)

    return inps


###########################################################################################

def main(argv):

    inps = command_line_parse(argv[:])
    inps.project_name = get_project_name(inps.customTemplateFile)
    inps.work_dir = get_work_directory(None, inps.project_name)
    inps = create_or_update_template(inps)
    os.chdir(inps.work_dir)

    if inps.step == 'preprocess':

        if os.path.exists(os.path.join(inps.work_dir, 'pre_run_files')):
            print('')
            print('**************************')
            print('pre_run_files folder exists.')
            print(os.path.join(inps.work_dir, 'pre_run_files'), ' already exists.')
            print('Please remove or rename this folder and try again.')
            print('')
            print('**************************')
        else:
            from insar.utils.stackRsmas import preprocessStack
            preprocessStack(inps, i=0)

            run_file_list = glob.glob(inps.work_dir + '/pre_run_files/run_*')
            with open(inps.work_dir + '/pre_run_files_list', 'w') as run_file:
                for item in run_file_list:
                    run_file.writelines(item + '\n')



    elif inps.step == 'mainprocess':

        inps.slcDir = inps.work_dir + '/SLC'
        try:
            files1 = glob.glob(inps.work_dir + '/DEM/*.wgs84')[0]
            files2 = glob.glob(inps.work_dir + '/DEM/*.dem')[0]
            dem_file = [files1, files2]
            dem_file = dem_file[0]
        except:
            dem_file = create_or_copy_dem(work_dir=inps.work_dir,
                                          template=inps.template,
                                          custom_template_file=inps.customTemplateFile)

        inps.demDir = dem_file
        command = 'stackSentinel.py'

        if inps.processingMethod == 'squeesar':
            inps.workflow = 'slc'

        prefixletters = ['-slc_directory', '-orbit_directory', '-aux_directory', '-working_directory',
                         '-dem', '-master_date', '-num_connections', '-num_overlap_connections',
                         '-swath_num', '-bbox', '-exclude_dates', '-include_dates', '-azimuth_looks',
                         '-range_looks', '-filter_strength', '-esd_coherence_threshold', '-snr_misreg_threshold',
                         '-unw_method', '-polarization', '-coregistration', '-workflow',
                         '-start_date', '-stop_date', '-text_cmd']

        inpsvalue = ['slcDir', 'orbitDir', 'auxDir', 'workingDir', 'demDir', 'masterDir',
                     'numConnections', 'numOverlapConnections', 'subswath', 'boundingBox',
                     'excludeDate', 'includeDate', 'azimuthLooks', 'rangeLooks', 'filtStrength',
                     'esdCoherenceThreshold', 'snrThreshold', 'unwMethod', 'polarization',
                     'coregistration', 'workflow', 'startDate', 'stopDate', 'textCmd']

        for value, pref in zip(inpsvalue, prefixletters):
            keyvalue = eval('inps.' + value)
            if keyvalue is not None:
                command = command + ' -' + str(pref) + ' ' + str(keyvalue)

        out_file = 'out_create_runfiles'
        command = '(' + command + ' | tee ' + out_file + '.o) 3>&1 1>&2 2>&3 | tee ' + out_file + '.e'

        logger.log(loglevel.INFO, command)
        messageRsmas.log(command)

        temp_list = ['run_files', 'configs', 'orbits']
        _remove_directories(temp_list)

        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.log(loglevel.ERROR, 'ERROR making run_files using {}'.format(script))
            raise Exception('ERROR making run_files using {}'.format(script))

        run_file_list = glob.glob(inps.work_dir + '/run_files/run_*')
        with open(inps.work_dir + '/run_files_list', 'w') as run_file:
            for item in run_file_list:
                run_file.writelines(item + '\n')


    else:
        temp_list = ['post_run_files', 'post_configs']
        _remove_directories(temp_list)

        print('inps:\n', inps)

        inps.bbox = '"{} {} {} {}"'.format(inps.custom_template['lat_south'], inps.custom_template['lat_north'],
                                              inps.custom_template['lon_west'], inps.custom_template['lon_east'])

        command = 'stackRsmas.py'

        items = ['squeesar.plmethod', 'squeesar.patch_size', 'squeesar.range_window', 'squeesar.azimuth_window']
        inpspar = []
        defaultval = ['sequential_EMI', '200', '21', '15']

        for item, idef in zip(items, defaultval):
            try:
                inpspar.append(inps.custom_template[item])
            except:
                inpspar.append(idef)

        inps.plmethod = inpspar[0]
        inps.patch_size = inpspar[1]
        inps.range_window = inpspar[2]
        inps.azimuth_window = inpspar[3]
        inps.slcDir = inps.work_dir + '/SLC'
        inps.technique = inps.processingMethod

        prefixletters = ['-customTemplateFile', '-slc_directory', '-working_directory', '-technique',
                         '-patchsize', '-plmethod', '-range_window', '-azimuth_window', '-bbox',
                         '-exclude_dates', '-azimuth_looks', '-range_looks', '-unw_method',
                         '-text_cmd']

        inpsvalue = ['customTemplateFile', 'slcDir', 'workingDir', 'technique', 'patch_size', 'plmethod',
                     'range_window', 'azimuth_window', 'bbox', 'excludeDate', 'azimuthLooks', 'rangeLooks',
                     'unwMethod', 'textCmd']

        for value, pref in zip(inpsvalue, prefixletters):
            keyvalue = eval('inps.' + value)
            if keyvalue is not None:
                command = command + ' -' + str(pref) + ' ' + str(keyvalue)

        print(command)

        out_file = 'out_create_runfiles'
        command = '(' + command + ' | tee ' + out_file + '.o) 3>&1 1>&2 2>&3 | tee ' + out_file + '.e'

        logger.log(loglevel.INFO, command)
        messageRsmas.log(command)

        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            logger.log(loglevel.ERROR, 'ERROR making run_files using {}'.format(script))
            raise Exception('ERROR making run_files using {}'.format(script))

        run_file_list = glob.glob(inps.work_dir + '/post_run_files/run_*')
        with open(inps.work_dir + '/post_run_files_list', 'w') as run_file:
            for item in run_file_list:
                run_file.writelines(item + '\n')


    logger.log(loglevel.INFO, "-----------------Done making Run files-------------------")

###########################################################################################

if __name__ == "__main__":
    main(sys.argv[:])