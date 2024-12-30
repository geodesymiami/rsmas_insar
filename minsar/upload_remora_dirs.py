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
from minsar.create_html import create_html

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

##############################################################################
EXAMPLE = """example:
    upload_data_products.py remora_*
"""

DESCRIPTION = (
    "Uploads remora directories to jetstream server"
)

def create_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE,
                 formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('data_dirs', nargs='+', metavar="DIRECTORY", help='upload one or more remora directories')

    return parser

def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    if inps.data_dirs:
        if 'remora' in inps.data_dirs[0]:
            inps.remora_flag = True
        else:
            raise Exception("USER ERROR: requires mintpy or miaplpy directory")

    print('inps: ',inps)
    return inps

###################################################
class Inps:
    def __init__(self, dir):
        self.dir = dir

##############################################################################

def main(iargs=None):

    inps = cmd_line_parse()

    inps.work_dir = os.getcwd()
    inps.project_name = os.path.relpath(inps.work_dir, os.getenv('SCRATCHDIR')).split(os.sep)[0]
    project_name = inps.project_name

    os.chdir(inps.work_dir)

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    REMOTEHOST_DATA = os.getenv('REMOTEHOST_DATA')
    REMOTEUSER = os.getenv('REMOTEUSER')
    REMOTE_DIR = '/data/HDF5EOS/'
    REMOTE_CONNECTION = REMOTEUSER + '@' + REMOTEHOST_DATA
    REMOTE_CONNECTION_DIR = REMOTE_CONNECTION + ':' + REMOTE_DIR

    scp_list = []
    for data_dir in inps.data_dirs:
        data_dir = data_dir.rstrip('/')
        scp_list.extend([ data_dir  ])


    print('################')
    print('Dirs to upload: ')
    for element in scp_list:
        print(element)
    print('################')
    import time
    time.sleep(2)

    for pattern in scp_list:
        if ( len(glob.glob(inps.work_dir + '/' + pattern)) >= 1 ):
            files=glob.glob(inps.work_dir + '/' + pattern)

            if os.path.isfile(files[0]):
               full_dir_name = os.path.dirname(files[0])
            elif os.path.isdir(files[0]):
               full_dir_name = os.path.dirname(files[0])
            else:
                raise Exception('ERROR finding directory in pattern in upload_data_products.py')

            dir_name = full_dir_name.removeprefix(inps.work_dir + '/run_files')
               
            # create remote directory
            print ('\nCreating remote directory:')
            command = 'ssh ' + REMOTE_CONNECTION + ' mkdir -p ' + REMOTE_DIR + project_name + '/run_files'
            print (command)

            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                raise Exception('ERROR creating remote directory in upload_data_products.py')

            # upload data
            print ('\nUploading data:')
            command = 'scp -r ' + inps.work_dir + '/' + pattern + ' ' + REMOTE_CONNECTION_DIR + '/' + project_name + '/' + pattern
            # command = 'scp -r ' + inps.work_dir + '/' + pattern + ' ' + REMOTE_CONNECTION_DIR + '/' + project_name + '/'.join(pattern.split('/')[0:-1])
            print (command)
            status = subprocess.Popen(command, shell=True).wait()
            if status is not 0:
                raise Exception('ERROR uploading using scp -r  in upload_data_products.py')
            
            ##########################################
            remote_url = 'http://' + REMOTEHOST_DATA + REMOTE_DIR + project_name + '/' + pattern + '/remora_summary.html'
            print('Data at:')
            print(remote_url)
            with open('remora_upload.log', 'a') as f:
                f.write(remote_url + "\n")

    # adjust permissions
    print ('\nAdjusting permissions:')
    command = 'ssh ' + REMOTEUSER + '@' +REMOTEHOST_DATA + ' chmod -R u=rwX,go=rX ' + REMOTE_DIR + project_name  + '/' + os.path.dirname(data_dir)
    print (command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR adjusting permissions in upload_data_products.py')

##########################################
    remote_url = 'http://' + REMOTEHOST_DATA + REMOTE_DIR + project_name + '/' + data_dir + '/remora_summary.html'
    print('Data at:')
    print(remote_url)
    with open('remora_upload.log', 'a') as f:
        f.write(remote_url + "\n")

    return None

if __name__ == "__main__":
    main()
