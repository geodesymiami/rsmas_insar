#!/usr/bin/env python3
########################
# Author:  Falk Amelung
#######################

import os
import subprocess
import sys
import glob
import time
import shutil
import argparse
from minsar.objects.rsmas_logging import loglevel
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
from minsar import email_results

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

##############################################################################

def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='upload_dataserver')

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    job_file_name = 'upload_dataserver'
    job_name = job_file_name

    if inps.wall_time == 'None':
        #inps.wall_time = config[job_file_name]['walltime']
        inps.wall_time = config['ingest_insarmaps']['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)

    time.sleep(wait_seconds)

    os.chdir(inps.work_dir)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    DATA_SERVER = ''
    REMOTE_DIR = '/rsync_test/'

    DATA_SERVER = 'centos@129.114.104.223'
    REMOTE_DIR = '/data/HDF5EOS/'

    destination = 'rsync_test/'
    destination = DATA_SERVER + ':' + REMOTE_DIR
    project_name = putils.get_project_name(inps.custom_template_file)

    rsync_list = [
            '/mintpy/inputs',
            '/mintpy/pic',
            '/mintpy/*.he5'
            ]

    command = 'ssh ' + DATA_SERVER + ' mkdir ' + REMOTE_DIR + project_name
    print (command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
         raise Exception('ERROR in upload_dataserver.py')

    for pattern in rsync_list:
        command = 'rsync -avuz ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
        command = 'rsync -avuz -e ssh --chmod=755 ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
        command = 'rsync -avuz -e ssh --chmod=Du=rwx,Dg=rx,Do=rx ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
        print (command)
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            raise Exception('ERROR in upload_dataserver.py')

    return

    #if inps.email:
    #    email_results.main([inps.custom_template_file, '--insarmap'])

    return None


if __name__ == "__main__":
    main()
