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
    # parser.add_argument('template_file', help='template file containing ssaraopt field', nargs='?')
    return parser


def ssh_with_commands(hostname, command_list):
    """
    Uses subprocess to ssh into a specified host and run the given commands.
    :param hostname: Name of host to ssh to.
    :param command_list: List of commands to run after connecting via ssh.
    :return: Exit status from subprocess.
    """
    ssh_proc = subprocess.Popen(['ssh', hostname, 'bash -s -l'], stdin=subprocess.PIPE)
    for cmd in command_list:
        ssh_proc.stdin.write(cmd.encode('utf8'))
        ssh_proc.stdin.write('\n'.encode('utf8'))
    ssh_proc.communicate()
    return ssh_proc.returncode


def download(script_name, template_file, slc_dir):
    """
    Runs download script with given script name.
    :param script_name: Name of download script to run (ssara, asfserial1, or asfserial2)
    :param template_file: Template file to download data from.
    :param slc_dir: SLC directory inside work directory.
    """
    if script_name not in {'ssara', 'asfserial1', 'asfserial2'}:
        print('{} download not supported'.format(script_name))
    out_file = os.path.join(os.getcwd(), 'out_download_{0}'.format(script_name))
    if script_name in {'asfserial1', 'asfserial2'}:
        script_name = 'asfserial'
    command = 'download_{0}_rsmas.py {1}'.format(script_name, template_file)
    # messageRsmas.log(command)
    command = '({0} > {1}.o) >& {1}.e'.format(command, out_file)
    ssh_command_list = ['s.cgood', 'cd {0}'.format(slc_dir), command]
    host = 'pegasus.ccs.miami.edu'
    status = ssh_with_commands(host, ssh_command_list)
    print('Exit status from download_{0}_rsmas.py: {1}'.format(script_name, status))


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

    download('ssara', inps.template_file, slc_dir)
    download('asfserial1', inps.template_file, slc_dir)
    download('asfserial2', inps.template_file, slc_dir)

###########################################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
