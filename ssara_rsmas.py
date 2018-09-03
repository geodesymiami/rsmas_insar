#!/usr/bin/env python3

import os
import sys
import time
import subprocess

	
def run_ssara(run_number=1):

	print("RUN NUMBER: "+str(run_number))	
	if run_number > 10:
		return
	
	command = 'ssara_federated_query-cj.py ' + ' '.join(sys.argv[1:len(sys.argv)])
	print(command)
	ssara_process = subprocess.Popen(["ssara_federated_query-cj.py"] + sys.argv[1:len(sys.argv)])
		
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
			print("SSARA Hung")
			ssara_process.terminate()
			break;
		
		time.sleep(60*wait_time)
		prev_size = curr_size
		completion_status = ssara_process.poll()
		print("{} minutes: {:.1f}GB, completion_status {} ".format(i*wait_time, curr_size/1024/1024, completion_status))
			
	exit_code = completion_status

	bad_codes = [137]
	
	if exit_code in bad_codes or hang_status:
		print("Run Again")
		run_ssara(run_number=run_number+1)

	ssara_output = subprocess.check_output(['ssara_federated_query.py']+sys.argv[1:len(sys.argv)]+["--print"])
	ssara_output_array = ssara_output.decode('utf-8').split('\n')
	ssara_output_filtered = ssara_output_array[5:len(ssara_output_array)-1]

	files_to_check = []
	for entry in ssara_output_filtered:
		files_to_check.append(entry.split(',')[-1].split('/')[-1])
		

	for f in files_to_check:
		if not os.path.isfile(f):
			run_ssara(run_number+1)
			return

	return


if __name__ == "__main__":
	
	run_ssara()					
					
