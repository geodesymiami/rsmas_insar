#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import datetime
import argparse
from rinsar.objects.dataset_template import Template
from rinsar.objects.rsmas_logging import RsmasLogger, loglevel
from rinsar.objects import message_rsmas
from rinsar.utils import process_utilities as putils
from rinsar.objects.auto_defaults import PathFind
sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password
import rinsar.create_batch as cb


pathObj = PathFind()
inps = None

logfile_name = pathObj.logdir + '/ssara_rsmas.log'
logger = RsmasLogger(file_name=logfile_name)


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser.add_argument('template', metavar="FILE", help='template file to use.')
    parser.add_argument('--submit', dest='submit_flag', action='store_true', help='submits job')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    return parser.parse_args(args)


def check_downloads(inps, run_number, args):
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
            run_ssara(inps.template, run_number + 1)
            return

    logger.log(loglevel.INFO, "Everything is there!")


def run_ssara(template, run_number=1):
    """ Runs ssara_federated_query-cj.py and checks for download issues.
        Runs ssara_federated_query-cj.py and checks continuously for whether the data download has hung without
        comleting or exited with an error code. If either of the above occur, the function is run again, for a
        maxiumum of 10 times.
        Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
        Returns: status_cod: int, the status of the donwload (0 for failed, 1 for success)
    """

    logger.log(loglevel.INFO, "RUN NUMBER: %s", str(run_number))
    if run_number > 10:
        return 0

    logger.log(loglevel.INFO, "PASSED RUN NUMBER > 10")

    # Compute SSARA options to use

    dataset_template = Template(template)

    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')
    logger.log(loglevel.INFO, "GENERATED SSARAOPT STRING")

    # add intersectWith to ssaraopt string
    ssaraopt = add_polygon_to_ssaraopt(dataset_template, ssaraopt=ssaraopt)

    # get kml file and create listing
    get_ssara_kml_and_listing(ssaraopt=ssaraopt)

    # Runs ssara_federated_query-cj.py with proper options
    ssara_call = ['ssara_federated_query-cj.py'] + ssaraopt + ['--print', '--download']
    print('Download data using:\n' + ' '.join(ssara_call))
    messageRsmas.log(' '.join(ssara_call))
    ssara_process = subprocess.Popen(' '.join(ssara_call), shell=True)

    logger.log(loglevel.INFO, "STARTED PROCESS")

    completion_status = ssara_process.poll()  # the completion status of the process
    hang_status = False  # whether or not the download has hung
    wait_time = 2  # 10 wait time in 'minutes' to determine hang status
    prev_size = -1  # initial download directory size
    i = 0  # index for waiting periods (for calculation of total time only)

    logger.log(loglevel.INFO, "INITIAL COMPLETION STATUS: %s", str(completion_status))

    # while the process has not completed
    while completion_status is None:

        i = i + 1

        # Computer the current download directory size
        curr_size = int(subprocess.check_output(['du', '-s', os.getcwd()]).split()[0].decode('utf-8'))

        # Compare the current and previous directory sizes to determine determine hang status
        if prev_size == curr_size:
            hang_status = True
            logger.log(loglevel.WARNING, "SSARA Hung")
            ssara_process.terminate()  # teminate the process beacause download hung
            break;  # break the completion loop

        prev_size = curr_size  # store current size for comparison after waiting

        time.sleep(60 * wait_time)  # wait 'wait_time' minutes before continuing (checking for completion)
        completion_status = ssara_process.poll()
        logger.log(loglevel.INFO,
                   "{} minutes: {:.1f}GB, completion_status {}".format(i * wait_time, curr_size / 1024 / 1024,
                                                                       completion_status))

    exit_code = completion_status  # get the exit code of the command
    ssara_process.terminate()
    logger.log(loglevel.INFO, "EXIT CODE: %s", str(exit_code))

    bad_codes = [137, -9]

    # If the exit code is one that signifies an error, rerun the entire command
    if exit_code in bad_codes or hang_status:
        if exit_code in bad_codes:
            logger.log(loglevel.WARNING, "Exited with bad exit code, running again")
        if hang_status:
            logger.log(loglevel.WARNING, "Hanging, running again")

        run_ssara(template, run_number=run_number + 1)

    return 0


def get_ssara_kml_and_listing(ssaraopt):
    """download the ssara kml file and generate a file listing of granules to be downloaded"""

    ssaraopt_kml = ['--kml' if x.startswith('--parallel') else x for x in ssaraopt]
    ssaraopt_print = ['--print' if x.startswith('--parallel') else x for x in ssaraopt]
    ssaraopt_print.append('>')
    ssaraopt_print.append('ssara_listing.txt')

    ssara_call = ['ssara_federated_query.py'] + ssaraopt_kml
    print('Get KML using:\n' + ' '.join(ssara_call))
    messageRsmas.log(' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)
    ssara_call = ['ssara_federated_query.py'] + ssaraopt_print
    print('Get listing using:\n' + ' '.join(ssara_call))
    messageRsmas.log(' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)

    return None


def add_polygon_to_ssaraopt(dataset_template, ssaraopt):
    """calculates intersectsWith polygon from bbox and replace frame in ssaraopt if give"""
    bbox_list = dataset_template.get_options()['sentinelStack.boundingBox'][1:-1].split(' ')
    delta_lat = 0.2
    delta_lon = 0.1
    min_lat = float(bbox_list[0]) - delta_lat
    max_lat = float(bbox_list[1]) + delta_lat
    min_lon = float(bbox_list[2]) - delta_lon
    max_lon = float(bbox_list[3]) + delta_lon

    polygon = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}))\''.format(
        min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat, min_lon, min_lat)

    # add --polygon and remove --frame option
    ssaraopt.insert(2, polygon)
    ssaraopt = [x for x in ssaraopt if not x[0:7] == '--frame']

    return ssaraopt


if __name__ == "__main__":
    inps = command_line_parse(sys.argv[1:])

    inps.project_name = putils.get_project_name(custom_template_file=inps.template)
    inps.work_dir = putils.get_work_directory(None, inps.project_name)
    inps.slc_dir = inps.work_dir + "/SLC"

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'download_ssara_rsmas'
        job_name = inps.template.split(os.sep)[-1].split('.')[0]
        work_dir = inps.work_dir
        wall_time = '24:00'

        cb.submit_script(job_name, job_file_name, sys.argv[:], work_dir, wall_time)
        sys.exit(0)

    os.chdir(inps.work_dir)
    messageRsmas.log(os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))
    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)
    os.chdir(inps.slc_dir)

    logger.log(loglevel.INFO, "DATASET: %s", str(inps.template.split('/')[-1].split(".")[0]))
    logger.log(loglevel.INFO, "DATE: %s", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
    succesful = run_ssara(inps.template)
    logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))
    logger.log(loglevel.INFO, "------------------------------------")	
