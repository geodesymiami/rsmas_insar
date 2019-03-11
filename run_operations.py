#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
from datetime import datetime
import shutil
import time
import glob

import subprocess
################### directory initiation for Josh to review (and remove comment)
status = subprocess.Popen('check_for_operations_directories_and_initiate.py', shell=True).wait() 
if status is not 0:
   raise Exception('ERROR in check_for_operations_directories_and_initiate.py')
##################

from download_ssara_rsmas import generate_ssaraopt_string
import generate_template_files as gt

import logging

#################### LOGGERS AND LOGGING SETUP ####################

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

std_formatter = logging.Formatter("%(message)s")

general = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/run_operations.log', 'a+', encoding=None)
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

dataset = 'GalapagosSenDT128VV'		                				        # Single Dataset for Testing

user = subprocess.check_output(['whoami']).decode('utf-8').strip("\n")  			# Currently logged in user
	
stored_date = None			  							# previously stored date
most_recent = None										# date parsed from SSARA
inps = None;				       							# command line arguments

job_to_dset = {}										# dictionary of jobs to datasets

date_format = "%Y-%m-%dT%H:%M:%S.%f"								# date format for reading and writing dates




"""
    Initializes logging handlers for INFO level and ERROR level file logging. Needed so as to be able to continue logging
    data to the appropiate dataset log after processSentinel completes.
    Parameters: dset: str, the dataset to write log output for
                mode: str, the logfile write mode (can be write or append)
    Returns:    none
"""
def setup_logging_handlers(dset, mode):
	global info_handler, error_handler
	
	# create a file handler for INFO level logging
	info_log_file = os.getenv('OPERATIONS')+'/LOGS/'+dset+'_info.log'
	info_handler = logging.FileHandler(info_log_file, mode, encoding=None)
	info_formatter = logging.Formatter("%(levelname)s - %(message)s")
	info_handler.setLevel(logging.INFO)
	info_handler.setFormatter(info_formatter)
	logger.addHandler(info_handler)

	# create a file handler for ERROR level logging
	error_log_file = os.getenv('OPERATIONS')+'/LOGS/'+dset+'_error.log'
	error_handler = logging.FileHandler(error_log_file, mode, encoding=None)
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
def create_process_rsmas_parser():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description="Submits processing jobs\
 for each datasest template present in the $OPERATIONS/TEMPLATES/ directory.  \nPlace run_operations_LSF.job file\
 into $OPERATIONS directory and submit with bsub < run_operations_LSF.job. \nIt runs run_operations.py once daily at 12:00 PM.")

	parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
	parser.add_argument("--dataset", dest='dataset', metavar="DATASET", help='Particular dataset to run')
	parser.add_argument('--templatecsv', dest='template_csv', metavar='FILE', help='local csv file containing template info.')
	parser.add_argument('--singletemplate', dest='single_template', metavar='FILE', help='singular template file to run on')
	parser.add_argument('--startssara', dest='startssara', action='store_true', help='process_rsmas.py --startssara')
	parser.add_argument('--stopssara', dest='stopssara', action='store_true', help='stop after downloading')
	parser.add_argument('--startprocess', dest='startprocess', action='store_true', help='process using sentinelstack package')
	parser.add_argument('--stopprocess', dest='stopprocess', action='store_true', help='stop after processing')
	parser.add_argument('--startpysar', dest='startpysar', action='store_true', help='run pysar')
	parser.add_argument('--stoppysarload', dest='stoppysarload', action='store_true', help='stop after loading into pysar')
	parser.add_argument('--stoppysar', dest='stoppysar', action='store_true', help='stop after pysar processing')
	parser.add_argument('--startinsarmaps', dest='startinsarmaps', action='store_true', help='ingest into insarmaps')
	parser.add_argument('--restart', dest='restart', action='store_true', help='remove $OPERATIONS directory before starting')
	parser.add_argument("--testsheet", dest="test_sheet", action='store_true', help='whether or not to use the test sheet')

	return parser

