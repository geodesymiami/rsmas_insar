#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import logging
import datetime
import argparse

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

inps = None

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
std_formatter = logging.Formatter("%(levelname)s - %(message)s")

# ssara_rsmas.log File Logging
fileHandler = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/ssara_rsmas.log', 'a+', encoding=None)
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(std_formatter)

# command line logging
streamHandler = logging.StreamHandler()
streamHandler.setLevel(logging.INFO)
streamHandler.setFormatter(std_formatter)

logger.addHandler(fileHandler)
logger.addHandler(streamHandler)

def create_parser():
	""" Creates command line argument parser object. """
	
	parser = argparse.ArgumentParser()
	parser.add_argument('template', type=str,  metavar="FILE", help='template file to use.')
	
	return parser
	
def command_line_parse(args):
	""" Parses command line agurments into inps variable. """
	
	global inps;
	
	parser = create_parser();
	inps = parser.parse_args(args)


def check_downloads(run_number, args):
	""" Checks if all of the ssara files to be dwonloaded actually exist.
	
		Checks if the files to be downloaded actually exist or not on the system as a means of validating 
		whether or not the wrapper completed succesfully.

		Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
					args: [string], ssara_federated_query.py options to run with
					
		Returns: none

	"""
	ssara_output = subprocess.check_output(['ssara_federated_query-cj.py']+args[1:len(args)]+["--print"])
	ssara_output_array = ssara_output.decode('utf-8').split('\n')
	ssara_output_filtered = ssara_output_array[5:len(ssara_output_array)-1]

	files_to_check = []
	for entry in ssara_output_filtered:
		files_to_check.append(entry.split(',')[-1].split('/')[-1])


	for f in files_to_check:
		if not os.path.isfile(str(os.getcwd())+"/"+str(f)):
			logger.warning("The file, %s, didn't download correctly. Running ssara again.", f)
			run_ssara(run_number+1)
			return
			
	logger.info("Everything is there!")


def run_ssara(run_number=1):
	""" Runs ssara_federated_query-cj.py and checks for download issues.
	
		Runs ssara_federated_query-cj.py and checks continuously for whether the data download has hung without 
		comleting or exited with an error code. If either of the above occur, the function is run again, for a 
		maxiumum of 10 times.
		
		Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
		Returns: status_cod: int, the status of the donwload (0 for failed, 1 for success)

	"""	


	logger.info("RUN NUMBER: %s", str(run_number))	
	if run_number > 10:
		return 0	
	
	# Compute SSARA options to use 
	with open(inps.template, 'r') as template_file:
		options = ''
		for line in template_file:
			if 'ssaraopt' in line:
				options = line.strip('\n').rstrip().split("= ")[1]
				break;
	options = options.split(' ')

	# Runs ssara_federated_query-cj.py with proper options
	ssara_options = ['ssara_federated_query-cj.py'] + options + ['--parallel', '10', '--print', '--download']	
	ssara_process = subprocess.Popen(ssara_options)
		
	completion_status = ssara_process.poll()	# the completion status of the process
	hang_status = False							# whether ot not the download has hung
	wait_time = 10								# wait time in 'minutes' to determine hang status
	prev_size = -1								# initial download directory size
	i=0											# the iteration number (for logging only)
	
	# while the process has not completed
	while completion_status is None:
		
		i=i+1
		
		# Computer the current download directory size
		curr_size = int(subprocess.check_output(['du','-s', os.getcwd()]).split()[0].decode('utf-8'))

		# Compare the current and previous directory sizes to determine determine hang status
		if prev_size == curr_size:
			hang_status = True
			logger.warning("SSARA Hung")
			ssara_process.terminate()	# teminate the process beacause download hung
			break;						# break the completion loop 
		
		time.sleep(60*wait_time)		# wait 'wait_time' minutes before continuing
		prev_size = curr_size
		completion_status = ssara_process.poll()
		logger.info("{} minutes: {:.1f}GB, completion_status {}".format(i*wait_time, curr_size/1024/1024, completion_status))
			
	exit_code = completion_status 	# get the exit code of the command
	logger.info("EXIT CODE: %s", str(exit_code))
	
	bad_codes = [137]
	
	# If the exit code is one that signifies an error, rerun the entire command
	if exit_code in bad_codes or hang_status:
		logger.warning("Something went wrong, running again")
		run_ssara(run_number=run_number+1)

	return 1


if __name__ == "__main__":
	command_line_parse(sys.argv[1:])
	logger.info("DATASET: %s", str(inps.template.split('/')[-1].split(".")[0]))
	logger.info("DATE: %s", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
	succesful = run_ssara()
	logger.info("SUCCESS: %s", str(succesful))
	logger.info("------------------------------------")					
