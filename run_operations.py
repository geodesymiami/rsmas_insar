#!/usr/bin/env python3 
import os
import sys
import subprocess
import argparse
from datetime import date, datetime
import shutil
import time
import glob

import generate_template_files as gt
from rsmas_logging import RsmasLogger, loglevel
from dataset_template import Template
import _process_utilities as putils

OPERATIONS_DIRECTORY = os.getenv('OPERATIONS')
STORED_DATE_FILE = OPERATIONS_DIRECTORY + "/stored_date.date"
TEMPLATE_DIRECTORY = OPERATIONS_DIRECTORY + "/TEMPLATES"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

logger_file = "run_operations.log"
logger_run_operations = RsmasLogger(logger_file)

def create_process_rsmas_parser():
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
    data_args.add_argument('--sheet_id', dest="sheet_id", metavar='SHEET ID', action='append', nargs=1, help='sheet id to use')
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

    parser = create_process_rsmas_parser()
    inps = parser.parse_args(args)

    return inps


def initiate_operations():

    operations_directory = os.getenv('OPERATIONS')
    templates_directory = operations_directory + "/TEMPLATES/"
    logs_directory = operations_directory + "/LOGS/"
    errors_directory = operations_directory + "/ERRORS/"

    if not os.path.isdir(operations_directory):
        os.mkdir(operations_directory)
    if not os.path.isdir(templates_directory):
        os.mkdir(templates_directory)
    if not os.path.isdir(logs_directory):
        os.mkdir(logs_directory)
        open(logs_directory + '/generate_templates.log', 'a').close()  # create empty file
    if not os.path.isdir(errors_directory):
        os.mkdir(errors_directory)
    if not os.path.exists(os.getenv('OPERATIONS') + '/stored_date.date'):
        open(os.getenv('OPERATIONS') + '/stored_date.date', 'a').close()  # create empty file

def generate_templates_with_options(csv, dataset, sheet):

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

    template_files = gt.main(template_options)

    return template_files

def get_datasets_to_process(dataset=None):

    # Obtains list of datasets to run processSentinel on
    if dataset:
        datasets = [dataset]
    else:
        template_files = glob.glob("{}/*.template".format(TEMPLATE_DIRECTORY))
        datasets = [putils.get_project_name(template) for template in template_files]

    return datasets

def get_newest_data_date(template_file):

    dset_template = Template(template_file)
    ssaraopt_string = dset_template.generate_ssaraopt_string()

    ssaraopt_cmd = 'ssara_federated_query.py {} --print'.format(ssaraopt_string)

    ssara_output = subprocess.check_output(ssaraopt_cmd, shell=True)

    newest_data = ssara_output.decode('utf-8').split("\n")[-2]
    date = datetime.strptime(newest_data.split(",")[3], DATE_FORMAT)

    return date

def get_last_downloaded_date(dset):

    dataset_line = None
    with open(STORED_DATE_FILE) as date_file:
        for line in date_file.readlines():
            if dset in line:
                dataset_line = line
                break

    if dataset_line is not None:
        last_date = dataset_line.split(": ")[1]
    else:
        last_date = datetime.strftime(datetime(1970, 1, 1, 0, 0, 0), DATE_FORMAT)

    return datetime.strptime(last_date, DATE_FORMAT)

def run_process_rsmas(inps, template_file, dataset):

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

    process_rsmas = subprocess.check_output(process_rsmas_cmd, shell=True)

    job_number = process_rsmas.split('\n')[0].split("<")[1].split('>')[0]

    stdout_file = "{}/{}/z_processRsmas_{}.o".format(os.getenv('SCRATHDIR'), dataset, job_number)
    stderr_file = "{}/{}/z_processRsmas_{}.e".format(os.getenv('SCRATHDIR'), dataset, job_number)

    logger_run_operations.log(loglevel.INFO, "Job Number: {}".format(job_number))

    return [stdout_file, stderr_file], job_number

def copy_output_file(output_file, job_to_dset):

    job = os.path.splitext(output_file.split("z_processRsmas_")[1])[0]
    dataset = job_to_dset[job]

    if os.path.exists(output_file) and os.path.isfile(output_file):

        base = "{}/{}/{}/".format(os.getenv('OPERATIONS'), 'ERRORS', dataset)

        if not os.path.exists(base):
            os.makedirs(base)

        destination = base + str(datetime.now().strftime("%m-%d-%Y")) + os.path.splitext(f)[1]
        shutil.copy(output_file, destination)

def overwrite_stored_date(dset, newest_date):

    new_line = "{}: {}\n".format(dset, newest_date.strftime(DATE_FORMAT))

    date_file = open(STORED_DATE_FILE, 'r')

    lines = date_file.readlines()

    for i, line in enumerate(lines):
        if dset in line:
            lines[i] = new_line
            logger_run_operations.log()
            date_file.close()
            return

    date_file.close()

    date_file = open(STORED_DATE_FILE, 'a')
    date_file.writelines([new_line])

    date_file.close()





def run_operations(args):

    inps = command_line_parse(args)

    # Remove and reinitiate $OPERATIONS directory
    if inps.restart:
        shutil.rmtree(os.getenv('OPERATIONS'))
        initiate_operations()

    template_files = []
    # inps.sheet_id is an array of sheets.
    # Each use of the --sheet_id command line parameter adds another array to the inps.sheet_id variable.
    for sheet in inps.sheet_id:
        template_files += generate_templates_with_options(inps.template_csv, inps.dataset, sheet[0])

    if inps.dataset:
        datasets = [inps.dataset]
    else:
        datasets = [putils.get_project_name(template) for template in template_files]

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

    total_output_files = len(output_files)
    mins = 0

    logger_run_operations.log(loglevel.INFO, "{} total output files".format(total_output_files))

    # Wait for all of the *.o/*.e files to be generated and copy them to the $OPERATIONS/ERRORS directory
    while len(output_files) != 0:
        logger_run_operations.log(loglevel.INFO, "{}/{} output files remaining after {} minutes".format(len(output_files), total_output_files, mins))
        for i, output_file in enumerate(output_files):
            if os.path.exists(output_file) and os.path.isfile(output_file):
                # Remove the output and error files (should appear next to each other in the list) and add them
                # to the list of files to be copied to to the OPERATIONS directory
                copy_output_file(output_files.pop(i), job_to_dset)

        time.sleep(60)

        mins += 1

    logger_run_operations.log(loglevel.INFO, "run_operations.py completed.")
    logger_run_operations.log(loglevel.INFO, "------------------------------")




if __name__ == "__main__":

    run_operations(sys.argv[1:])
