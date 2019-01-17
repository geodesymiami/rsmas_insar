#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
from dataset_template import Template
import datetime
from rsmas_logging import rsmas_logger, loglevel
import messageRsmas
import _process_utilities as putils
import stat
import glob

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password
from download_ssara_rsmas import generate_ssaraopt_string

logfile_name = os.getenv('OPERATIONS') + '/LOGS/asfserial_rsmas.log'
logger = rsmas_logger(file_name=logfile_name)

inps = None

def create_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('template', metavar="FILE", help='template file to use.')

	return parser


def command_line_parse(args):
	global inps

	parser = create_parser()
	inps = parser.parse_args(args)

def generate_files_csv():
	""" Generates a csv file of the files to download serially.
	
		Uses the `awk` command to generate a csv file containing the data files to be download
		serially. The output csv file is then sent through the `sed` command to remove the first five
		empty values to eliminate errors in download_ASF_serial.py.
	
	"""
	ssaraopt = generate_ssaraopt_string(template_file=inps.template)
	ssaraopt = ssaraopt.split(' ')
	
	filecsv_options = ['ssara_federated_query.py']+ssaraopt+['--print', '|', 'awk', "'BEGIN{FS=\",\"; ORS=\",\"}{ print $14}'", '>', 'files.csv']
	csv_command = ' '.join(filecsv_options)
	subprocess.Popen(csv_command, shell=True).wait()
	sed_command = "sed 's/^.\{5\}//' files.csv > new_files.csv"
	
	subprocess.Popen(sed_command, shell=True).wait()
	

def run_download_asf_serial():
	""" Runs download_ASF_serial.py with proper files.
	
		Runs adapted download_ASF_serial.py with a CLI username and password and a csv file containing
		the the files needed to be downloaded (provided by ssara_federated_query.py --print)
		
	"""
	
	status = subprocess.Popen(['download_ASF_serial.py', '-username', password.asfuser, '-password', password.asfpass, 'new_files.csv']).wait()
	logger.log(loglevel.INFO, "EXIT CODE: %s", str(status))

	return status

def change_file_permissions():
	""" changes the permissions of downloaded files to 755 """
	
	zip_files = glob.glob('S1*.zip')
	for file in zip_files:
	    os.chmod(file,0o666)

if __name__ == "__main__":
        
	command_line_parse(sys.argv[1:])
	inps.project_name = putils.get_project_name(custom_template_file=inps.template)
	inps.work_dir = putils.get_work_directory(None, inps.project_name)
	inps.slcDir = inps.work_dir + "/SLC"
	os.chdir(inps.work_dir)
	messageRsmas.log(os.path.basename(sys.argv[0]) + ' ' + ' '.join(sys.argv[1::]))
	os.chdir(inps.slcDir)
	try:
	    os.remove(os.path.expanduser('~')+'/.bulk_download_cookiejar.txt')
	except OSError:
	    pass
	

	generate_files_csv()
	succesful = run_download_asf_serial()
	change_file_permissions()
	logger.log(loglevel.INFO, "SUCCESS: %s", str(succesful))
	logger.log(loglevel.INFO, "------------------------------------")

