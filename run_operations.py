#!/usr/bin/env python3 
import os
import sys
import subprocess
import argparse
from datetime import datetime
import shutil
import time

import generate_template_files
from rsmas_logging import RsmasLogger, loglevel
import dataset_template
import _process_utilities as putils


############## DIRECTORY AND FILE CONSTANTS ##############
OPERATIONS_DIRECTORY = os.getenv('OPERATIONS')
SCRATCH_DIRECTORY = os.getenv('SCRATCHDIR')
TEMPLATE_DIRECTORY = OPERATIONS_DIRECTORY + "/TEMPLATES"
LOGS_DIRECTORY = OPERATIONS_DIRECTORY + "/LOGS"
ERRORS_DIRECTORY = OPERATIONS_DIRECTORY + "/ERRORS"
STORED_DATE_FILE = OPERATIONS_DIRECTORY + "/stored_date.date"

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

logger_file = "{}/{}/run_operations.log".format(OPERATIONS_DIRECTORY, "LOGS")
logger_run_operations = RsmasLogger(logger_file)

def create_run_operations_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description="""Submits processing jobs for each datasest template present in the 
                                     $OPERATIONS/TEMPLATES/ directory.  \nPlace run_operations_LSF.job file into 
                                     $OPERATIONS directory and submit with bsub < run_operations_LSF.job. \nIt runs 
                                     run_operations.py once daily at 12:00 PM.""")

    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')

    data_args = parser.add_argument_group("Dataset and Template Files", "Dataset and Template Files")
    data_args.add_argument('-dataset', dest='dataset', metavar="DATASET", help='Particular dataset to run')
    data_args.add_argument('-templatecsv', dest='template_csv', metavar='FILE', help='local csv file containing template info.')
    data_args.add_argument('-singletemplate', dest='single_template', metavar='FILE', help='singular template file to run on')
    data_args.add_argument('--sheet_ids', dest="sheet_id", metavar='SHEET ID', action='append', nargs=1, help='sheet id to use')
    data_args.add_argument('--restart', dest='restart', action='store_true', help='remove $OPERATIONS directory before starting')

    process_args = parser.add_argument_group("Processing steps", "processing Steps")
    process_args.add_argument('--startssara', dest='startssara', action='store_true', help='process_rsmas.py --startssara')
    process_args.add_argument('--stopssara', dest='stopssara', action='store_true', help='stop after downloading')
    process_args.add_argument('--startprocess', dest='startprocess', action='store_true', help='process using sentinelstack package')
    process_args.add_argument('--stopprocess', dest='stopprocess', action='store_true', help='stop after processing')
    process_args.add_argument('--startpysar', dest='startpysar', action='store_true', help='run pysar')
    process_args.add_argument('--stoppysarload', dest='stoppysarload', action='store_true', help='stop after loading into pysar')
    process_args.add_argument('--stoppysar', dest='stoppysar', action='store_true', help='stop after pysar processing')
    process_args.add_argument('--startinsarmaps', dest='startinsarmaps', action='store_true', help='ingest into insarmaps')

    return parser

def command_line_parse(args):

    parser = create_run_operations_parser()
    inps = parser.parse_args(args)

    return inps


def initiate_operations():
    """
        Creates necessary directories if they do not already exist on the file system.
        Files and directories created:
            OPERATIONS/
                TEMPLATES/
                LOGS/
                ERRORS/
                stored_date.date
    """
    if not os.path.isdir(OPERATIONS_DIRECTORY):
        os.mkdir(OPERATIONS_DIRECTORY)

    if not os.path.isdir(TEMPLATE_DIRECTORY):
        os.mkdir(TEMPLATE_DIRECTORY)

    if not os.path.isdir(LOGS_DIRECTORY):
        os.mkdir(LOGS_DIRECTORY)

    if not os.path.isdir(ERRORS_DIRECTORY):
        os.mkdir(ERRORS_DIRECTORY)

    if not os.path.exists(STORED_DATE_FILE):
        open(STORED_DATE_FILE, 'a').close()  # create empty file

def generate_templates_with_options(csv, dataset, sheet):
    """
    Generates all active template files based on the provided Google Sheet
    :param csv: a local CSV file that can be used in lieu of a Google Sheet
    :param dataset: an individual dataset to generate a template file for
    :param sheet: the URL id of the Google Sheet containing template info
    :return: a list of template files generated
    """
    template_options = []
    if csv:
        template_options.append('--csv')
        template_options.append(csv)
    if dataset:
        template_options.append('--dataset')
        template_options.append(dataset)
    if sheet:
        template_options.append('--sheet_id')
        template_options.append(sheet)

    template_files = generate_template_files.main(template_options)

    return template_files

