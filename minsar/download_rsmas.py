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

from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js

###############################################################################


def main(iargs=None):
    """Downloads data with ssara and asfserial scripts."""

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    command = os.path.basename(__file__) + ' ' + iargs[0]
    message_rsmas.log(inps.work_dir, command)

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'download_rsmas'
        work_dir = os.getcwd()
        job_name = job_file_name
        if inps.wall_time == 'None':
            inps.wall_time = config[job_file_name]['walltime']

        js.submit_script(job_name, job_file_name, sys.argv[:], work_dir, inps.wall_time)
        sys.exit(0)

    if not inps.template['topsStack.slcDir'] is None:
        slc_dir = inps.template['topsStack.slcDir']
    else:
        slc_dir = os.path.join(inps.work_dir, 'SLC')

    if not os.path.isdir(inps.work_dir):
        os.makedirs(inps.work_dir)

    if not os.path.isdir(slc_dir):
        os.makedirs(slc_dir)

    # if satellite is not Sentinel (not tried yet)
    if 'SenDT' not in inps.project_name and 'SenAT' not in inps.project_name:

        ssara_call = ['ssara_federated_query.py'] + inps.ssaraopt + ['--print', '--download']
        ssara_process = subprocess.Popen(ssara_call, shell=True).wait()
        completion_status = ssara_process.poll()

        return

    download('ssara', inps.customTemplateFile, slc_dir, outnum=1)
    #download('ssara', inps.customTemplateFile, slc_dir, outnum = 2)
    #download('asfserial', inps.customTemplateFile, slc_dir, outnum = 1)

    return None

###########################################################################################


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


def download(script_name, customTemplateFile, slc_dir, outnum):
    """
    Runs download script with given script name.
    :param script_name: Name of download script to run (ssara, asfserial)
    :param customTemplateFile: Template file to download data from.
    :param slc_dir: SLC directory inside work directory.
    """
    if script_name not in {'ssara', 'asfserial'}:
        print('{} download not supported'.format(script_name))

    out_file = os.path.join(os.getcwd(), 'out_download_{0}{1}'.format(script_name, outnum))
    command = 'download_{0}_rsmas.py {1}'.format(script_name, customTemplateFile)
    command = '({0} > {1}.o) >& {1}.e'.format(command, out_file)

    if os.getenv('DOWNLOADHOST') == 'local':
        print('Command: ' + command )
        proc = subprocess.Popen(command,  stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output, error = proc.communicate()
        if proc.returncode is not 0:
            raise Exception('ERROR downloading using: download_{0}_rsmas.py'.format(script_name))
    else:
        ssh_command_list = ['s.bgood', 'cd {0}'.format(slc_dir), command]
        host = os.getenv('DOWNLOADHOST')
        status = ssh_with_commands(host, ssh_command_list)

    print('Exit status from download_{0}_rsmas.py: {1}'.format(script_name, status))

###############################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
