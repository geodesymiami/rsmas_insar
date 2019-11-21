#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import time
from minsar.objects.dataset_template import Template
from minsar.objects.rsmas_logging import RsmasLogger, loglevel
from minsar.objects import message_rsmas
from minsar.utils import process_utilities as putils
from minsar.utils.download_ssara_rsmas import add_polygon_to_ssaraopt
import minsar.job_submission as js
import glob
from minsar.objects.auto_defaults import PathFind
import password_config as password


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    logfile_name = inps.work_dir + '/asfserial_rsmas.log'
    logger = RsmasLogger(file_name=logfile_name)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'download_asfserial_rsmas'
        job_name = inps.custom_template_file.split(os.sep)[-1].split('.')[0]
        work_dir = inps.work_dir

        if inps.wall_time == 'None':
            inps.wall_time = config['download_rsmas']['walltime']

        js.submit_script(job_name, job_file_name, sys.argv[:], work_dir, inps.wall_time)

    os.chdir(inps.work_dir)

    if not inps.template['topsStack.slcDir'] is None:
        inps.slc_dir = inps.template['topsStack.slcDir']
    else:
        inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    project_slc_dir = os.path.join(inps.work_dir, 'SLC')

    os.chdir(inps.slc_dir)

    try:
        os.remove(os.path.expanduser('~') + '/.bulk_download_cookiejar.txt')
    except OSError:
        pass
    
    dataset_template = Template(inps.custom_template_file)
    dataset_template.options.update(PathFind.correct_for_ssara_date_format(dataset_template.options))
    subprocess.Popen("rm new_files.csv", shell=True).wait()
    standardTuple = (inps, dataset_template)
    if inps.seasonalStartDate is not None and inps.seasonalEndDate is not None:
        ogStartYearInt = int(dataset_template.options['ssaraopt.startDate'][:4])
        if int(inps.seasonalStartDate) > int(inps.seasonalEndDate):
            y = 1
        else:
            y = 0
        YearRange = int(dataset_template.options['ssaraopt.endDate'][:4]) - ogStartYearInt + 1
        if YearRange > 1 and y == 1:
            YearRange = YearRange - 1
        seasonalStartDateAddOn = '-' + inps.seasonalStartDate[:2] + '-' + inps.seasonalStartDate[2:]
        seasonalEndDateAddOn = '-' + inps.seasonalEndDate[:2] + '-' + inps.seasonalEndDate[2:]
        ogEndDate = dataset_template.options['ssaraopt.endDate']
        for x in range(YearRange):
            seasonalTuple = standardTuple + (x, ogStartYearInt, y, YearRange, seasonalStartDateAddOn, seasonalEndDateAddOn, ogEndDate)
            generate_files_csv(project_slc_dir, inps.custom_template_file, seasonalTuple)
            y += 1
    else:
        generate_files_csv(project_slc_dir, inps.custom_template_file, standardTuple)
    succesful = run_download_asf_serial(project_slc_dir, logger)
    change_file_permissions()
    logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))
    logger.log(loglevel.INFO, "------------------------------------")

    return None