"""
    Parses command line arguments into inps object as object parameters
    Parameters: args: [str], array of command line arguments
    Returns:    none
"""	
def command_line_parse(args):
	global inps;

	parser = create_process_rsmas_parser()
	inps = parser.parse_args(args)
	
	logger.info("\tCOMMAND LINE VARIABLES:")
	logger.info("\t\t--dataset     	    : %s\n", inps.dataset)
	logger.info("\t\t--templatecsv      : %s\n", inps.template_csv)
	logger.info("\t\t--singletemplate   : %s\n", inps.single_template)
	logger.info("\t\t--startssara       : %s\n", inps.startssara)
	logger.info("\t\t--stopssara        : %s\n", inps.stopssara)
	logger.info("\t\t--startprocess     : %s\n", inps.startprocess)
	logger.info("\t\t--stopprocess      : %s\n", inps.stopprocess)
	logger.info("\t\t--startpysar       : %s\n", inps.startpysar)
	logger.info("\t\t--stoppysarload    : %s\n", inps.stoppysarload)
	logger.info("\t\t--stoppysar        : %s\n", inps.stoppysar)
	logger.info("\t\t--startinsarmaps   : %s\n", inps.startinsarmaps)
	logger.info("\t\t--testsheet	    : %s\n", inps.test_sheet)
	
###################### Auxiliary Functions #####################

"""
    Reads the most recently stored date for the given dataset from the stored_date.date file, and parses the newest data date from ssara_federated_query.
    Parameters: ssara_output: str, string output from ssara_federated_query.py ... --print
    Returns:    none
"""
def set_dates(ssara_output):
	global stored_date, most_recent
	
	most_recent_data = ssara_output.split("\n")[-2]
	most_recent = datetime.strptime(most_recent_data.split(",")[3], date_format)

	# Write Most Recent Date to File
	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'rb') as stored_date_file:
	
		try:
			date_line = subprocess.check_output(['grep', dataset, os.getenv('OPERATIONS')+'/stored_date.date']).decode('utf-8')
			stored_date = datetime.strptime(date_line.split(": ")[1].strip('\n'), date_format)
		except subprocess.CalledProcessError as e:
			
			stored_date = datetime.strptime("1970-01-01T12:00:00.000000", date_format)
			
			with open(os.getenv('OPERATIONS')+'/stored_date.date', 'a+') as date_file:
				data = str(dataset + ": "+str(datetime.strftime(most_recent, date_format))+"\n")
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
	
	data = []
	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'r') as date_file:
		data = date_file.readlines();
	
	for i, line in enumerate(data):
		if dataset in line:
			data[i] = str(dataset + ": "+str(datetime.strftime(most_recent, date_format))+"\n")
	
	with open(os.getenv('OPERATIONS')+'/stored_date.date', 'w') as date_file:
		date_file.writelines(data)

"""
    Submits a  processSentinel.py job with the associated options as defined by the provided command line arguments
    Parameters: none
    Returns:    [files], [str] an array of file paths to the processSentinel output and error files
"""
def run_process_rsmas():
	global user, dataset
	
	psen_extra_options = []
	
	if inps.startssara:
		psen_extra_options.append('--startssara')
	if inps.stopssara:
		psen_extra_options.append('--stopssara')
	if inps.startprocess:
		psen_extra_options.append('--startprocess') 
	if inps.stopprocess:
		psen_extra_options.append('--stopprocess') 
	if inps.startpysar:
		psen_extra_options.append('--startpysar')
	if inps.stoppysarload:
		psen_extra_options.append('--stoppysarload')
	if inps.stoppysar:
		psen_extra_options.append('--stoppysar')
	if inps.startinsarmaps:
		psen_extra_options.append('--startinsarmaps')
		
	if len(psen_extra_options) == 0:
		psen_extra_options.append('--insarmaps')
		
	psen_options = ['process_rsmas.py', os.getenv('OPERATIONS')+'/TEMPLATES/'+dataset+'.template'] + psen_extra_options + ['--submit']
	
	psen_output = subprocess.check_output(psen_options).decode('utf-8')
	
	job_number = psen_output.split('\n')[0].split("<")[1].split('>')[0]
	logger.info("JOB NUMBER: %s", job_number)
	
	job_to_dset[job_number] = dataset
	
	stdout_file_path = os.getenv('SCRATCHDIR')+'/'+dataset+'/z_processSentinel_'+job_number+'.o'
	stderr_file_path = os.getenv('SCRATCHDIR')+'/'+dataset+'/z_processSentinel_'+job_number+'.e'
	
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
			
		else:
			raise IOError
			
	logger.removeHandler(info_handler)
	logger.removeHandler(error_handler)

