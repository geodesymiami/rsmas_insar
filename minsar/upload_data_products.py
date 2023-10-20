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

    parser.add_argument('custom_template_file', nargs='?', default=None, help='custom template with option settings.\n')

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
    parser.add_argument('--dir', dest='data_dirs', nargs='+', default=False,  metavar="DIRECTORY",
                         help='upload specific mintpy/miaplpy directory')
    parser.add_argument('--all',
                         dest='all_flag',
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

    if inps.data_dirs:
        if 'mintpy' in inps.data_dirs[0]:
            inps.mintpy_flag = True
        if 'miaplpy' in inps.data_dirs[0]:
            inps.miaplpy_flag = True

    if not inps.data_dirs:
        if inps.mintpy_flag:
            inps.data_dirs = ['mintpy']
        if inps.miaplpy_flag:
            inps.data_dirs = ['miaplpy']

    #if inps.all_flag:
    #    if inps.mintpy_flag:
    #        inps.mintpy_all_flag = True
    #    if inps.miaplpy_flag:
    #        inps.miaplpy_all_flag = True

    print(inps)
    return inps

##############################################################################

def main(iargs=None):

    inps = cmd_line_parse()

    if inps.custom_template_file:
       inps.project_name = putils.get_project_name(custom_template_file=inps.custom_template_file)
       inps.work_dir = putils.get_work_directory(None, inps.project_name)
    else:
       if len(inps.data_dirs[0].rstrip('/').split("/")) == 1:
          inps.work_dir = os.getcwd()
       else:
          # Allows for upload_data_products.py --dir unittestGalapagosSenDT128/miaplpy --all   (log entry not right)
          inps.work_dir = os.getcwd() + '/' + os.path.dirname(inps.data_dir)
          inps.data_dir = inps.data_dirs.split("/")[1]
       inps.project_name = os.path.basename(inps.work_dir)

    project_name = inps.project_name

    if inps.image_products_flag:
       inps.mintpy_flag = False

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

    for data_dir in inps.data_dirs:
        data_dir = data_dir.rstrip('/')
        if inps.mintpy_flag:
            scp_list.extend([
            '/'+ data_dir +'/*.he5',
            '/'+ data_dir +'/pic',
            '/'+ data_dir +'/inputs'
            ])

        if inps.all_flag:
            scp_list = [ '/mintpy/*' ]

        if inps.miaplpy_flag:
            dir_list = glob.glob(data_dir + '/network_*')
            for network_dir in dir_list:
             scp_list.extend([
                '/'+ network_dir +'/*.he5',
                '/'+ network_dir +'/demErr.h5',
                '/'+ network_dir +'/pic' 
                ])
                #'/'+ network_dir +'/inputs'

             if inps.all_flag:
                 scp_list.extend([
                 '/'+ network_dir +'/*.he5',
                 '/'+ network_dir +'/avgSpatialCoh.h5',
                 '/'+ network_dir +'/demErr.h5',
                 '/'+ network_dir +'/numInvIfgram.h5',
                 '/'+ network_dir +'/timeseries.h5',
                 '/'+ network_dir +'/velocity.h5',
                 '/'+ network_dir +'/*.cfg',
                 '/'+ network_dir +'/*.txt',
                 '/'+ network_dir +'/inputs/geometryRadar.h5',
                 '/'+ network_dir +'/inputs/ifgramStack.h5',
                 '/'+ network_dir +'/inputs/smallbaselineApp.cfg',
                 '/'+ network_dir +'/inputs/*template',
                 '/'+ network_dir +'/geo', 
                 '/'+ network_dir +'/pic' 
                 ])
                 #'/'+ network_dir +'../inputs/*',
                 #'/'+ network_dir +'/inputs'

            scp_list.extend([
            '/'+ os.path.basename(data_dir) +'/inputs/slcStack.h5',
            '/'+ os.path.basename(data_dir) +'/inputs/geometryRadar.h5',
            '/'+ os.path.basename(data_dir) +'/maskPS.h5',
            '/'+ os.path.basename(data_dir) +'/miaplpyApp.cfg',
            '/'+ os.path.basename(data_dir) +'/inputs/baselines', 
            '/'+ os.path.basename(data_dir) +'/inputs/*.template', 
            '/'+ os.path.basename(data_dir) +'/inverted/tempCoh_average*', 
            '/'+ os.path.basename(data_dir) +'/inverted/phase_series.h5', 
            '/'+ os.path.basename(data_dir) +'/inverted/tempCoh_full*' 
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
