#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import datetime
import argparse
from minsar.objects.dataset_template import Template
from minsar.objects.rsmas_logging import RsmasLogger, loglevel
from minsar.objects import message_rsmas
from minsar.utils import process_utilities as putils
from minsar.objects.auto_defaults import PathFind
from minsar.job_submission import JOB_SUBMIT

pathObj = PathFind()
inps = None


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    logfile_name = inps.work_dir + '/ssara_rsmas.log'
    logger = RsmasLogger(file_name=logfile_name)

    #import pdb; pdb.set_trace()
    if not inps.template[inps.prefix + 'Stack.slcDir'] is None:
        inps.download_dir = inps.template[inps.prefix + 'Stack.slcDir']

    if 'COSMO' in inps.template['ssaraopt.platform']:
        inps.download_dir = os.path.join(inps.work_dir, 'RAW_data')
    else:
        inps.download_dir = os.path.join(inps.work_dir, 'SLC')

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'download_ssara_rsmas'
        job_name = inps.custom_template_file.split(os.sep)[-1].split('.')[0]
        job_obj = JOB_SUBMIT(inps)
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)
        sys.exit(0)

    if not os.path.isdir(inps.download_dir):
        os.makedirs(inps.download_dir)
    os.chdir(inps.download_dir)

    succesful = run_ssara(inps.download_dir, inps.custom_template_file, inps.delta_lat, logger)

    return None


def check_downloads(inps, run_number, args, logger):
    """ Checks if all of the ssara files to be dwonloaded actually exist.

        Checks if the files to be downloaded actually exist or not on the system as a means of validating
        whether or not the wrapper completed succesfully.

        Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
                    args: [string], ssara_federated_query.py options to run with

        Returns: none

    """
    ssara_output = subprocess.check_output(['ssara_federated_query-cj.py'] + args[1:len(args)] + ["--print"])
    ssara_output_array = ssara_output.decode('utf-8').split('\n')
    ssara_output_filtered = ssara_output_array[5:len(ssara_output_array) - 1]

    files_to_check = []
    for entry in ssara_output_filtered:
        files_to_check.append(entry.split(',')[-1].split('/')[-1])

    for f in files_to_check:
        if not os.path.isfile(str(os.getcwd()) + "/" + str(f)):
            logger.log(loglevel.WARNING, "The file, %s, didn't download correctly. Running ssara again.")
            run_ssara(inps.download_dir, inps.custom_template_file, delta_lat, logger, run_number + 1)
            return

    logger.log(loglevel.INFO, "Everything is there!")


def run_ssara(download_dir, template, delta_lat, logger, run_number=1):
    """ Runs ssara_federated_query-cj.py and checks for download issues.
        Runs ssara_federated_query-cj.py and checks continuously for whether the data download has hung without
        comleting or exited with an error code. If either of the above occur, the function is run again, for a
        maxiumum of 10 times.
        Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
        Returns: status_cod: int, the status of the donwload (0 for failed, 1 for success)
    """

    # Compute SSARA options to use

    dataset_template = Template(template)
    dataset_template.options.update(pathObj.correct_for_ssara_date_format(dataset_template.options))

    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')

    # add intersectWith to ssaraopt string
    ssaraopt = add_polygon_to_ssaraopt(dataset_template.get_options(), ssaraopt.copy(), delta_lat)

    # get kml file and create listing
    get_ssara_kml(download_dir, ssaraopt=ssaraopt)

    # Runs ssara_federated_query.bash with proper options
    ssara_call = ['ssara_federated_query.bash'] + ssaraopt + ['--print', '--download']

    #FA 9/20: I could not figure out how to get the string into a bash shell variable, that is why writing a file
    #print( ' '.join(ssara_call) )

    with open('../ssara_command.txt', 'w') as f:
        f.write(' '.join(ssara_call) + '\n')

    return 


def get_ssara_kml(download_dir, ssaraopt):
    """download the ssara kml file and generate a file listing of granules to be downloaded"""

    ssaraopt_kml = ['--kml --maxResults=20000' if x.startswith('--parallel') else x for x in ssaraopt]

    ssara_call = ['ssara_federated_query.py'] + ssaraopt_kml
    print('Get KML using:\n' + ' '.join(ssara_call))
    message_rsmas.log(download_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)

    return None


def add_polygon_to_ssaraopt(dataset_template, ssaraopt, delta_lat):
    """calculates intersectsWith polygon from bbox and replace frame in ssaraopt if give"""
    
    if not 'acquisition_mode' in dataset_template:
        print('WARNING: "acquisition_mode" is not given --> default: tops   (available options: tops, stripmap)')
        prefix = 'tops'
    else:
        prefix = dataset_template['acquisition_mode']

    bbox_list = dataset_template[prefix + 'Stack.boundingBox'].split(' ')

    bbox_list[0] = bbox_list[0].replace("\'", '')   # this does ["'-8.75", '-7.8', '115.0', "115.7'"] (needed for run_operations.py, run_operations
    bbox_list[1] = bbox_list[1].replace("\'", '')   # -->       ['-8.75',  '-7.8', '115.0', '115.7']  (should be modified so that this is not needed)
    bbox_list[2] = bbox_list[2].replace("\'", '')
    bbox_list[3] = bbox_list[3].replace("\'", '')

    delta_lon = delta_lat * 0.2
    min_lat = float(bbox_list[0]) - delta_lat
    max_lat = float(bbox_list[1]) + delta_lat
    min_lon = float(bbox_list[2]) - delta_lon
    max_lon = float(bbox_list[3]) + delta_lon

    polygon = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, ' \
              '{:.2f} {:.2f}))\''.format(min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat,
                                         min_lon, min_lat)

    # add --polygon and remove --frame option
    ssaraopt.insert(2, polygon)
    ssaraopt = [x for x in ssaraopt if not x[0:7] == '--frame']

    return ssaraopt

def add_point_to_ssaraopt(dataset_template, ssaraopt):
    """calculates intersectsWith polygon from bbox and replace frame in ssaraopt if give"""
    
    if not 'acquisition_mode' in dataset_template:
        print('WARNING: "acquisition_mode" is not given --> default: tops   (available options: tops, stripmap)')
        prefix = 'tops'
    else:
        prefix = dataset_template['acquisition_mode']

    point = dataset_template['ssaraopt.intersectsWithPoint'].split(' ')
    bbox_list = dataset_template[prefix + 'Stack.boundingBox'].split(' ')

    point[0] = point[0].replace("\'", '')   # this does ["'-8.75", '-7.8', '115.0', "115.7'"] (needed for run_operations.py, run_operations
    point[1] = point[1].replace("\'", '')   # -->       ['-8.75',  '-7.8', '115.0', '115.7']  (should be modified so that this is not needed)

    point = '--intersectsWith=\'Point({:.2f} {:.2f})\''.format( float(point[0]), float(point[1]))

    # add --point and remove --frame option
    ssaraopt.insert(2, point)

    ssaraopt = [x for x in ssaraopt if not x[0:7] == '--frame']

    return ssaraopt

if __name__ == "__main__":
    main()
