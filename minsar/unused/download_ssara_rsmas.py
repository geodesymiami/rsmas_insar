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

    if not inps.template[inps.prefix + 'Stack.slcDir'] is None:
        inps.slc_dir = inps.template[inps.prefix + 'Stack.slcDir']
    else:
        inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    project_slc_dir = os.path.join(inps.work_dir, 'SLC')
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

    if not os.path.isdir(project_slc_dir):
        os.makedirs(project_slc_dir)
    os.chdir(inps.slc_dir)

    logger.log(loglevel.INFO, "DATASET: %s", str(inps.custom_template_file.split('/')[-1].split(".")[0]))
    logger.log(loglevel.INFO, "DATE: %s", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
    succesful = run_ssara(project_slc_dir, inps.custom_template_file, inps.delta_lat, logger)
    logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))
    logger.log(loglevel.INFO, "------------------------------------")

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
            run_ssara(inps.slc_dir, inps.custom_template_file, delta_lat, logger, run_number + 1)
            return

    logger.log(loglevel.INFO, "Everything is there!")


def run_ssara(slc_dir, template, delta_lat, logger, run_number=1):
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
    dataset_template.options.update(pathObj.correct_for_ssara_date_format(dataset_template.options))

    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')
    logger.log(loglevel.INFO, "GENERATED SSARAOPT STRING")

    # add intersectWith to ssaraopt string
    ssaraopt = add_polygon_to_ssaraopt(dataset_template.get_options(), ssaraopt.copy(), delta_lat)

    # get kml file and create listing
    get_ssara_kml_and_listing(slc_dir, ssaraopt=ssaraopt)

    # Runs ssara_federated_query-cj.py with proper options
    ssara_call = ['ssara_federated_query-cj.py'] + ssaraopt + ['--print', '--download']
    print('Download data using:\n' + ' '.join(ssara_call))
    message_rsmas.log(slc_dir, ' '.join(ssara_call))
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
            break  # break the completion loop

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

        run_ssara(slc_dir, template, delta_lat, logger, run_number=run_number + 1)

    return 0


def get_ssara_kml_and_listing(slc_dir, ssaraopt):
    """download the ssara kml file and generate a file listing of granules to be downloaded"""

    ssaraopt_kml = ['--kml' if x.startswith('--parallel') else x for x in ssaraopt]
    ssaraopt_print = ['--print' if x.startswith('--parallel') else x for x in ssaraopt]
    ssaraopt_print.append('>')
    ssaraopt_print.append(os.path.join(slc_dir, 'ssara_listing.txt'))

    ssara_call = ['ssara_federated_query.py'] + ssaraopt_kml
    print('Get KML using:\n' + ' '.join(ssara_call))
    message_rsmas.log(slc_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)
    ssara_call = ['ssara_federated_query.py'] + ssaraopt_print
    print('Get listing using:\n' + ' '.join(ssara_call))
    message_rsmas.log(slc_dir, ' '.join(ssara_call))
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
