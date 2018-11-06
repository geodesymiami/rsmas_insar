#! /usr/bin/env python3
###############################################################################
# Author: Falk Amelung
# Created: 11/2018
###############################################################################
"""
check for existence of directories and empty files for run_operations.py,
create them as needed
"""
import os

def main():
    """ initiate directories for run_operations.py """

    operations_directory = os.getenv('OPERATIONS')
    templates_directory = operations_directory  + "/TEMPLATES/"
    logs_directory = operations_directory  + "/LOGS/"
    errors_directory = operations_directory  + "/ERRORS/"

    if not os.path.isdir(operations_directory):
        os.mkdir(operations_directory)
    if not os.path.isdir(templates_directory):
        os.mkdir(templates_directory)
    if not os.path.isdir(logs_directory):
        os.mkdir(logs_directory)
        open(logs_directory+'/generate_templates.log', 'a').close()  # create empty file
    if not os.path.isdir(errors_directory):
        os.mkdir(errors_directory)
    if not os.path.exists(os.getenv('OPERATIONS')+'/stored_date.date'):
        open(os.getenv('OPERATIONS')+'/stored_date.date', 'a').close()  # create empty file

###########################################################################################
if __name__ == '__main__':
    main()