def generate_files_csv(slc_dir, custom_template_file, tupleParam):
    """ Generates a csv file of the files to download serially.
    Uses the `awk` command to generate a csv file containing the data files to be download
    serially. The output csv file is then sent through the `sed` command to remove the first five
    empty values to eliminate errors in download_ASF_serial.py.
    """
    
    inps = tupleParam[0]
    dataset_template = tupleParam[1]
    if inps.seasonalStartDate is not None and inps.seasonalEndDate is not None:
        x = tupleParam[2]
        ogStartYearInt = tupleParam[3]
        y = tupleParam[4]
        YearRange = tupleParam[5]
        seasonalStartDateAddOn = tupleParam[6]
        seasonalEndDateAddOn = tupleParam[7]
        ogEndDate = tupleParam[8]
        if x == 0:
            if YearRange == 1:
                if y == 0:
                    if int(inps.seasonalEndDate) < int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')) or int(inps.seasonalStartDate) > int(ogEndDate[4:].replace('-', '')):
                        return
                    else:
                        if int(inps.seasonalStartDate) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                            dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt) + seasonalStartDateAddOn
                        if int(inps.seasonalEndDate) < int(ogEndDate[4:].replace('-', '')):
                            dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt) + seasonalEndDateAddOn
                elif int(dataset_template.options['ssaraopt.endDate'][:4]) - ogStartYearInt + 1 == 1:
                    if int(inps.seasonalStartDate) > int(ogEndDate[4:].replace('-', '')):
                        return
                    elif int(inps.seasonalStartDate) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                        dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt) + seasonalStartDateAddOn
                else:
                    if int(inps.seasonalStartDate) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                        dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt) + seasonalStartDateAddOn
                    if int(inps.seasonalEndDate) < int(ogEndDate[4:].replace('-', '')):
                        dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt + y) + seasonalEndDateAddOn
            else:
                if y == 0:
                    if int(inps.seasonalEndDate) < int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                        return
                    else: 
                        if int(inps.seasonalStartDate) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                            dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt) + seasonalStartDateAddOn
                        dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt) + seasonalEndDateAddOn
                else:
                    if int(inps.seasonalStartDate) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                        dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt) + seasonalStartDateAddOn
                    dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt + y) + seasonalEndDateAddOn
        elif x < YearRange - 1:
            dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt + x) + seasonalStartDateAddOn
            dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt + y) + seasonalEndDateAddOn
        elif x == YearRange - 1:
            if int(inps.seasonalEndDate) < int(ogEndDate[4:].replace('-', '')):
                dataset_template.options['ssaraopt.endDate'] = str(ogStartYearInt + y) + seasonalEndDateAddOn
            else: 
                dataset_template.options['ssaraopt.endDate'] = ogEndDate
            dataset_template.options['ssaraopt.startDate'] = str(ogStartYearInt + x) + seasonalStartDateAddOn
    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')

    # add intersectWith to ssaraopt string #FA 8/19: the delta_lat default value should come from a command_linr parse
    ssaraopt = add_polygon_to_ssaraopt(dataset_template.get_options(), ssaraopt.copy(), delta_lat=0.0)

    filecsv_options = ['ssara_federated_query.py'] + ssaraopt + ['--print', '|', 'awk',
                                                                 "'BEGIN{FS=\",\"; ORS=\",\"}{ print $14}'", '>',
                                                                 os.path.join(slc_dir, 'files.csv')]

    csv_command = ' '.join(filecsv_options)
    message_rsmas.log(slc_dir, csv_command)
    subprocess.Popen(csv_command, shell=True).wait()
    # FA 8/2019: replaced new_files.csv by files.csv as infile argument
    sed_command = "sed 's/^.\{5\}//;s/,\{1,4\}$//' " + os.path.join(slc_dir, 'files.csv') + \
                  ">>" + os.path.join(slc_dir, 'new_files.csv')
    message_rsmas.log(slc_dir, sed_command)
    subprocess.Popen(sed_command, shell=True).wait()


def run_download_asf_serial(slc_dir, logger, run_number=1):
    """ Runs download_ASF_serial.py with proper files.
    Runs adapted download_ASF_serial.py with a CLI username and password and a csv file containing
    the the files needed to be downloaded (provided by ssara_federated_query.py --print)
    """

    logger.log(loglevel.INFO, "RUN NUMBER: %s", str(run_number))
    if run_number > 10:
        return 0

    command = ' '.join(['download_ASF_serial.py', '-username', password.asfuser, '-password', 
                                              password.asfpass, slc_dir + '/new_files.csv'])

    message_rsmas.log(os.getcwd(), command)
    completion_status = subprocess.Popen(' '.join(['download_ASF_serial.py', '-username', password.asfuser, '-password',
                                                   password.asfpass, slc_dir + '/new_files.csv']), shell=True).wait()

    hang_status = False  # whether or not the download has hung
    wait_time = 6  # wait time in 'minutes' to determine hang status
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
            asfserial_process.terminate()  # teminate the process beacause download hung
            break  # break the completion loop

        time.sleep(60 * wait_time)  # wait 'wait_time' minutes before continuing
        prev_size = curr_size
        completion_status = asfserial_process.poll()
        logger.log(loglevel.INFO,
                   "{} minutes: {:.1f}GB, completion_status {}".format(i * wait_time, curr_size / 1024 / 1024,
                                                                       completion_status))

    exit_code = completion_status  # get the exit code of the command
    logger.log(loglevel.INFO, "EXIT CODE: %s", str(exit_code))

    bad_codes = [137, -9]

    # If the exit code is one that signifies an error, rerun the entire command
    if exit_code in bad_codes or hang_status:
        logger.log(loglevel.WARNING, "Something went wrong, running again")
        run_download_asf_serial(slc_dir, logger, run_number=run_number + 1)

    return exit_code


def change_file_permissions():
    """ changes the permissions of downloaded files to 755 """

    os.system('chmod g+rw *')
    os.system('chmod o+r *')

    #zip_files = glob.glob('S1*.zip')
    #for file in zip_files:
    #    os.chmod(file, 0o666)  ---> does not work


if __name__ == "__main__":
    main()
