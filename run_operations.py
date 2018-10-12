#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from datetime import datetime
import shutil
import time
import glob

import generate_templates as gt

import logging

#################### LOGGERS AND LOGGING SETUP ####################

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

std_formatter = logging.Formatter("%(message)s")

logfilename = os.getenv('OPERATIONS') + '/LOGS/run_operations.log'
os.makedirs(os.path.dirname(logfilename), exist_ok=True)
general = logging.FileHandler(logfilename, 'a+', encoding=None)
general.setLevel(logging.INFO)
general.setFormatter(std_formatter)
logger.addHandler(general)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(std_formatter)
logger.addHandler(console)

info_handler = None
error_handler = None

#################### GLOBAL VARIABLES ####################

dataset = 'GalapagosSenDT128VV'  # Single Dataset for Testing

user = subprocess.check_output(['whoami']).decode('utf-8').strip("\n")  # Currently logged in user

stored_date = None  # previously stored date
most_recent = None  # date parsed from SSARA
inps = None;  # command line arguments

job_to_dset = {}  # dictionary of jobs to datasets

date_format = "%Y-%m-%dT%H:%M:%S.%f"  # date format for reading and writing dates


def setup_logging_handlers(dset, mode):
	""" Initializes logging handlers for INFO level and ERROR level file logging.
		Needed so as to be able to continue logging data to the appropiate dataset log after processSentinel completes.

		Parameters: dset: str, the dataset to write log output for
					mode: str, the logfile write mode (can be write or append)
		Returns:    none
	"""
	global info_handler, error_handler

	# create a file handler for INFO level logging
	info_log_file = os.getenv('OPERATIONS') + '/LOGS/' + dset + '_info.log'
	os.makedirs(os.path.dirname(info_log_file), exist_ok=True)
	info_handler = logging.FileHandler(info_log_file, mode, encoding=None)
	info_formatter = logging.Formatter("%(levelname)s - %(message)s")
	info_handler.setLevel(logging.INFO)
	info_handler.setFormatter(info_formatter)
	logger.addHandler(info_handler)

	# create a file handler for ERROR level logging
	error_log_file = os.getenv('OPERATIONS') + '/LOGS/' + dset + '_error.log'
	os.makedirs(os.path.dirname(error_log_file), exist_ok=True)
	error_handler = logging.FileHandler(error_log_file, mode, encoding=None)
	err_formatter = logging.Formatter("%(levelname)s - %(message)s")
	error_handler.setLevel(logging.ERROR)
	error_handler.setFormatter(err_formatter)
	logger.addHandler(error_handler)


###################### Command Line Argument Processing #################

