#!/usr/bin/env python3 
import os
import glob
import sys
import subprocess
import argparse
from datetime import datetime
import shutil
import time

from minsar.utils import generate_template_files
from minsar.objects.rsmas_logging import RsmasLogger, loglevel
from minsar.objects import dataset_template
from minsar.objects.dataset_template import Template
import minsar.utils.process_utilities as putils
from minsar.objects.auto_defaults import PathFind
from minsar.utils.download_ssara import add_polygon_to_ssaraopt

pathObj = PathFind()

############## DIRECTORY AND FILE CONSTANTS ##############
OPERATIONS_DIRECTORY = os.getenv('OPERATIONS')
SCRATCH_DIRECTORY = os.getenv('SCRATCHDIR')
TEMPLATE_DIRECTORY = os.path.join(OPERATIONS_DIRECTORY, "TEMPLATES")
LOGS_DIRECTORY = os.path.join(OPERATIONS_DIRECTORY, "LOGS")
ERRORS_DIRECTORY = os.path.join(OPERATIONS_DIRECTORY, "ERRORS")
STORED_DATE_FILE = os.path.join(OPERATIONS_DIRECTORY, "stored_date.date")

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"

logger_file = os.path.join(LOGS_DIRECTORY, "run_operations.log")
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
    data_args.add_argument('--sheet_id', dest="sheet_ids", metavar='SHEET ID', action='append', nargs=1, help='sheet id to use')
    data_args.add_argument('--restart', dest='restart', action='store_true', help='remove $OPERATIONS directory before starting')

    # FA 8/2019: need to use --start, --end and --step as does process_rsmas.py
    process_args = parser.add_argument_group("Processing steps", "processing Steps")
    process_args.add_argument('--startssara', dest='startssara', action='store_true', help='process_rsmas.py --startssara')
    process_args.add_argument('--stopssara', dest='stopssara', action='store_true', help='stop after downloading')
    process_args.add_argument('--startifgrams', dest='startifgrams', action='store_true', help='run ifgrams')
    process_args.add_argument('--startmintpy', dest='startmintpy', action='store_true', help='run mintpy')
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
    Extracts project names from the list of tenplate files
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

    delta_lat = 0.0   # 8/2019: this should use the same default as download_ssara_rsmas.py which I believe is set in
                      # utils/process_utilities.py:    flag_parser.add_argument('--delta_lat', dest='delta_lat', default='0.0', type=float,

    dataset_template = Template(template_file)
    dataset_template.options.update(pathObj.correct_for_ssara_date_format(dataset_template.options))

    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')

    # add intersectWith to ssaraopt string
    ssaraopt = add_polygon_to_ssaraopt(dataset_template.get_options(), ssaraopt.copy(), delta_lat)

    ssaraopt_cmd = ['ssara_federated_query.py'] + ssaraopt + ['--print']
    ssaraopt_cmd = ' '.join(ssaraopt_cmd[:])

    print(ssaraopt_cmd)
    # Yield list of images in following format:
    # ASF,Sentinel-1A,15775,2017-03-20T11:49:56.000000,2017-03-20T11:50:25.000000,128,3592,3592,IW,NA,DESCENDING,R,VV+VH,https://datapool.asf.alaska.edu/SLC/SA/S1A_IW_SLC__1SDV_20170320T114956_20170320T115025_015775_019FA4_097A.zip
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
    # dataset_line = None
    # with open(STORED_DATE_FILE, 'r') as date_file:
    #     for line in date_file.readlines():
    #         if dset in line:
    #             dataset_line = line
    #             break

    # if dataset_line is not None:
    #     last_date = dataset_line.split(": ")[1].strip("\n")
    # else:
    #     last_date = datetime.strftime(datetime(1970, 1, 1, 0, 0, 0), DATE_FORMAT)

    MINSAR_LOG_DIR = "~/minsar_log"

    logfiles = glob.glob("{}/*{}*.o".format(os.path.expanduser(MINSAR_LOG_DIR), dset))
    logfiles.sort(key=os.path.getctime)

    print(logfiles)

    l = None
    if len(logfiles) > 0:
        f = logfiles[-1]

        with open(f) as logfile:
            for line in logfile.readlines():
                if 'Last processed image date:' in line:
                    l = line
                    break

    if l:                
        last_date = l.split(": ")[-1]
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
    print("RUNNING process_rsmas.py: " + template_file)

    if inps.startssara:
        process_rsmas_options.append('--start download')
    if inps.startifgrams:
        process_rsmas_options.append('--start ifgrams')
    if inps.startinsarmaps:
        process_rsmas_options.append('--start insarmaps')
    ''' FA 5/2019: here we used to have the same options as process_rsmas.py
        need to revisit whetehr any options are useful with the run_files'''

    process_rsmas_options = ' '.join(process_rsmas_options)

    process_rsmas_cmd = "process_rsmas.py {} {} --submit".format(template_file, process_rsmas_options)
    print (process_rsmas_cmd)

    process_rsmas = subprocess.check_output(process_rsmas_cmd, shell=True).decode('utf-8')
    
    job_number = process_rsmas.split('\n')[0]

    file_base = os.path.join(SCRATCH_DIRECTORY, dataset)

    stdout_file = os.path.join(file_base, "process_rsmas_{}.o".format(job_number))
    stderr_file = os.path.join(file_base, "process_rsmas_{}.e".format(job_number))

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

        print(newest_date)
        print(last_date)

        if newest_date > last_date:
            print("Submitting minsar_wrapper.bash for {}".format(putils.get_project_name(template_file)))
            subprocess.Popen(["minsar_wrapper.bash", template_file], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            print("SKIPPING")
    print("-------------- run_operations.py has completed. Exiting now. -------------- \n\n\n\n\n\n\n")

    sys.exit(0)
    return



if __name__ == "__main__":

    run_operations(sys.argv[1:])