def copy_error_files_to_logs(project_dir, destination_dir):
	"""Copy out*.e files into LOGS/project_2017-03-20_out directory."""
	error_files=glob.glob('out*.e')
	if not os.path.isdir(destination_dir):
	    os.makedirs(destination_dir)
	for file in error_files:
	    shutil.copy(file, destination_dir)
           

if __name__ == "__main__":

	from datetime import datetime
	
	logger.info("RUN_OPERATIONS for %s:\n", datetime.fromtimestamp(time.time()).strftime(date_format))
	
	# Parse command line arguments
	command_line_parse(sys.argv[1:])
	
	# delete OPERATIONS folder if --restart
	if inps.restart:
	    shutil.rmtree(os.getenv('OPERATIONS'))
	    status = subprocess.Popen('check_for_operations_directories_and_initiate.py', shell=True).wait()
	    if status is not 0:
	       raise Exception('ERROR in check_for_operations_directories_and_initiate.py')
           
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
	datasets = glob.glob(templates_directory+"*.template")
	datasets = [d.split('.', 1)[0].split('/')[-1] for d in datasets]	
	if inps.dataset:
		datasets = [d for d in datasets if d == inps.dataset]

	all_output_files = []
	
	logger.info("\tDATASETS: \n "+str(datasets))
	
	# Perform the processing routine for each dataset
	for dset in datasets:
		
		dataset = dset;
		
		setup_logging_handlers(dataset, "a")
		
		template_file = templates_directory+'/'+dataset+'.template'

		dataset_template = Template(template_file)

		# Generate SSARA Options to Use
		ssaraopt = dataset_template.generate_ssaraopt_string()
		ssaraopt = 'ssara_federated_query.py ' + ssaraopt + ' --print'
		ssaraopt=ssaraopt.split(' ')
		
		# Run SSARA and check output	
		ssara_output = subprocess.check_output(ssaraopt).decode('utf-8');   #note to Josh: for easier debugging lets call using a string instead of a list
		
		# Sets date variables for stored and most recent dates
		set_dates(ssara_output)

		psen_time = datetime.fromtimestamp(time.time()).strftime(date_format)

		if compare_dates():

			# Write that stored date was overwritten
			overwrite_stored_date()
			
			# Submit job via process_rsmas and store output
			logger.info("%s: STARTING PROCESS SENTINEL JOB AT: %s (newest date: %s)\n", dataset, psen_time, most_recent)
			files_to_move = run_process_rsmas()
			
			all_output_files += files_to_move;
			
		else:
			logger.info("%s: NO NEW DATA on %s (most recent: %s)\n", dataset, psen_time, stored_date)

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
			
		log_dir = os.getenv('OPERATIONS')+'/LOGS/'+dset+'_'+str(most_recent)[0:10]+'_out'
		work_dir = os.getenv('SCRATCHDIR') + '/' + dset
		copy_error_files_to_logs( project_dir=work_dir, destination_dir=log_dir)

		logger.info("\tCOMPLETED AT: %s", datetime.fromtimestamp(time.time()).strftime(date_format))
		logger.info("----------------------------------\n")	
	
	sys.exit()
