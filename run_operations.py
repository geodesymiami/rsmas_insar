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

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

job_to_dset = {}

#################### GLOBAL VARIABLES ####################

dataset = 'GalapagosSenDT128VV'		                # Single Dataset for Testing

user = subprocess.check_output(['whoami']).decode('utf-8').strip("\n")  			# Currently logged in user
	
stored_date = None					# previously stored date
most_recent = None					# date parsed from SSARA
inps = None;

std_formatter = logging.Formatter("%(message)s")

general = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/run_operations.log', 'a+', encoding=None)
general.setLevel(logging.DEBUG)
general.setFormatter(std_formatter)
logger.addHandler(general)

console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(std_formatter)
logger.addHandler(console)

info_handler = None
error_handler = None

"""
    Initializes logging handlers for INFO label and ERROR level file logging. Needed so as to be able to continue logging
    data to the appropiate dataset log after run_operations completes.
    Parameters: dset: str, the dataset to write log output for
                mode: str, the logfile write mode (can be write or append)
    Returns:    none
"""
def setup_logging_handlers(dset, mode):
	global info_handler, error_handler
	# create a file handler
	info_handler = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/'+dset+'_info.log', mode, encoding=None)
	info_handler.setLevel(logging.INFO)
	info_handler.setFormatter(std_formatter)
	logger.addHandler(info_handler)

	# create a file handler
	error_handler = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/'+dset+'_error.log', mode, encoding=None)
	err_formatter = logging.Formatter("%(levelname)s - %(message)s")
	error_handler.setLevel(logging.ERROR)
	error_handler.setFormatter(err_formatter)
	logger.addHandler(error_handler)

###################### Command Line Argument Processing #################

"""
    Defines commandline argument parser and command line arguments to accept
    Parameters: none
    Returns:    parser: argument parser object
"""
def create_process_sentinel_parser():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

	parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
	parser.add_argument("--dataset", dest='dataset', metavar="DATASET", help='Particular dataset to run')
	parser.add_argument('--templatecsv', dest='template_csv', metavar='FILE', help='local csv file containing template info.')
	parser.add_argument('--singletemplate', dest='single_template', metavar='FILE', help='singular template file to run on')
	parser.add_argument('--startssara', dest='startssara', action='store_true', help='process_sentinel.py --startssara')
	parser.add_argument('--startprocess', dest='startprocess', action='store_true', help='process using sentinelstack package')
	parser.add_argument('--startpysar', dest='startpysar', action='store_true', help='run pysar')
	parser.add_argument('--startinsarmaps', dest='startinsarmaps', action='store_true', help='ingest into insarmaps')
	parser.add_argument("--testsheet", dest="test_sheet", action='store_true', help="whether or not to use the test sheet rather than the production sheet")

	return parser

"""
    Parses command line arguments into inps object as object parameters
    Parameters: args: [str], array of command line arguments
    Returns:    none
"""	
def command_line_parse(args):
	global inps;

	parser = create_process_sentinel_parser()
	inps = parser.parse_args(args)
	
	logger.info("--dataset	      	: %s", inps.dataset)
	logger.info("--templatecsv      : %s", inps.template_csv)
	logger.info("--singletemplate   : %s", inps.single_template)
	logger.info("--startssara       : %s", inps.startssara)
	logger.info("--startprocess     : %s", inps.startprocess)
	logger.info("--startpysar       : %s", inps.startpysar)
	logger.info("--startinsarmaps   : %s", inps.startinsarmaps)
	logger.info("--testsheet	: %s", inps.test_sheet)
	
	
###################### Auxiliary Functions #####################
"""
    Obtains the currently logged in user using the `whoami` command with subprocess
    Parameters: none
    Returns:    none
"""
def get_user(): 
	global user
	user = subprocess.check_output(['whoami']).decode('utf-8').strip("\n")

