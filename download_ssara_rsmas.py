#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import datetime
import argparse
from dataset_template import Template
from rsmas_logging import rsmas_logger, loglevel
import messageRsmas
import _process_utilities as putils

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

inps = None

logfile_name = os.getenv('OPERATIONS') + '/LOGS/ssara_rsmas.log'
logger = rsmas_logger(file_name=logfile_name)


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser.add_argument('template', metavar="FILE", help='template file to use.')

    return parser

def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    global inps

    parser = create_parser()
    inps = parser.parse_args(args)

def check_downloads(run_number, args):
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
            logger.log(logging.WARNING, "The file, %s, didn't download correctly. Running ssara again.")
            run_ssara(run_number + 1)
            return

    logger.log(loglevel.INFO, "Everything is there!")


def generate_ssaraopt_string(template_file):
    """ generates ssaraopt string from ssaraopt.* in template_file. If not given returns ssaraopt proper
        Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
        Returns: ssaraopt: str, the string with the options to call ssara_federated_query.py
    """
    # use ssaraopt.platform, relativeOrbit and frame if given, else use ssaraopt
    try:
       platform = Template(template_file).get_options()['ssaraopt.platform']
       relativeOrbit = Template(template_file).get_options()['ssaraopt.relativeOrbit']
       frame = Template(template_file).get_options()['ssaraopt.frame']
       ssaraopt='--platform='+platform+' --relativeOrbit='+relativeOrbit+' --frame='+frame

       try:
          startDate = Template(template_file).get_options()['ssaraopt.startDate']
          ssaraopt=ssaraopt+' -s='+startDate
       except:
          pass
       try:
          endDate = Template(template_file).get_options()['ssaraopt.endDate']
          ssaraopt=ssaraopt+' -e='+endDate
       except:
          pass

    except:
       try: 
         ssaraopt = Template(template_file).get_options()['ssaraopt']
       except:
         raise Exception('no ssaraopt or ssaraopt.platform, relativeOrbit, frame found')

    # add parallel doenload option. If ssaraopt.parallelDownload not given use default value
    try:
       parallelDownload = Template(template_file).get_options()['ssaraopt.parallelDownload']
    except:
       parallelDownload = '30'     # default
    ssaraopt=ssaraopt+' --parallel='+parallelDownload

    return ssaraopt
    
def run_ssara(run_number=1):
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

    # Compute SSARA options to use 

    ssaraopt =  generate_ssaraopt_string(template_file=inps.template)

    ssaraopt = ssaraopt.split(' ')

    # Runs ssara_federated_query-cj.py with proper options
    ssara_call    = ['ssara_federated_query-cj.py'] + ssaraopt + ['--print', '--download']
    ssara_process = subprocess.Popen(ssara_call)

    completion_status = ssara_process.poll()  # the completion status of the process
    hang_status = False  # whether or not the download has hung
    wait_time =  2  # 10 wait time in 'minutes' to determine hang status
    prev_size = -1  # initial download directory size
    i = 0  # the iteration number (for logging only)

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

        time.sleep(60 * wait_time)  # wait 'wait_time' minutes before continuing
        prev_size = curr_size
        completion_status = ssara_process.poll()
        logger.log(loglevel.INFO, "{} minutes: {:.1f}GB, completion_status {}".format(i * wait_time, curr_size / 1024 / 1024,
                                                                        completion_status))

    exit_code = completion_status  # get the exit code of the command
    logger.log(loglevel.INFO, "EXIT CODE: %s", str(exit_code))

    bad_codes = [137]

    # If the exit code is one that signifies an error, rerun the entire command
    if exit_code in bad_codes or hang_status:
        logger.log(loglevel.WARNING, "Something went wrong, running again")
        run_ssara(run_number=run_number + 1)

    return 1

if __name__ == "__main__":
    command_line_parse(sys.argv[1:])

    inps.project_name = putils.get_project_name(custom_template_file=inps.template)
    inps.work_dir = putils.get_work_directory(None, inps.project_name)
    inps.slcDir = putils.get_slc_directory(inps.work_dir)
    os.chdir(inps.work_dir)
    messageRsmas.log(os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1::]))
    os.chdir(inps.slcDir)

    logger.log(loglevel.INFO, "DATASET: %s", str(inps.template.split('/')[-1].split(".")[0]))
    logger.log(loglevel.INFO, "DATE: %s", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
    succesful = run_ssara()
    logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))
    logger.log(loglevel.INFO, "------------------------------------")				
