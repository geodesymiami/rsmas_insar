#!/usr/bin/python
import os
import sys
import subprocess
import argparse

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

inps=None

def create_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('template', dest='template', metavar="FILE", help='template file to use.')
	
	return parser
	
def command_line_parse(args):
	global inps;
	
	parser = create_parser();
	inps = parser.parse_args(args) 

'''
	Creates a csv file composed of the list of data files to be downloaded for the template.
	The file is created by sending the output of ssara_federated_query.py ... --print through an
	'awk' command to grab the data file name and output it to files.csv. file.csv is then parsed
	through a `sed` command to remove the first 5 empty entries in files.csv and output the result
	to `new_files.csv`.
'''	
def create_downloads_file():
	
	with open(inps.template, 'r') as template_file:
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

if __name__ == "__main__":
	
	command_line_parse(sys.argv[1:])
	
	create_downloads_file()			
	
	serial_status = subprocess.Popen(['download_ASF_serial.py', '-username', password.asfuser, '-password', password.asfpass, 'new_files.csv']).wait()
	
