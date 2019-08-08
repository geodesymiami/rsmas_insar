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

from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
from minsar.utils import download_ssara_rsmas, download_asfserial_rsmas
import contextlib
###############################################################################


def main(iargs=None):
    """Downloads data with ssara and asfserial scripts."""

    inps = putils.cmd_line_parse(iargs, script='download_rsmas')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

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


def download(script_name, customTemplateFile, slc_dir, outnum):
    """
    Runs download script with given script name.
    :param script_name: Name of download script to run (ssara, asfserial)
    :param customTemplateFile: Template file to download data from.
    :param slc_dir: SLC directory inside work directory.
    """
    if script_name not in {'ssara', 'asfserial'}:
        print('{} download not supported'.format(script_name))

    if script_name == 'ssara':
        try:
            with open('out_download_ssara.o', 'w') as f:
                with contextlib.redirect_stdout(f):
                    download_ssara_rsmas.main([customTemplateFile])
        except:
            with open('out_download_ssara.e', 'w') as g:
                with contextlib.redirect_stderr(g):
                    download_ssara_rsmas.main([customTemplateFile])

    elif script_name == 'asfserial':
        try:
            with open('out_download_asfserial.o', 'w') as f:
                with contextlib.redirect_stdout(f):
                    download_asfserial_rsmas.main([customTemplateFile])
        except:
            with open('out_download_asfserial.e', 'w') as g:
                with contextlib.redirect_stderr(g):
                    download_asfserial_rsmas.main([customTemplateFile])

    # print('Exit status from download_{0}_rsmas.py: {1}'.format(script_name, status))

###############################################################################


if __name__ == '__main__':
    main()
