#!/usr/bin/python
import os
import sys
import subprocess

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

def generate_files_csv():
	""" Generates a csv file of the files to download serially.
	
		Uses the `awk` command to generate a csv file containing the data files to be download
		serially. The output csv file is then sent through the `sed` command to remove the first five
		empty values to eliminate errors in download_ASF_serial.py.
	
	"""
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
	
def run_download_asf_serial():
	""" Runs download_ASF_serial.py with proper files.
	
		Runs adapted download_ASF_serial.py with a CLI username and password and a csv file containing
		the the files needed to be downloaded (provided by ssara_federated_query.py --print)
		
	"""
	
	status = subprocess.Popen(['download_ASF_serial.py', '-username', password.asfuser, '-password', password.asfpass, 'new_files.csv']).wait()
	
	return status

if __name__ == "__main__":
	
	generate_files_csv()
	run_download_asf_serial()
	
	
	