def get_datasets_to_process(template_files, dataset=None):
    """
    Converts the template files being used in dataset/project names
    :param template_files: the list of template files to parse the dataset name from
    :param dataset: a single dataset to return
    :return: a list of dataset names
    """
    # Obtains list of datasets to run processSentinel on
    if dataset:
        datasets = [dataset]
    else:
        datasets = [putils.get_project_name(template) for template in template_files]

    return datasets

def get_newest_data_date(template_file):
    """
    Obtains the most recent image date for a dataset
    :param template_file: the template file corresponding to the dataset being obtained
    :return: the newest image date in "YYYY-MM-DD T H:M:S.00000" format
    """
    dset_template = dataset_template.Template(template_file)
    ssaraopt_string = dset_template.generate_ssaraopt_string()

    ssaraopt_cmd = 'ssara_federated_query.py {} --print'.format(ssaraopt_string)

    ssara_output = subprocess.check_output(ssaraopt_cmd, shell=True)

    newest_data = ssara_output.decode('utf-8').split("\n")[-2]

    return datetime.strptime(newest_data.split(",")[3], DATE_FORMAT)

def get_last_downloaded_date(dset):
    """
    Obtains the most recent date an image was downloaded for a given dataset by reading the stored_date.date file.
    If this is the first time images were downloaded for a given dataset, the date 01-01-1970 is used.
    :param dset: the dataset to get the most recent download date from
    :return: the most recent download date in "YYYY-MM-DD T H:M:S.00000" format
    """
    dataset_line = None
    with open(STORED_DATE_FILE, 'r') as date_file:
        for line in date_file.readlines():
            if dset in line:
                dataset_line = line
                break

    if dataset_line is not None:
        last_date = dataset_line.split(": ")[1].strip("\n")
    else:
        last_date = datetime.strftime(datetime(1970, 1, 1, 0, 0, 0), DATE_FORMAT)
    
    return datetime.strptime(last_date, DATE_FORMAT)

def run_process_rsmas(inps, template_file, dataset):
    """
    Submits `process_rsmas.py` as a job for the given dataset/template_file
    :param inps: the command line variable namespace (is modified in place)
    :param template_file: the template file associated with the dataset being processed
    :param dataset: the dataset being processed
    :return: a list of the two output files to be generated by the `process_rsmas` call, and the job number of
             the `process_rsmas` job submission.
    """
    process_rsmas_options = []

    if inps.startssara:
        process_rsmas_options.append('--startssara')
    if inps.stopssara:
        process_rsmas_options.append('--stopssara')
    if inps.startprocess:
        process_rsmas_options.append('--startprocess')
    if inps.stopprocess:
        process_rsmas_options.append('--stopprocess')
    if inps.startpysar:
        process_rsmas_options.append('--startpysar')
    if inps.stoppysarload:
        process_rsmas_options.append('--stoppysarload')
    if inps.stoppysar:
        process_rsmas_options.append('--stoppysar')
    if inps.startinsarmaps:
        process_rsmas_options.append('--startinsarmaps')

    if len(process_rsmas_options) == 0:
        process_rsmas_options.append('--insarmaps')

    process_rsmas_options = ' '.join(process_rsmas_options)

    process_rsmas_cmd = "process_rsmas.py {} {} --submit".format(template_file, process_rsmas_options)

    process_rsmas = subprocess.check_output(process_rsmas_cmd, shell=True).decode('utf-8')
    
    job_number = process_rsmas.split('\n')[0]

    file_base = os.path.join(SCRATCH_DIRECTORY, dataset)

    stdout_file = os.path.join(file_base, "/process_rsmas_{}.o".format(job_number))
    stderr_file = os.path.join(file_base, "/process_rsmas_{}.e".format(job_number))

    logger_run_operations.log(loglevel.INFO, "Job Number: {}".format(job_number))
    logger_run_operations.log(loglevel.INFO, "Output Files: {}, {}".format(stdout_file, stderr_file))

    return [stdout_file, stderr_file], job_number

def copy_output_file(output_file, dataset):
    """
    Copies the provided output_file to the $OPERATIONS/ERRORS directory for easy access
    :param output_file: the output file to be copied (EXAMPLE: process_rsmas_00000001.o)
    :param dataset: the dataset this file is associated with
    """
    if os.path.exists(output_file) and os.path.isfile(output_file):

        base = os.path.join(OPERATIONS_DIRECTORY, 'ERRORS', dataset, '')

        if not os.path.exists(base):
            os.makedirs(base)

        output_file_name = str(datetime.now().strftime("%m-%d-%Y")) + os.path.splitext(output_file)[1]

        destination = os.path.join(base, output_file_name)

        shutil.copy(output_file, destination)

