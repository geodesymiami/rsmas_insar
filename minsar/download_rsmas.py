#! /usr/bin/env python3
"""This script downloads SAR data and deals with various errors produced by download clients
   Author: Falk Amelung, Sara Mirzaee
   Created:12/2018
"""
###############################################################################

import os
import sys
import argparse
import subprocess
import time
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
from minsar.utils import download_ssara_rsmas, download_asfserial_rsmas, check_download
import contextlib
from contextlib import redirect_stdout
import io

class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
###############################################################################


def main(iargs=None):
    """Downloads data with ssara and asfserial scripts."""

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    job_file_name = 'download_rsmas'
    job_name = job_file_name

    if inps.wall_time == 'None':
        inps.wall_time = config[job_file_name]['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)
        sys.exit(0)

    time.sleep(wait_seconds)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

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

    download('ssara', inps.custom_template_file, slc_dir, outnum=1)
    download('asfserial', inps.custom_template_file, slc_dir, outnum = 1)

    for i_download in [2,3]:
        download_success = run_check_download(slc_dir = slc_dir)

        if not download_success:
           print('check_download.py: There were bad files, download again')
           message_rsmas.log(inps.work_dir,'check_download.py: there were bad files, download again')

           download('ssara', inps.custom_template_file, slc_dir, outnum = i_download)
           download('asfserial', inps.custom_template_file, slc_dir, outnum = i_download)

###########################################################################################

def run_check_download(slc_dir):
    """ 
    Runs check_download script and returns True if all *zip files are fine and False otherwise.
    :param slc_dir: SLC directory to check
    """
    f = io.StringIO()
    with redirect_stdout(f):
        check_download.main([slc_dir,'--delete'])
        out = f.getvalue()
   
    if 'Broken zipfiles' in out or 'Files with ' in out:
        print ('Bad downloads found')
        return False
    else:
        return True

###########################################################################################


def download(script_name, custom_template_file, slc_dir, outnum):
    """
    Runs download script with given script name.
    :param script_name: Name of download script to run (ssara, asfserial)
    :param custom_template_file: Template file to download data from.
    :param slc_dir: SLC directory inside work directory.
    """
    if script_name not in {'ssara', 'asfserial'}:
        print('{} download not supported'.format(script_name))

    out_file = os.path.join(os.path.dirname(slc_dir), 'out_download_{0}{1}'.format(script_name, outnum))
    command = 'download_{0}_rsmas.py {1}'.format(script_name, custom_template_file)
    command = '({0} > {1}.o) >& {1}.e'.format(command, out_file)

    if os.getenv('DOWNLOADHOST') == 'local':
        print('Command: ' + command)
        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output, error = proc.communicate()
        if proc.returncode is not 0:
            raise Exception('ERROR downloading using: download_{0}_rsmas.py'.format(script_name))
    else:
        ssh_command_list = ['s.bgood', 'cd {0}'.format(slc_dir), command]
        host = os.getenv('DOWNLOADHOST')
        status = ssh_with_commands(host, ssh_command_list)

        print('Exit status from download_{0}_rsmas.py: {1}'.format(script_name, status))

###############################################################################


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

###############################################################################


if __name__ == '__main__':
    main()
