#!/usr/bin/env python3
########################
# Author:  Falk Amelung
# 2/2020
#######################

import os
import subprocess
import sys
import glob
import time
import shutil
from pathlib import Path
import argparse
from minsar.objects.rsmas_logging import loglevel
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from natsort import natsorted

EXAMPLE = """example:
  remove_date_from_run_files.py 

  remove_date_from_run_files.py $PWD/run_files 20150325 --startRunFile 3
  \n
"""

##############################################################################

def main(iargs=None):
    """
    remove dates from run_files
    """

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Utility to remove dates from run_files',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument('run_files_dir', metavar="runfiles_DIR", default='run_files', help='run_files_dir [default: working_directory/run_files]')
    parser.add_argument('date', metavar="date", help='dates to be removed')
    parser.add_argument('--startRunFile', dest='start_run_file', default=1, type=int, help='start run file number (default = 1).\n')

    inps = parser.parse_args(args=iargs)

    print ('dir, date, start:',inps.run_files_dir, inps.date, inps.start_run_file)
    putils.run_remove_date_from_run_files(inps.run_files_dir, inps.date, inps.start_run_file)
    return None

##########################################################################

if __name__ == "__main__":
    main()
