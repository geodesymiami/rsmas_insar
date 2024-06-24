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
    upload_data_products.py --dir mintppy
    upload_data_products.py --dir miaplpy
    upload_data_products.py --dir miaplpy/network_single_reference
"""

DESCRIPTION = (
    "Uploads mintpy and miaplpy data products to jetstream server"
)

def create_parser():
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE,
                 formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--dir', dest='data_dirs', nargs='+', default=False,  metavar="DIRECTORY",
                         help='upload specific mintpy/miaplpy directory')
    parser.add_argument('--geo', dest='geo_flag', action='store_true', default=False, help='uploads geo  directory')
    parser.add_argument('--slcStack', dest='slcStack_flag', action='store_true', default=False, help='uploads miaplpy*/inputs directory')
    parser.add_argument('--all', dest='all_flag', action='store_true', default=False, help='uploads full directory')
    #parser.add_argument('--triplets', dest='triplets_flag', action='store_true', default=False, help='uploads numTriNonzeroIntAmbiguity.h5')
    parser.add_argument('--triplets', dest='triplets_flag', action='store_true', default=True, help='uploads numTriNonzeroIntAmbiguity.h5')

    return parser

def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    inps.mintpy_flag = False
    inps.miaplpy_flag = False
    if inps.data_dirs:
        if 'mintpy' in inps.data_dirs[0]:
            inps.mintpy_flag = True
        elif 'miaplpy' in inps.data_dirs[0]:
            inps.miaplpy_flag = True
        else:
            raise Exception("USER ERROR: requires mintpy or miaplpy directory")

    print('inps: ',inps)
    return inps

###################################################
class Inps:
    def __init__(self, dir):
        self.dir = dir

def create_html_if_needed(dir):
    if not os.path.isfile(dir + '/index.html'):
        # Create an instance of Inps with the directory
        inps = Inps(dir)
        create_html(inps)
   
##############################################################################

def main(iargs=None):

    inps = cmd_line_parse()

    inps.work_dir = os.getcwd()
    inps.project_name = os.path.basename(inps.work_dir)

    project_name = inps.project_name

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
            if os.path.isdir(data_dir + '/pic'):
               create_html_if_needed(data_dir + '/pic')
            scp_list.extend([
            '/'+ data_dir +'/*.he5',
            '/'+ data_dir +'/timeseries*demErr.h5',
            '/'+ data_dir +'/pic',
            '/'+ data_dir +'/inputs/geometryRadar.h5',
            '/'+ data_dir +'/inputs/smallbaselineApp.cfg',
            '/'+ data_dir +'/inputs/*.template',
            '/'+ data_dir +'/geo/geo_velocity.h5'
            ])
            if inps.geo_flag:
               scp_list.extend([
               '/'+ data_dir +'/geo/geo_*.h5'
               ])
            #if inps.geo_flag:
            #   scp_list.extend([
            #   '/'+ data_dir +'/geo/geo_avgSpatialCoh.h5',
            #   '/'+ data_dir +'/geo/geo_geometryRadar.h5',
            #   '/'+ data_dir +'/geo/geo_maskTempCoh.h5',
            #   '/'+ data_dir +'/geo/geo_temporalCoherence.h5',
            #   '/'+ data_dir +'/geo/geo_timeseries_demErr.h5'
            #   #'/'+ data_dir +'/geo/geo_velocity.h5'             # already included earlier
            #   ])
            if inps.triplets_flag:
                   scp_list.extend([
                   '/'+ data_dir +'/numTriNonzeroIntAmbiguity.h5',
                   ])

        if inps.miaplpy_flag:
            if 'network_' in data_dir:
               dir_list = [ data_dir ]
            else:
               dir_list = glob.glob(data_dir + '/network_*')

            # loop over network_* folder(s)
            for network_dir in dir_list:
                create_html_if_needed(network_dir + '/pic')
                scp_list.extend([
                '/'+ network_dir +'/*.he5',
                '/'+ network_dir +'/demErr.h5',
                '/'+ network_dir +'/velocity.h5',
                '/'+ network_dir +'/temporalCoherence.h5',
                '/'+ network_dir +'/avgSpatialCoh.h5',
                '/'+ network_dir +'/maskTempCoh.h5',
                '/'+ network_dir +'/numTriNonzeroIntAmbiguity.h5',
                '/'+ network_dir +'/../maskPS.h5',
                '/'+ network_dir +'/pic',
                '/'+ network_dir +'/inputs/geometryRadar.h5',
                '/'+ network_dir +'/geo/geo_velocity.h5'             # already included earlier
                ])
                if inps.geo_flag:
                   scp_list.extend([
                   '/'+ data_dir +'/geo/geo_*.h5'
                   ])
                #if inps.geo_flag:
                #   scp_list.extend([
                #   '/'+ network_dir +'/geo/geo_avgSpatialCoh.h5',
                #   '/'+ network_dir +'/geo/geo_geometryRadar.h5',
                #   '/'+ network_dir +'/geo/geo_maskTempCoh.h5',
                #   '/'+ network_dir +'/geo/geo_temporalCoherence.h5',
                #   '/'+ network_dir +'/geo/geo_timeseries_*demErr.h5'
                #   #'/'+ network_dir +'/geo/geo_velocity.h5'             # already included earlier
                #   ])
                if inps.triplets_flag:
                   scp_list.extend([
                   '/'+ network_dir +'/numTriNonzeroIntAmbiguity.h5',
                   ])
                if inps.all_flag:
                    scp_list.extend([
                    '/'+ network_dir +'/numInvIfgram.h5',
                    '/'+ network_dir +'/timeseries_demErr.h5',
                    '/'+ network_dir +'/inputs/ifgramStack.h5',
                    '/'+ network_dir +'/inputs/smallbaselineApp.cfg',
                    '/'+ network_dir +'/inputs/*template',
                    '/'+ network_dir +'/*.cfg',
                    '/'+ network_dir +'/*.txt',
                    '/'+ network_dir +'/geo', 
                    ])

            # After completion of network_* loops
            scp_list.extend([
            '/'+ os.path.dirname(data_dir) +'/maskPS.h5',
            '/'+ os.path.dirname(data_dir) +'/miaplpyApp.cfg',
            '/'+ os.path.dirname(data_dir) +'/inputs/geometryRadar.h5',
            '/'+ os.path.dirname(data_dir) +'/inputs/baselines', 
            '/'+ os.path.dirname(data_dir) +'/inputs/*.template', 
            '/'+ os.path.dirname(data_dir) +'/inverted/tempCoh_average*', 
            #'/'+ os.path.dirname(data_dir) +'/inputs/slcStack.h5',
            #'/'+ os.path.dirname(data_dir) +'/inverted/phase_series.h5', 
            '/'+ os.path.dirname(data_dir) +'/inverted/tempCoh_full*' 
            ])
            if inps.slcStack_flag:
                scp_list.extend([
                '/'+ os.path.dirname(data_dir) +'/inputs/slcStack.h5'
                ])

    print('################')
    print('Data to upload: ')
    for element in scp_list:
        print(element)
    print('################')

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
            #print ('\nAdjusting permissions:')
            #command = 'ssh ' + DATA_SERVER + ' chmod -R u=rwX,go=rX ' + REMOTE_DIR + project_name  + pattern
            #print (command)
            #status = subprocess.Popen(command, shell=True).wait()
            #if status is not 0:
            #    raise Exception('ERROR adjusting permissions in upload_data_products.py')

    # adjust permissions
    print ('\nAdjusting permissions:')
    command = 'ssh ' + DATA_SERVER + ' chmod -R u=rwX,go=rX ' + REMOTE_DIR + project_name  + '/' + os.path.dirname(data_dir)
    print (command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR adjusting permissions in upload_data_products.py')

##########################################
    remote_url = 'http://' + DATA_SERVER.split('@')[1] + REMOTE_DIR + '/' + project_name + '/' + data_dir + '/pic'
    print('Data at:\n',remote_url)
    with open('upload.log', 'a') as f:
        f.write(remote_url + "\n")
##########################################

        #for pattern in rsync_list:
        #    command = 'rsync -avuz -e ssh --chmod=Du=rwx,Dg=rx,Do=rx,Fu=rw,Fg=r,Fo=r ' + inps.work_dir + pattern + ' ' + destination + project_name + '/'.join(pattern.split('/')[0:-1])
        #    print (command)
        #    status = subprocess.Popen(command, shell=True).wait()
        #    if status is not 0:
        #        raise Exception('ERROR in upload_data_products.py')
        #
        #    return None

    return None

if __name__ == "__main__":
    main()