def overwrite_stored_date(dset, newest_date):
    """
    Overwrites the stored_date.date file entry for the provided dataset with the provided date
    :param dset: the dataset to be overriden
    :param newest_date: the new date to override with
    """
    new_line = "{}: {}\n".format(dset, newest_date.strftime(DATE_FORMAT))

    lines = open(STORED_DATE_FILE, 'r').readlines()
    
    for i, line in enumerate(lines):
        if dset in line:
            lines[i] = new_line
            date_file = open(STORED_DATE_FILE, 'w')
            date_file.writelines(lines)
            break
    else:
        date_file = open(STORED_DATE_FILE, 'a')
        date_file.write(new_line)
    
    date_file.close()


def run_operations(args):
    """
    Runs the entire data processing routing from start to finish. Steps as follows:
        1. Generates the template files for all of the datasets in the provivded CSV or Google Sheet file
        2. Gets the dataset names for each template files
        for each dataset:
            3. Gets the newest available image date from `ssara_federated_query.py`
            4. Gets the last image date downloaded from the `stored_date.date` file
            5. Runs `process_rsmas.py` if their is new data available
        6. Waits for all of the output files from submitted `process_rsmas` calls to exist
    :param args: command line arguments to use
    """
    inps = command_line_parse(args)

    # Remove and reinitiate $OPERATIONS directory
    if inps.restart:
        shutil.rmtree(OPERATIONS_DIRECTORY)
    
    initiate_operations()

    template_files = []

    # inps.sheet_ids is an array of sheets.
    # Each use of the --sheet_id command line parameter adds another array to the inps.sheet_id variable.
    for sheet in inps.sheet_ids:
        template_files += generate_templates_with_options(inps.template_csv, inps.dataset, sheet[0])

    datasets = get_datasets_to_process(template_files, inps.dataset)

    logger_run_operations.log(loglevel.INFO, "Datasets to Process: {}".format(datasets))

    output_files = []
    job_to_dset = {}

    for dset in datasets:

        template_file = "{}/{}.template".format(TEMPLATE_DIRECTORY, dset)

        logger_run_operations.log(loglevel.INFO, "{}: {}".format(dset, template_file))

        newest_date = get_newest_data_date(template_file)
        last_date = get_last_downloaded_date(dset)

        logger_run_operations.log(loglevel.INFO, "Newest Date: {}".format(newest_date))
        logger_run_operations.log(loglevel.INFO, "Last Date: {}".format(last_date))

        if newest_date > last_date:

            logger_run_operations.log(loglevel.INFO, "Starting process_rsmas for {}".format(dset))

            #  Exit and don't overwrite date file if process_rsmas.py throws and error
            try:
                # Submit processing job and running processing routine vis process_rsmas.py
                outputs, job = run_process_rsmas(inps, template_file, dset)

                # Overwrite the most recent date of data download in the date file
                overwrite_stored_date(dset, newest_date)

                job_to_dset[job] = dset
                output_files += outputs

            except Exception as e:
                logger_run_operations.log(loglevel.ERROR, "process_rsmas threw an error ({}) and exited.".format(e))

        logger_run_operations.log(loglevel.INFO, "{} process_rsmas calls completed.".format(dset))

    logger_run_operations.log(loglevel.INFO, "All process_rsmas calls complete. Waiting for output files to appear")

    logger_run_operations.log(loglevel.INFO, "{} total output files".format(len(output_files)))

    # check if output files exist
    i = 0
    wait_time_sec = 60
    total_wait_time_min = 0
    while i < len(output_files):
        if os.path.isfile(output_files[i]):
            logger_run_operations.log(loglevel.INFO, "Job #{} of {} complete (output file {})".format(i + 1, len(output_files), output_files[i]))

            # Parses the job number from the file name ('process_rsmas_jobnumber.o')
            # Looks up dataset associated with that job number in the dictionary
            # Copies outputs file to appropriate location in $OPERATIONS
            job_number = output_files[i].split("process_rsmas_")[1].split(".")[0]
            dset = job_to_dset[job_number]
            copy_output_file(output_file=output_files[i], dataset=dset)

            i += 1
        else:
            logger_run_operations.log(loglevel.INFO, "Waiting for job #{} of {} (output file {}) after {} minutes".format(i + 1, len(output_files),
                                                                                       output_files[i],
                                                                                       total_wait_time_min))
            total_wait_time_min += wait_time_sec / 60
            time.sleep(wait_time_sec)

    logger_run_operations.log(loglevel.INFO, "run_operations.py completed.")
    logger_run_operations.log(loglevel.INFO, "------------------------------")



if __name__ == "__main__":

    run_operations(sys.argv[1:])
