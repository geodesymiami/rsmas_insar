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
from multiprocessing.dummy import Pool as ThreadPool

def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    logfile_name = inps.work_dir + '/asfserial_rsmas.log'
    global logger
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

    global project_slc_dir
    project_slc_dir = os.path.join(inps.work_dir, 'SLC')

    os.chdir(inps.slc_dir)

    try:
        os.remove(os.path.expanduser('~') + '/.bulk_download_cookiejar.txt')
    except OSError:
        pass
    
    dataset_template = Template(inps.custom_template_file)
    dataset_template.options.update(PathFind.correct_for_ssara_date_format(dataset_template.options))
    subprocess.Popen("rm " + project_slc_dir + "/new_files*.csv", shell=True).wait()
    seasonal_start_date = None
    seasonal_end_date = None

    try:
        if dataset_template.options['seasonalStartDate'] is not None and dataset_template.options['seasonalEndDate'] is not None:
            seasonal_start_date = dataset_template.options['seasonalStartDate']
            seasonal_end_date = dataset_template.options['seasonalEndDate']
    except:
        pass

    if inps.seasonalStartDate is not None and inps.seasonalEndDate is not None:
        seasonal_start_date = inps.seasonalStartDate
        seasonal_end_date = inps.seasonalEndDate

    if seasonal_start_date is not None and seasonal_end_date is not None:
        generate_seasonal_files_csv(dataset_template, seasonal_start_date, seasonal_end_date)
    else:
        generate_files_csv(project_slc_dir, dataset_template)

    parallel = False

    try:
        if dataset_template.options['parallel'] == 'yes':
            parallel = True
    except:
        pass

    """if inps.parallel == 'yes':
        parallel = True"""

    threads = os.cpu_count()

    try:
        if dataset_template.options['threads'] is not None:
            threads = int(dataset_template.options['threads'])
    except:
        pass

    """if inps.processes is not None:
        processes = inps.processes"""

    if parallel:
        run_parallel_download_asf_serial(project_slc_dir, threads)
    else:
        succesful = run_download_asf_serial(project_slc_dir, logger)
        logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))

    change_file_permissions()
    logger.log(loglevel.INFO, "------------------------------------")
    subprocess.Popen("rm " + project_slc_dir + "/new_files*.csv", shell=True).wait()

    return None


def generate_seasonal_files_csv(dataset_template, seasonal_start_date, seasonal_end_date):
    """ Helps generate only the required seasonal ssaraopt dates to avoid unnecessary information
    """

    original_start_year = int(dataset_template.options['ssaraopt.startDate'][:4])
    if int(seasonal_start_date) > int(seasonal_end_date):
        offset = 1
    else:
        offset = 0
    year_range = int(dataset_template.options['ssaraopt.endDate'][:4]) - original_start_year + 1
    if year_range > 1 and offset == 1:
        year_range = year_range - 1
    ssaraopt_seasonal_start_date = '-' + seasonal_start_date[:2] + '-' + seasonal_start_date[2:]
    ssaraopt_seasonal_end_date = '-' + seasonal_end_date[:2] + '-' + seasonal_end_date[2:]
    original_end_date = dataset_template.options['ssaraopt.endDate']
    for counter in range(year_range):
        seasonal_tuple = (counter, original_start_year, offset, year_range, ssaraopt_seasonal_start_date, ssaraopt_seasonal_end_date, original_end_date)
        dates = generate_seasonal_ssaraopt_dates(dataset_template, seasonal_start_date, seasonal_end_date, seasonal_tuple)
        if dates is not None:
            generate_files_csv(project_slc_dir, dataset_template, dates[0], dates[1])
        counter += 1