"""
    Reads template file for the current dataset and parses out the 'ssaraopt' option before creating command options line options 
    array for ssara_federated_query.py
    Parameters: none
    Returns:    ssara_options: [str], array of command line options to run ssara_federated_query with
"""
def create_ssara_options():
	
	with open('/nethome/'+user+'/insarlab/OPERATIONS/TEMPLATES/'+dataset+'.template', 'r') as template_file:
		options = ''
		for line in template_file:
			if 'ssaraopt' in line:
				options = line.strip('\n').rstrip().split("= ")[1]
				logger.info("OPTIONS: %s", str(options))
				break;
					
	# Compute SSARA options to use
	options = options.split(' ')
	logger.debug("OPTIONS ARRAY: %s", str(options))

	ssara_options = ['ssara_federated_query.py'] + options + ['--print']
	
	logger.debug("SSARA OPTIONS: %s", str(ssara_options))	
		
	return ssara_options
		
"""
    Reads the most recently stored date for the given dataset from the stored_date.date file, and parses the newest data date from
    ssara_federated_query.
    Parameters: ssara_output: str, string output from ssara_federated_query.py ... --print
    Returns:    none
"""
def set_dates(ssara_output):
	global stored_date, most_recent
	
	most_recent_data = ssara_output.split("\n")[-2]
	most_recent = datetime.strptime(most_recent_data.split(",")[3], "%Y-%m-%dT%H:%M:%S.%f")

	# Write Most Recent Date to File
	logger.info("\nNEWEST DATE: %s\n", str(most_recent))

	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'rb') as stored_date_file:
	
		try:
			date_line = subprocess.check_output(['grep', dataset, os.getenv('OPERATIONS')+'/stored_date.date']).decode('utf-8')
			stored_date = datetime.strptime(date_line.split(": ")[1].strip('\n'), "%Y-%m-%dT%H:%M:%S.%f")
		except subprocess.CalledProcessError as e:
			stored_date = datetime.strptime("1970-01-01T12:00:00.000000", "%Y-%m-%dT%H:%M:%S.%f")
			with open(os.getenv('OPERATIONS')+'/stored_date.date', 'a+') as date_file:
				data = str(dataset + ": "+str(datetime.strftime(most_recent, "%Y-%m-%dT%H:%M:%S.%f"))+"\n")
				date_file.write(data)

"""
    Compares the most recent and stored dates 
    Parameters: none
    Returns:    boolean, whether the most recent data is more recent than the stored date
"""
def compare_dates():
	global stored_date, most_recent
	
	return most_recent > stored_date
	
"""
    Overwrites the date stored in the stored_date.date file for the given dataset
    Parameters: none
    Returns:    none
"""
def overwrite_stored_date():
	global user, most_recent

	logger.info("STORED DATE OVERWRITTEN TO: %s", str(most_recent))
	
	data = []
	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'r') as date_file:
		data = date_file.readlines();
	
	for i, line in enumerate(data):
		if dataset in line:
			data[i] = str(dataset + ": "+str(datetime.strftime(most_recent, "%Y-%m-%dT%H:%M:%S.%f"))+"\n")

	logger.debug("DATE FILE OVERWRITTEN WITH: %s", str(data))
	
	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'w') as date_file:
		date_file.writelines(data)

"""
    Runs processSentinel.py with the associated options as defined by the provided command line arguments
    Parameters: none
    Returns:    [files], [str] an array of file paths to the processSentinel output and error files
"""
def run_process_sentinel():
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
		
	psen_options = ['process_sentinel.py', '/nethome/'+user+'/insarlab/OPERATIONS/TEMPLATES/'+dataset+'.template'] + psen_extra_options + ['--bsub']
	
	psen_output = subprocess.check_output(psen_options).decode('utf-8')
	
	job_number = psen_output.split('\n')[0].split("<")[1].split('>')[0]
	
	job_to_dset[job_number] = dataset
	
	logger.info("JOB NUMBER: %s", job_number)
	
	stdout_file_path = os.getenv('SCRATCHDIR')+dataset+'/z_processSentinel_'+job_number+'.o'
	stderr_file_path = os.getenv('SCRATCHDIR')+dataset+'/z_processSentinel_'+job_number+'.e'
	
	return [stdout_file_path, stderr_file_path]

