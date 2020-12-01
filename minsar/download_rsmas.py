#! /usr/bin/env python3
"""This script downloads SAR data and deals with various errors produced by download clients
   Author: Falk Amelung, Sara Mirzaee
   Created:12/2018
"""
###############################################################################

import os
import sys
import subprocess
import time
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar.utils import check_download
from contextlib import redirect_stdout
import io
from minsar.utils.download_ssara import add_polygon_to_ssaraopt
from minsar.utils.download_ssara import add_point_to_ssaraopt

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

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_obj = JOB_SUBMIT(inps)
        job_name = 'download_rsmas'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)

    if inps.prefix == 'tops':
        if not inps.template[inps.prefix + 'Stack.slcDir'] in [None, 'None']:
            download_dir = os.path.abspath(inps.template[inps.prefix + 'Stack.slcDir'])
        else:
            download_dir = os.path.join(inps.work_dir, 'SLC')
    else:
        if not inps.template['raw_image_dir'] in [None, 'None']:
            download_dir = inps.template['raw_image_dir']
        else:
            download_dir = os.path.join(inps.work_dir, 'RAW_data')

    os.makedirs(inps.work_dir, exist_ok=True)
    os.makedirs(download_dir, exist_ok=True)

    if 'CSK' in inps.project_name:
        command = 'download_gep_csk.py {}'.format(inps.custom_template_file)
        os.system(command)
        return

    if 'SenDT' not in inps.project_name and 'SenAT' not in inps.project_name or os.getenv('SSARA_ASF') == 'False':
        
        try:
           # inps.template['ssaraopt.intersectsWithPoint']
           inps.ssaraopt = ' '.join(add_point_to_ssaraopt(inps.template, inps.ssaraopt.split(' ')))
        except:
           inps.ssaraopt = ' '.join(add_polygon_to_ssaraopt(inps.template, inps.ssaraopt.split(' '), delta_lat=inps.delta_lat)) 
        command = 'ssara_federated_query.py ' + inps.ssaraopt + ' --print' + ' --download'

        os.chdir(download_dir)
        message_rsmas.log(download_dir, command)

        status = subprocess.Popen(command, shell=True).wait()

        if status is not 0:
            raise Exception('ERROR in ssara_federated_query.py')

        os.chdir(inps.work_dir)
        return

    if os.getenv('SSARA_ASF') == 'False':
        return

    download('ssara', inps.custom_template_file, download_dir, outnum=1)
    #download('asfserial', inps.custom_template_file, download_dir, outnum = 1)

    for i_download in [2, 3]:
        download_success = run_check_download(download_dir = download_dir)

        if not download_success:
           print('check_download.py: There were bad files, download again')
           message_rsmas.log(inps.work_dir,'check_download.py: there were bad files, download again')

           download('ssara', inps.custom_template_file, download_dir, outnum = i_download)
           #download('asfserial', inps.custom_template_file, download_dir, outnum = i_download)

###########################################################################################

def run_check_download(download_dir):
    """ 
    Runs check_download script and returns True if all *zip files are fine and False otherwise.
    :param download_dir: SLC/download directory to check
    """
    f = io.StringIO()
    with redirect_stdout(f):
        check_download.main([download_dir, '--delete'])
        out = f.getvalue()
   
    if 'Broken zipfiles' in out or 'Files with ' in out:
        print ('Bad downloads found')
        return False
    else:
        return True

###########################################################################################


def download(script_name, custom_template_file, download_dir, outnum):
    """
    Runs download script with given script name.
    :param script_name: Name of download script to run (ssara, asfserial)
    :param custom_template_file: Template file to download data from.
    :param download_dir: SLC/download directory inside work directory.
    """
    if script_name not in {'ssara', 'asfserial'}:
        print('{} download not supported'.format(script_name))

    out_file = os.path.join(os.path.dirname(download_dir), 'out_download_{0}{1}'.format(script_name, outnum))
    command = 'download_{0}_rsmas.py {1}'.format(script_name, custom_template_file)
    command = '({0} > {1}.o) >& {1}.e'.format(command, out_file)

    if os.getenv('DOWNLOADHOST') == 'local':
        print('Command: ' + command)
        proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        output, error = proc.communicate()
        if proc.returncode is not 0:
            raise Exception('ERROR downloading using: download_{0}_rsmas.py'.format(script_name))
    else:
        ssh_command_list = ['s.bgood', 'cd {0}'.format(download_dir), command]
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
