#!/usr/bin/env python3

import os
import sys
import time
import subprocess
import argparse

def get_dirsize(path):
	total_size = 0
	for dirpath, dirnames, filenames in os.walk(path):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			total_size += os.path.getsize(fp)
	print(total_size)
	return total_size
	
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
		completion_status = ssara_process.poll()
		download_speed = (curr_size - prev_size) / 1024 /  wait_time / 60
		print("{} minutes: {:.1f} GB, {:.1f} MB/s, {:.1f} GB/hr, completion_status: {} ".format(i*wait_time, 
                  curr_size/1024/1024, download_speed, download_speed*3600/1024, completion_status))
		prev_size = curr_size
			
	exit_code = completion_status

	bad_codes = [137]
	
	if exit_code in bad_codes or hang_status:
		print("Run Again")
		run_ssara(run_number=run_number+1)
		
	return


if __name__ == "__main__":
	
	run_ssara()					
					
