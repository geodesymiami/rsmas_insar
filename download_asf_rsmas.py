#!/usr/bin/python
import os
import sys
import subprocess

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password


if __name__ == "__main__":
	
	with open(sys.argv[1], 'r') as template_file:
		options = ''
		for line in template_file:
			if 'ssaraopt' in line:
				options = line.strip('\n').rstrip().split("= ")[1].split(' ')
				break;				
	
	filecsv_options = ['ssara_federated_query.py']+options+['--print', '|', 'awk', "'BEGIN{FS=\",\"; ORS=\",\"}{ print $14}'", '>', 'files.csv']
	csv_command = ' '.join(filecsv_options)
	filescsv_status = subprocess.Popen(csv_command, shell=True).wait()
	sed_command = "sed 's/^.\{5\}//' files.csv > new_files.csv";
	subprocess.Popen(sed_command, shell=True).wait()
	
	serial_status = subprocess.Popen(['download_ASF_serial.py', '-username', password.asfuser, '-password', password.asfpass, 'new_files.csv']).wait()
	
