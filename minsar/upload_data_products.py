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

    inps = putils.cmd_line_parse(iargs, script='upload_data_products')

    if inps.image_products_flag:
       inps.mintpy_products_flag = False
    
    os.chdir(inps.work_dir)

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    # get DATA_SERVER and return if it does not exist

    DATA_SERVER = 'centos@129.114.104.223'

    #try:
    #    DATA_SERVER = os.getenv('DATA_SERVER')
    #except:
    #    return

    project_name = putils.get_project_name(inps.custom_template_file)

    if inps.mintpy_products_flag or inps.minopy_products_flag:

        REMOTE_DIR = '/data/HDF5EOS/'
        destination = DATA_SERVER + ':' + REMOTE_DIR

        scp_list = []
        if os.path.exists(inps.work_dir + '/mintpy'):
            scp_list.extend([
                '/mintpy/pic',
                '/mintpy/*.he5',
                '/mintpy/inputs',
                '/remora_*'
                ])
        if os.path.exists(inps.work_dir + '/minopy'):
            scp_list.extend([
                '/minopy/pic',
                '/minopy/*.he5',
                '/minopy/inputs',
                ])

        if os.path.exists(inps.work_dir + '/minopy_sequential'):
            scp_list.extend([
                '/minopy_sequential/pic',
                '/minopy_sequential/*.he5',
                '/minopy_sequential/inputs',
                ])
        
        if os.path.exists(inps.work_dir + '/minopy_single_reference'):
            scp_list.extend([
                '/minopy_single_reference/pic',
                '/minopy_single_reference/*.he5',
                '/minopy_single_reference/inputs',
                ])
        
        if inps.mintpy_products_all_flag:
            scp_list = [ '/mintpy' ]

        if os.path.exists(inps.work_dir + '/mintpy'):
            command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name + '/mintpy'
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                 raise Exception('ERROR in upload_data_products.py')
        if os.path.exists(inps.work_dir + '/minopy'):
            command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name + '/minopy'
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                 raise Exception('ERROR in upload_data_products.py')
        if os.path.exists(inps.work_dir + '/minopy_sequential'):
            command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name + '/minopy_sequential'
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                 raise Exception('ERROR in upload_data_products.py')
        if os.path.exists(inps.work_dir + '/minopy_single_reference'):
            command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name + '/minopy_single_reference'
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                 raise Exception('ERROR in upload_data_products.py')



        for pattern in scp_list:
            if ( len(glob.glob(inps.work_dir + '/' + pattern)) >= 1 ):
                command = 'scp -r ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
                print (command)
                status = subprocess.Popen(command, shell=True).wait()
                if status is not 0:
                    raise Exception('ERROR in upload_data_products.py')

                print ('\nAdjusting permissions:')
                command = 'ssh ' + DATA_SERVER + ' chmod -R u=rwX,go=rX ' + REMOTE_DIR + project_name 
                print (command)
                status = subprocess.Popen(command, shell=True).wait()
                if status is not 0:
                    raise Exception('ERROR in upload_data_products.py')

    if inps.image_products_flag:
        REMOTE_DIR = '/data/image_products/'
        destination = DATA_SERVER + ':' + REMOTE_DIR

        rsync_list = [
                '/image_products/*',
                ]

        command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name
        print (command)
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
             raise Exception('ERROR in upload_data_products.py')


        for pattern in rsync_list:
            command = 'rsync -avuz -e ssh --chmod=Du=rwx,Dg=rx,Do=rx,Fu=rw,Fg=r,Fo=r ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                raise Exception('ERROR in upload_data_products.py')

        return None

    return None

if __name__ == "__main__":
    main()
