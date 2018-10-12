#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse

inps = None;

def create_argument_parser():
	parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
	
	group = parser.add_argument_group('Input File', 'File/Dataset to display')
	group.add_argument("file", type=str, help="The file to batch create")
	group.add_argument("--template", dest='template', metavar="FILE", help='The template file with options')
	group.add_argument("--memory", dest='memory', metavar="NUMBER", help='Amount of memory to allocate')
	group.add_argument("--wall", dest='wall', metavar="NUMBER", help='Amount of wlal time to use')

	return parser
	
def parse_arguments(args):
	global inps
	
	parser = create_argument_parser()
	inps = parser.parse_args(args)
	
	if inps.memory is None:
		inps.memory = 3600
	if inps.wall is None:
		inps.wall = "4:00"
	
def read_input_file_to_array():
	
	files_array = []
	with open(inps.file) as file:
		files_array = file.readlines()
	
	print(files_array)
	
	return files_array
	
def write_job_files():
	
	files_array = read_input_file_to_array()
	
	job_files = []
	
	for i, file_name in enumerate(files_array):
	
		job_file_name = inps.file.split("/")[-1]+"_"+str(i)+".job";
		job_name = job_file_name.split(".")[0]
		job_file_lines = [
			
			"#! /bin/bash",
			"\n#BSUB -J "+ job_name, 
			"\n#BSUB -P insarlab",
			"\n#BSUB -n 1",
			"\n#BSUB -R span[hosts=1]",
			"\n#BSUB -o "+job_name+"%J.o",
			"\n#BSUB -e "+job_name+"%J.e",
			"\n#BSUB -q general",
			"\n#BSUB -W "+str(inps.wall),
			"\n#BSUB -R rusage[mem="+str(inps.memory)+"]",
			"\nfree",
			"\ncd /scratch/projects/insarlab/"+os.getlogin()+"/"+inps.file.split("/")[-3]+"/run_files/",
			"\n"+file_name
			
		]
		
		with open("/Users/joshua/Desktop/"+job_file_name, "w+") as job_file:
			job_file.writelines(job_file_lines)
			job_files.append(job_file.name)
			
	return job_files
	
def submmit_jobs_to_bsub(job_files):
	
	files = []
	
	for job in job_files:
		command = "bsub < "+job
		output = subprocess.check_output(command.split(" "))
		job_number = output.split('\n')[0].split("<")[1].split('>')[0]
		
		files_to_add = 
			
if __name__ == "__main__":
	
	parse_arguments(sys.argv[1:])
	job_files = write_job_files()
	print(job_files)
	submmit_jobs_to_bsub(job_files)
