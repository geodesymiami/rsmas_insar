#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

import messageRsmas
import _process_utilities as putils

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

def run_download_asf_serial():
	""" Runs download_ASF_serial.py with proper files.
	
		Runs adapted download_ASF_serial.py with a CLI username and password and a csv file containing
		the the files needed to be downloaded (provided by ssara_federated_query.py --print)
		
	"""
	
	status = subprocess.Popen(['download_ASF_serial.py', '-username', password.asfuser, '-password', password.asfpass, 'new_files.csv']).wait()
	
	return status

if __name__ == "__main__":
        
	command_line_parse(sys.argv[1:])
	inps.project_name = putils.get_project_name(custom_template_file=inps.template)
	inps.work_dir = putils.get_work_directory(None, inps.project_name)
	inps.slcDir = putils.get_slc_directory(inps.work_dir)
	os.chdir(inps.work_dir)
	messageRsmas.log(os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1::]))
	os.chdir(inps.slcDir)

	generate_files_csv()
	run_download_asf_serial()
	
	
	
