#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

std_formatter = logging.Formatter("%(levelname)s - %(message)s")

general = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/ssara_rsmas.log', 'a+', encoding=None)
general.setLevel(logging.INFO)
general.setFormatter(std_formatter)
logger.addHandler(general)


"""
    Checks if the files too be downloaded actually exist or not on the system as a means of validating whether
    or not the wrapper completed succesdully.

    Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
    Returns: none

"""
def check_downloads(run_number):
	ssara_output = subprocess.check_output(['ssara_federated_query.py']+sys.argv[1:len(sys.argv)]+["--print"])
	ssara_output_array = ssara_output.decode('utf-8').split('\n')
	ssara_output_filtered = ssara_output_array[5:len(ssara_output_array)-1]

	files_to_check = []
	for entry in ssara_output_filtered:
		files_to_check.append(entry.split(',')[-1].split('/')[-1])


	for f in files_to_check:
		if not os.path.isfile(f):
			logger.warning("The file, %s, didn't download correctly. Running ssara again.", f)
			run_ssara(run_number+1, serial=True)
			return

"""
     Runs ssara_federated_query-cj.py and checks continuously for whether the data download has hung without comleting
     or exited with an error code. If either of the above occur, the function is run again, for a maxiumum of 10 times.
         
     Parameters: run_number: int, the current iteration the wrapper is on (maxiumum 10 before quitting)
     Returns: none

"""	
def run_ssara(run_number=1, serial=False):

	logger.info("RUN NUMBER: %s\n", str(run_number))	
	if not serial and run_number > 10:
		return
		
	if serial and run_number > 2:
		return
	
	args = sys.argv[1:len(sys.argv)]
	if serial:
		if "--parallel" in args:
			args.remove("--parallel");
			
	
	
	command = 'ssara_federated_query-cj.py ' + ' '.join(args)
	
	ssara_process = subprocess.Popen(["ssara_federated_query-cj.py"] + args)
		
	completion_status = ssara_process.poll()
	hang_status = False
	wait_time = 10	# wait time in `minutes` to determine hang status
	
	prev_size = -1
	
	i=0
	while completion_status is None:
		
		i=i+1
		curr_size = int(subprocess.check_output(['du','-s', os.getcwd()]).split()[0].decode('utf-8'))

		if prev_size == curr_size:
			hang_status = True
			logger.warning("SSARA Hung\n")
			ssara_process.terminate()
			break;
		
		time.sleep(60*wait_time)
		prev_size = curr_size
		completion_status = ssara_process.poll()
		logger.info("{} minutes: {:.1f}GB, completion_status {} \n".format(i*wait_time, curr_size/1024/1024, completion_status))
			
	exit_code = completion_status
	logger.info("EXIT CODE: %s", str(exit_code))
	
	bad_codes = [137]
	
	if exit_code in bad_codes or hang_status:
		logger.warning("Something went wrong, running again\n")
		run_ssara(run_number=run_number+1)

	check_downloads(run_number)
	
	logger.info("-------------------------------------------")

	return


if __name__ == "__main__":
	
	run_ssara()					
					
