#! /usr/bin/env python3
"""This script downloads SAR data and deals with various errors produced by download clients
   Author: Falk Amelung
   Created:12/2018
"""
###############################################################################

import os
import sys
import argparse
import subprocess

import messageRsmas
import _process_utilities as putils

###############################################################################
EXAMPLE = '''example:
  download_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
'''

def command_line_parse(iargs=None):
    """Command line parser."""
    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    return inps

def create_parser():
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(description='Downloads SAR data using a variety of scripts',
                                     formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('template_file', help='template file containing ssaraopt field')
    #parser.add_argument('template_file', help='template file containing ssaraopt field', nargs='?')
    return parser

###############################################################################
def main(iargs=None):
    """Downloads data with ssara and asfserial scripts."""

    inps = command_line_parse(iargs)

    project_name = putils.get_project_name(custom_template_file=inps.template_file)
    work_dir = putils.get_work_directory(None, project_name)
    slc_dir = os.path.join(work_dir, 'SLC')
    if not os.path.isdir(work_dir):
        os.makedirs(work_dir)
    if not os.path.isdir(slc_dir):
        os.makedirs(slc_dir)

    os.chdir(work_dir)

    # if satellite is not Sentinel (not tried yet)
    if 'SenDT' not in project_name and 'SenAT' not in project_name:

        from download_ssara_rsmas import generate_ssaraopt_string

        ssaraopt = generate_ssaraopt_string(template_file=inps.template)
        ssara_call = ['ssara_federated_query.py'] + ssaraopt + ['--print', '--download']
        ssara_process = subprocess.Popen(ssara_call, shell=True).wait()
        completion_status = ssara_process.poll()

        return

    out_file = os.getcwd() + '/' + 'out_download_ssara'
    command = 'download_ssara_rsmas.py ' + inps.template_file
    #messageRsmas.log(command)
    command = '('+command+' > '+out_file+'.o) >& '+out_file+'.e'
    command_list = ['s.cgood', 'cd ' + slc_dir, command] 
    ssh_proc = subprocess.Popen(['ssh', 'pegasus.ccs.miami.edu', 'bash -s -l'], stdin=subprocess.PIPE)
    for cmd in command_list:
        ssh_proc.stdin.write(cmd.encode('utf8'))
        ssh_proc.stdin.write('\n'.encode('utf8'))
    ssh_proc.communicate()
    print('Exit status from download_ssara_rsmas.py:', ssh_proc.returncode)

    out_file = os.getcwd() + '/' + 'out_download_asfserial1'
    command = 'download_asfserial_rsmas.py ' + inps.template_file
    #messageRsmas.log(command)
    command = '('+command+' > '+out_file+'.o) >& '+out_file+'.e'
    command_list = ['s.cgood', 'cd ' + slc_dir, command]
    ssh_proc = subprocess.Popen(['ssh', 'pegasus.ccs.miami.edu', 'bash -s -l'], stdin=subprocess.PIPE)
    for cmd in command_list:
        ssh_proc.stdin.write(cmd.encode('utf8'))
        ssh_proc.stdin.write('\n'.encode('utf8'))
    ssh_proc.communicate()
    print('Exit status from download_asfserial_rsmas.py:', ssh_proc.returncode)

    out_file = os.getcwd() + '/' + 'out_download_asfserial2'
    command = 'download_asfserial_rsmas.py ' + inps.template_file
    #messageRsmas.log(command)
    command = '('+command+' > '+out_file+'.o) >& '+out_file+'.e'
    command_list = ['s.cgood', 'cd ' + slc_dir, command]
    ssh_proc = subprocess.Popen(['ssh', 'pegasus.ccs.miami.edu', 'bash -s -l'], stdin=subprocess.PIPE)
    for cmd in command_list:
        ssh_proc.stdin.write(cmd.encode('utf8'))
        ssh_proc.stdin.write('\n'.encode('utf8'))
    ssh_proc.communicate()
    print('Exit status from download_asfserial_rsmas.py:', ssh_proc.returncode)

###########################################################################################
if __name__ == '__main__':
    main(sys.argv[1:])
