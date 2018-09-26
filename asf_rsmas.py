#!/usr/bin/python

import subprocess
import os

if __name__ == "__main__":
	
	filecsv_options = ['ssara_federated_query.py']+options+['--print', '|', 'awk', "'BEGIN{FS=\",\"; ORS=\",\"}{ print $14}'", '>', 'files.csv']
	csv_command = ' '.join(filecsv_options)
	filescsv_status = subprocess.Popen(csv_command, shell=True).wait()
	sed_command = "sed 's/^.\{5\}//' files.csv > new_files.csv";
	subprocess.Popen(sed_command, shell=True).wait()
	
	asf_command = "download_ASF_serial.py --username "+password.asfuser+" --password "+password.asfpass+' new_files.csv'
	
	serial_status = subprocess.Popen(asf_command).wait()
	
