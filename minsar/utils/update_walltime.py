#! /usr/bin/env python3
import os
import sys
import shutil
import time
import argparse
import subprocess
import minsar
import minsar.utils.process_utilities as putils

def main(iargs=None):

     parser = argparse.ArgumentParser(description='CLI Parser')
     arg_group = parser.add_argument_group('General options:')
     arg_group.add_argument('job_file_name', help='The job file that failed with a timeout error.\n')

     inps = parser.parse_args(args=iargs)

     wall_time = putils.extract_walltime_from_job_file(inps.job_file_name)
     new_wall_time = putils.multiply_walltime(wall_time, factor=1.2)
     putils.replace_walltime_in_job_file(inps.job_file_name, new_wall_time)

if __name__ == "__main__":
     main()