def create_process_sentinel_parser():
	"""
		Defines commandline argument parser and command line arguments to accept

		Parameters: none
		Returns:    parser: argument parser object
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

	parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
	parser.add_argument("--dataset", dest='dataset', metavar="DATASET", help='Particular dataset to run')
	parser.add_argument('--templatecsv', dest='template_csv', metavar='FILE',
						help='local csv file containing template info.')
	parser.add_argument('--singletemplate', dest='single_template', metavar='FILE',
						help='singular template file to run on')
	parser.add_argument('--startssara', dest='startssara', action='store_true', help='process_sentinel.py --startssara')
	parser.add_argument('--startprocess', dest='startprocess', action='store_true',
						help='process using sentinelstack package')
	parser.add_argument('--startpysar', dest='startpysar', action='store_true', help='run pysar')
	parser.add_argument('--startinsarmaps', dest='startinsarmaps', action='store_true', help='ingest into insarmaps')
	parser.add_argument("--testsheet", dest="test_sheet", action='store_true',
						help='whether or not to use the test sheet')

	return parser


def command_line_parse(args):
	"""
		Parses command line arguments into inps object as object parameters

		Parameters: args: [str], array of command line arguments
		Returns:    none
	"""
	global inps;

	parser = create_process_sentinel_parser()
	inps = parser.parse_args(args)

	logger.info("\tCOMMAND LINE VARIABLES:")
	logger.info("\t\t--dataset     	    : %s\n", inps.dataset)
	logger.info("\t\t--templatecsv      : %s\n", inps.template_csv)
	logger.info("\t\t--singletemplate   : %s\n", inps.single_template)
	logger.info("\t\t--startssara       : %s\n", inps.startssara)
	logger.info("\t\t--startprocess     : %s\n", inps.startprocess)
	logger.info("\t\t--startpysar       : %s\n", inps.startpysar)
	logger.info("\t\t--startinsarmaps   : %s\n", inps.startinsarmaps)
	logger.info("\t\t--testsheet	    : %s\n", inps.test_sheet)


###################### Auxiliary Functions #####################

def create_ssara_options():
	""" Reads template file for the current dataset and parses out the 'ssaraopt' option before creating command options
		line options array for ssara_federated_query.py

		Parameters: none
		Returns:    ssara_options: [str], array of command line options to run ssara_federated_query with
	"""

	with open('/nethome/' + user + '/insarlab/OPERATIONS/TEMPLATES/' + dataset + '.template', 'r') as template_file:
		options = ''
		for line in template_file:
			if 'ssaraopt' in line:
				options = line.strip('\n').rstrip().split("= ")[1]
				break;

	# Compute SSARA options to use
	options = options.split(' ')

	ssara_options = ['ssara_federated_query.py'] + options + ['--print']

	return ssara_options


def set_dates(ssara_output):
	""" Reads the most recently stored date for the given dataset from the stored_date.date file, and parses the newest
		data date from ssara_federated_query.

		Parameters: ssara_output: str, string output from ssara_federated_query.py ... --print
		Returns:    none
	"""
	global stored_date, most_recent

	most_recent_data = ssara_output.split("\n")[-2]
	most_recent = datetime.strptime(most_recent_data.split(",")[3], date_format)

	# Checks if the stored_date.date file exists and created the file+directories if it doesn't
	filename = os.getenv('OPERATIONS') + '/stored_date.date'
	if not os.path.exists(filename):
		if not os.path.exists(os.path.dirname(filename)):
			os.makedirs(os.path.dirname(filename))
		subprocess.Popen("touch "+filename, shell=True).wait()

	# Write Most Recent Date to File
	with open(filename, 'rb') as stored_date_file:

		try:
			date_line = subprocess.check_output(
				['grep', dataset, os.getenv('OPERATIONS') + '/stored_date.date']).decode('utf-8')
			stored_date = datetime.strptime(date_line.split(": ")[1].strip('\n'), date_format)
		except subprocess.CalledProcessError as e:

			stored_date = datetime.strptime("1970-01-01T12:00:00.000000", date_format)

			with open(os.getenv('OPERATIONS') + '/stored_date.date', 'a+') as date_file:
				data = str(dataset + ": " + str(datetime.strftime(most_recent, date_format)) + "\n")
				date_file.write(data)


def compare_dates():
	""" Compares the most recent and stored dates

		Parameters: none
		Returns:    boolean, whether the most recent data is more recent than the stored date
	"""
	global stored_date, most_recent

	return most_recent > stored_date


def overwrite_stored_date():
	""" Overwrites the date stored in the stored_date.date file for the given dataset

		Parameters: none
		Returns:    none
	"""
	global user, most_recent

	data = []
	with open(os.getenv('OPERATIONS') + '/stored_date.date', 'r') as date_file:
		data = date_file.readlines();

	for i, line in enumerate(data):
		if dataset in line:
			data[i] = str(dataset + ": " + str(datetime.strftime(most_recent, date_format)) + "\n")

	with open(os.getenv('OPERATIONS') + '/stored_date.date', 'w') as date_file:
		date_file.writelines(data)


def run_process_sentinel():
	""" Submits a processSentinel.py job with the associated options as defined by the provided command line arguments

		Parameters: none
		Returns:    [files], [str] an array of file paths to the processSentinel output and error files
	"""
	global user, dataset

	psen_extra_options = []

	if inps.startssara:
		psen_extra_options.append('--startssara')
	if inps.startprocess:
		psen_extra_options.append('--startprocess')
	if inps.startpysar:
		psen_extra_options.append('--startpysar')
	if inps.startinsarmaps:
		psen_extra_options.append('--startinsarmaps')

	if len(psen_extra_options) == 0:
		psen_extra_options.append('--insarmaps')

	psen_options = ['process_sentinel.py',
					os.getenv('OPERATIONS') + '/TEMPLATES/' + dataset + '.template'] + psen_extra_options + ['--bsub']

	psen_output = subprocess.check_output(psen_options).decode('utf-8')

	job_number = psen_output.split('\n')[0].split("<")[1].split('>')[0]
	logger.info("JOB NUMBER: %s", job_number)

	job_to_dset[job_number] = dataset

	stdout_file_path = os.getenv('SCRATCHDIR') + '/' + dataset + '/z_processSentinel_' + job_number + '.o'
	stderr_file_path = os.getenv('SCRATCHDIR') + '/' + dataset + '/z_processSentinel_' + job_number + '.e'

	return [stdout_file_path, stderr_file_path]


def post_processing(files_to_move):
	""" Copies the output and error files from processSentinel to the $OPERATIONS/ERRORS directory

		Parameters: files_to_move: [str], arrays of files to move to the ERRORS directory
		Returns:    none
	"""
	global output_file, most_recent

	job = files_to_move[0].split('/z_processSentinel_')[1].strip(".o")

	setup_logging_handlers(job_to_dset[job], "a+")

	for filename in files_to_move:
		if os.path.exists(filename) and os.path.isfile(filename):

			base = os.getenv('OPERATIONS') + '/ERRORS/' + dataset + '/'

			if not os.path.exists(base):
				os.makedirs(base)

			dest = base + str(most_recent)[0:10]
			if filename[-1] is 'o':
				dest += '.o'
			elif filename[-1] is 'e':
				dest += '.e'

			shutil.copy(filename, dest)

		else:
			raise IOError

	logger.removeHandler(info_handler)
	logger.removeHandler(error_handler)


if __name__ == "__main__":

	from datetime import datetime

	logger.info("RUN_OPERATIONS for %s:\n", datetime.fromtimestamp(time.time()).strftime(date_format))

	# Parse command line arguments
	command_line_parse(sys.argv[1:])

	# Generate Template Files
	template_options = []
	if inps.template_csv:
		template_options.append('--csv')
		template_options.append(inps.template_csv)
	if inps.dataset:
		template_options.append('--dataset')
		template_options.append(inps.dataset)
	if inps.test_sheet:
		template_options.append('--testsheet')

	gt.main(template_options);

	datasets = []

	templates_directory = os.getenv('OPERATIONS') + "/TEMPLATES/"

	# Obtains list of datasets to run processSentinel on
	datasets = glob.glob(templates_directory + "*.template")
	datasets = [d.split('.', 1)[0].split('/')[-1] for d in datasets]
	if inps.dataset:
		datasets = [d for d in datasets if d == inps.dataset]

	all_output_files = []

	logger.info("\tDATASETS: \n " + str(datasets))

	# Perform the processing routine for each dataset
	for dset in datasets:

		dataset = dset;

		setup_logging_handlers(dataset, "a")

		# Generate SSARA Options to Use
		ssara_options = create_ssara_options()

		# Run SSARA and check output
		ssara_output = subprocess.check_output(ssara_options).decode('utf-8');

		# Sets date variables for stored and most recent dates
		set_dates(ssara_output)

		psen_time = datetime.fromtimestamp(time.time()).strftime(date_format)

		if compare_dates():

			# Write that stored date was overwritten
			overwrite_stored_date()

			# Submit job via process_sentinel and store output
			logger.info("%s: STARTING PROCESS SENTINEL JOB AT: %s (newest date: %s)\n", dataset, psen_time, most_recent)
			files_to_move = run_process_sentinel()

			all_output_files += files_to_move;

		else:
			logger.info("%s: NO NEW DATA on %s (most recent: %s)\n", dataset, psen_time, stored_date)

		logger.removeHandler(info_handler)
		logger.removeHandler(error_handler)

		# Perform post processing on all of the output and error files produced by processSentinel
		while len(all_output_files) != 0:
			for i, file in enumerate(all_output_files):
				if os.path.exists(file) and os.path.isfile(file):
					files_to_move = [all_output_files[i], all_output_files[i + 1]]
					post_processing(files_to_move)

					all_output_files[:] = [f for fi in files_to_move if
										   fi not in file and fi not in all_output_files[i + 1]]

			time.sleep(60)

		logger.info("\tCOMPLETED AT: %s", datetime.fromtimestamp(time.time()).strftime(date_format))
		logger.info("----------------------------------\n")

	sys.exit()