"""
    Copies the output and error files from processSentinel to the $OPERATIONS/ERRORS directory
    Parameters: files_to_move: [str], arrays of files to move to the ERRORS directory
    Returns:    none
"""
def post_processing(files_to_move):
	global output_file, most_recent
	
	job = files_to_move[0].split('/z_processSentinel_')[1].strip(".o")
	
	setup_logging_handlers(job_to_dset[job], "a+")
	
	for file in files_to_move:
		if os.path.exists(file) and os.path.isfile(file):

			base = os.getenv('OPERATIONS') + '/ERRORS/'+dataset+'/'

			if not os.path.exists(base):
				os.makedirs(base)

			dest = base + str(most_recent)[0:10]
			if file[-1] is 'o':
				dest += '.o'
			elif file[-1] is 'e':
				dest += '.e'

			shutil.copy(file, dest)
			logger.info("COPIED %s to %s", file, dest)
			
		else:
			logger.error("%s does not exist!", file)
			raise IOError
			
	logger.info("----------------------------------")
	logger.error("-----------------------------------")
	logger.removeHandler(info_handler)
	logger.removeHandler(error_handler)


if __name__ == "__main__":
	
	# Parse command line arguments
	command_line_parse(sys.argv[1:])
	
	# Determine Currently Logged in User                                                                                                                                     
	get_user()
	
	# Generate Template Files
	template_options = []
	if inps.template_csv:
		template_options.append('--csv')
		template_options.append(inps.template_csv)
		logger.debug("GENERATING TEMPLATE FROM FILE: %s", inps.template_csv)
	if inps.dataset:
		template_options.append('--dataset')
		template_options.append(inps.dataset)
		logger.info("GENERATING TEMPLATE FOR DATASET: %s", inps.dataset)
	if inps.test_sheet:
		template_options.append('--testsheet')
		logger.info("USING TEST GOOGLE SHEET")
	
	logger.debug("TEMPLATE OPTIONS: %s", str(template_options))
	
	gt.main(template_options);
	
	datasets = []
	
	templates_directory = os.getenv('OPERATIONS') + "/TEMPLATES/"
	
	# Obtains list of datasets to run processSentinel on
	datasets = glob.glob(templates_directory+"*.template")
	datasets = [d.split('.', 1)[0].split('/')[-1] for d in datasets]	
	if inps.dataset:
		datasets = [d for d in datasets if d == inps.dataset]
			
	logger.warning("DATASETS: %s", str(datasets));

	logger.info("TEMPLATE GENERATION COMPLETED\n")

	all_output_files = []

	# Perform the processing routine for each dataset
	for dset in datasets:
		
		dataset = dset;
		
		setup_logging_handlers(dataset, "a")
		
		# Debugguing Outfile and Error File                                                                                                                              
		logger.info("\nSTART TIME: %s", datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
		logger.info("USER: %s\n", user)
		logger.info("DATASET: %s", dataset)
		
		# Generate SSARA Options to Use
		ssara_options = create_ssara_options()
		
		# Run SSARA and check output	
		ssara_output = subprocess.check_output(ssara_options).decode('utf-8');
		
		# Sets date variables for stored and most recent dates
		set_dates(ssara_output)

		if compare_dates():

			# Write that stored date was overwritten
			logger.info("NEW DATA EXISTS, STORED DATE BEING OVERWRITTEN")
			overwrite_stored_date()
			
			# Submit job via process_sentinel and store output
			logger.warning("STARTING PROCESS SENTINEL JOB")
			files_to_move = run_process_sentinel()
		
			logger.info("PROCESS SENTINEL JOB BEGAN AT: %s", datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
			
			all_output_files += files_to_move;
			
		else:
			logger.info("NO NEW DATA!\n")
			logger.info("----------------------------------")
			logger.error("-----------------------------------")

		logger.removeHandler(info_handler)
		logger.removeHandler(error_handler)
		
		# Perform post processing on all of the output and error files produced by processSentinel
		while len(all_output_files) != 0:
			for i, file in enumerate(all_output_files):
				if os.path.exists(file) and os.path.isfile(file):
					files_to_move = [all_output_files[i], all_output_files[i+1]]
					post_processing(files_to_move)
				
					all_output_files[:] = [f for fi in files_to_move if fi not in file and fi not in all_output_files[i+1]]
				
			time.sleep(60)

      	logger.warning("run_operations COMPLETE")
	logger.info("END TIME: %s", datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))	
	
	sys.exit()
