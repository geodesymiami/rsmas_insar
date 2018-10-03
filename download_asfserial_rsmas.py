#!/usr/bin/python
import os
import sys
import subprocess
import logging
import argparse
import datetime
from rsmas_logging import rsmas_logger
from dataset_template import Template

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

logfile_name = os.getenv('OPERATIONS') + '/LOGS/asfserial_rsmas.log'
logger = rsmas_logger(file=logfile_name)

inps = None

def create_parser():
	parser = argparse.ArgumentParser()
	parser.add_argument('template', dest='template', metavar="FILE", help='template file to use.')

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
	options = Template(inps.template).get_options()['ssaraopt']
	options = options.split(' ')
	
	filecsv_options = ['ssara_federated_query.py']+options+['--print', '|', 'awk', "'BEGIN{FS=\",\"; ORS=\",\"}{ print $14}'", '>', 'files.csv']
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
	logger.log(logging.INFO, status)
	return status

if __name__ == "__main__":
	logger.log(logging.INFO, "DATASET: %s", str(inps.template.split('/')[-1].split(".")[0]))
	logger.log(logging.INFO, "DATE: %s", datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"))
	generate_files_csv()
	succesful = run_download_asf_serial()
	logger.log(logging.INFO, "SUCCESS: %s", str(succesful))
	logger.log(logging.INFO, "------------------------------------")

