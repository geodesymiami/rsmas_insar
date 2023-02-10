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
#from minsar import email_results

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

##############################################################################
def create_parser():
    parser = argparse.ArgumentParser(description='Convert MintPy timeseries product into HDF-EOS5 format\n' +
                                     '  https://earthdata.nasa.gov/esdis/eso/standards-and-references/hdf-eos5\n' +
                                     '  https://mintpy.readthedocs.io/en/latest/hdfeos5/')
#                                     formatter_class=argparse.RawDescriptionHelpFormatter,
#                                     epilog=TEMPALTE+'\n'+EXAMPLE)

    parser.add_argument('custom_template_file', nargs='?', help='custom template with option settings.\n')

    parser.add_argument('--mintpy',
                         dest='mintpy_flag',
                         action='store_true',
                         default=False,
                         help='uploads mintpy data products to data portal')
    parser.add_argument('--miaplpy',
                         dest='miaplpy_flag',
                         action='store_true',
                         default=False,
                         help='uploads miaplpy/*_network data products to data portal')
    parser.add_argument('--dir', dest='data_dir',  metavar="DIRECTORY",
                         help='upload specific mintpy/miaplpy directory')
    parser.add_argument('--all',
                         dest='mintpy_all_flag',
                         action='store_true',
                         default=False,
                         help='uploads full mintpy dir')
    parser.add_argument('--imageProducts',
                         dest='image_products_flag',
                         action='store_true',
                         default=False,
                         help='uploads image data products to data portal')
    return parser


def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    inps.miaplpy_all_flag = inps.mintpy_all_flag

    return inps

##############################################################################

def main(iargs=None):

    inps = cmd_line_parse()

    if inps.custom_template_file:
       inps.project_name = putils.get_project_name(custom_template_file=inps.custom_template_file)
       inps.work_dir = putils.get_work_directory(None, inps.project_name)
    else:
       inps.work_dir = os.getcwd()
       inps.project_name = os.path.basename(inps.work_dir)
    project_name = inps.project_name

    if inps.image_products_flag:
       inps.mintpy_flag = False

    if inps.data_dir:
        inps.mintpy_flag = False
        inps.miaplpy_flag = False

    os.chdir(inps.work_dir)

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    # get DATA_SERVER and return if it does not exist
    #try:
    #    DATA_SERVER = os.getenv('DATA_SERVER')
    #except:
    #    return

    DATA_SERVER = 'exouser@149.165.154.65'
    REMOTE_DIR = '/data/HDF5EOS/'
    destination = DATA_SERVER + ':' + REMOTE_DIR

    scp_list = []

    if inps.mintpy_flag or inps.miaplpy_flag or inps.data_dir:

        if inps.mintpy_flag:
            data_dir = 'mintpy'
            if os.path.exists(inps.work_dir + '/mintpy'):
                scp_list.extend([
                    '/'+ data_dir +'/*.he5',
                    '/'+ data_dir +'/pic',
                    '/'+ data_dir +'/inputs'
                    ])

            if inps.mintpy_all_flag:
                scp_list = [ '/mintpy' ]

        if inps.miaplpy_flag:
            dir_list = glob.glob('miaplpy/network_*')
            for data_dir in dir_list:
                if os.path.exists(inps.work_dir +'/'+ data_dir):
                    scp_list.extend([
                        '/'+ data_dir +'/*.he5',
                        '/'+ data_dir +'/demErr.h5',
                        '/'+ data_dir +'/pic' 
                        ])
                        #'/'+ data_dir +'/inputs'

        if inps.data_dir:
                dir_list = glob.glob(inps.data_dir + '/network_*')
                for data_dir in dir_list:
                     #if os.path.exists(inps.work_dir +'/'+ data_dir):
                     if not inps.miaplpy_all_flag:
                         scp_list.extend([
                             '/'+ data_dir +'/*.he5',
                             '/'+ data_dir +'/demErr.h5',
                             '/'+ data_dir +'/pic' 
                             ])
                     else:
                         scp_list.extend([
                             '/'+ data_dir +'/*.he5',
                             '/'+ data_dir +'/*.h5',
                             '/'+ data_dir +'/*.cfg',
                             '/'+ data_dir +'/*.txt',
                             '/'+ data_dir +'/inputs/geometryRadar.h5',
                             '/'+ data_dir +'/inputs/smallbaselineApp.cfg',
                             '/'+ data_dir +'/inputs/*template',
                             '/'+ data_dir +'/pic' 
                             ])
                             #'/'+ data_dir +'../inputs/*',
                             #'/'+ data_dir +'/inputs'

                scp_list.extend([
                    '/'+ os.path.dirname(data_dir) +'/inputs/slcStack.h5',
                    '/'+ os.path.dirname(data_dir) +'/inputs/geometryRadar.h5',
                    '/'+ os.path.dirname(data_dir) +'/maskPS.h5',
                    '/'+ os.path.dirname(data_dir) +'/inputs/baselines' 
                    ])

        for pattern in scp_list:
            if ( len(glob.glob(inps.work_dir + '/' + pattern)) >= 1 ):
                #files=glob.glob(inps.work_dir + '/' + pattern)
                files=glob.glob(inps.work_dir + pattern)

                if os.path.isfile(files[0]):
                   full_dir_name = os.path.dirname(files[0])
                elif os.path.isdir(files[0]):
                   full_dir_name = os.path.dirname(files[0])
                else:
                    raise Exception('ERROR finding directory in pattern in upload_data_products.py')

                dir_name = full_dir_name.removeprefix(inps.work_dir +'/')
                   
                # create remote directory
                print ('\nCreating remote directory:',dir_name)
                command = 'ssh ' + DATA_SERVER + ' mkdir -p ' + REMOTE_DIR + project_name + '/' + dir_name
                print (command)
                status = subprocess.Popen(command, shell=True).wait()
                if status is not 0:
                    raise Exception('ERROR creating remote directory in upload_data_products.py')

                # upload data
                print ('\nUploading data:')
                command = 'scp -r ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
                print (command)
                status = subprocess.Popen(command, shell=True).wait()
                if status is not 0:
                    raise Exception('ERROR uploading using scp -r  in upload_data_products.py')

                # adjust permissions
                print ('\nAdjusting permissions:')
                command = 'ssh ' + DATA_SERVER + ' chmod -R u=rwX,go=rX ' + REMOTE_DIR + project_name  + pattern
                print (command)
                status = subprocess.Popen(command, shell=True).wait()
                if status is not 0:
                    raise Exception('ERROR adjusting permissions in upload_data_products.py')

##########################################

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