def generate_seasonal_ssaraopt_dates(dataset_template, seasonal_start_date, seasonal_end_date, tuple_param):
    """ Generates appropriate seasonal ssaraopt dates for the download process
    Parameters include tuple_param which contains information required for successfully setting the dates
    """

    counter = tuple_param[0]
    original_start_year = tuple_param[1]
    offset = tuple_param[2]
    year_range = tuple_param[3]
    ssaraopt_seasonal_start_date = tuple_param[4]
    ssaraopt_seasonal_end_date = tuple_param[5]
    original_end_date = tuple_param[6]

    start_date = dataset_template.options['ssaraopt.startDate']
    end_date = dataset_template.options['ssaraopt.endDate']

    if counter == 0:
        if year_range == 1:
            if offset == 0:
                if int(seasonal_end_date) < int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')) or int(seasonal_start_date) > int(original_end_date[4:].replace('-', '')):
                    return None
                if int(seasonal_start_date) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    start_date = str(original_start_year) + ssaraopt_seasonal_start_date
                if int(seasonal_end_date) < int(original_end_date[4:].replace('-', '')):
                    end_date = str(original_start_year) + ssaraopt_seasonal_end_date
            elif int(dataset_template.options['ssaraopt.endDate'][:4]) - original_start_year + 1 == 1:
                if int(seasonal_start_date) > int(original_end_date[4:].replace('-', '')):
                    return None
                if int(seasonal_start_date) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    start_date = str(original_start_year) + ssaraopt_seasonal_start_date
            else:
                if int(seasonal_start_date) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    start_date = str(original_start_year) + ssaraopt_seasonal_start_date
                if int(seasonal_end_date) < int(original_end_date[4:].replace('-', '')):
                    end_date = str(original_start_year + offset) + ssaraopt_seasonal_end_date
        else:
            if offset == 0:
                if int(seasonal_end_date) < int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    return None
                if int(seasonal_start_date) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    start_date = str(original_start_year) + ssaraopt_seasonal_start_date
                end_date = str(original_start_year) + ssaraopt_seasonal_end_date
            else:
                if int(seasonal_start_date) >  int(dataset_template.options['ssaraopt.startDate'][4:].replace('-', '')):
                    start_date = str(original_start_year) + ssaraopt_seasonal_start_date
                end_date = str(original_start_year + offset) + ssaraopt_seasonal_end_date
    elif counter < year_range - 1:
        start_date = str(original_start_year + counter) + ssaraopt_seasonal_start_date
        end_date = str(original_start_year + offset) + ssaraopt_seasonal_end_date
    elif counter == year_range - 1:
        if int(seasonal_end_date) < int(original_end_date[4:].replace('-', '')):
            end_date = str(original_start_year + offset) + ssaraopt_seasonal_end_date
        else:
            end_date = original_end_date
        start_date = str(original_start_year + counter) + ssaraopt_seasonal_start_date

    return (start_date, end_date)


def generate_files_csv(slc_dir, custom_template_file, start_date=None, end_date=None):
    """ Generates a csv file of the files to download serially.
    Uses the `awk` command to generate a csv file containing the data files to be download
    serially. The output csv file is then sent through the `sed` command to remove the first five
    empty values to eliminate errors in download_ASF_serial.py.
    """

    dataset_template = custom_template_file

    if start_date is not None and end_date is not None:
        dataset_template.options['ssaraopt.startDate'] = start_date
        dataset_template.options['ssaraopt.endDate'] = end_date

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


def run_parallel_download_asf_serial(project_slc_dir, threads):
    """ Creates the chunk files necessary for Pool and runs it for the parallel download process
    The parameter processes is the desired number of processes to run. If no input is provided the default os.cpu_count() is used which is the number of processors
    """

    comma = '^[^,]+,?'
    file_num = 1
    total_num = 0
    csv_chunk_files = []

    while os.stat(project_slc_dir + '/new_files.csv').st_size != 0:
        subprocess.Popen("grep -E -o '" + comma + "' " + project_slc_dir + "/new_files.csv | tr -d '\n' >> " + project_slc_dir + "/new_files" + str(file_num) + ".csv", shell=True).wait()
        subprocess.Popen("sed -r -i 's/" + comma + "//' " + project_slc_dir + "/new_files.csv", shell=True).wait()
        file_num += 1
        total_num += 1
        if file_num > threads:
            file_num = 1
    if total_num < threads:
        processes = total_num
    for file_num in range(1, threads + 1):
        subprocess.Popen("sed -r -i 's/,$//' " + project_slc_dir + "/new_files" + str(file_num) + ".csv", shell=True).wait()
        csv_chunk_files.append('new_files' + str(file_num) + '.csv')

    ThreadPool(threads).map(run_parallel_download_asf_serial_helper, csv_chunk_files)


def run_parallel_download_asf_serial_helper(csv_chunk_file):
    """ Helper function necessary to run Pool since it requires only one parameter
    """

    exit_code = run_download_asf_serial(project_slc_dir, logger, csv_file=csv_chunk_file)
    logger.log(loglevel.INFO, "SUCCESS: %s", exit_code)


def run_download_asf_serial(slc_dir, logger, run_number=1, csv_file='new_files.csv'):
    """ Runs download_ASF_serial.py with proper files.
    Runs adapted download_ASF_serial.py with a CLI username and password and a csv file containing
    the the files needed to be downloaded (provided by ssara_federated_query.py --print)
    """

    logger.log(loglevel.INFO, "RUN NUMBER: %s", str(run_number))
    if run_number > 10:
        return 0

    command = ' '.join(['download_ASF_serial.py', '-username', password.asfuser, '-password', 
                                              password.asfpass, slc_dir + '/' + csv_file])

    message_rsmas.log(os.getcwd(), command)
    completion_status = subprocess.Popen(' '.join(['download_ASF_serial.py', '-username', password.asfuser, '-password',
                                                   password.asfpass, slc_dir + '/' + csv_file]), shell=True).wait()

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
        run_download_asf_serial(slc_dir, logger, run_number=run_number + 1, csv_file=csv_file)

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
