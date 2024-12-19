#!/usr/bin/env python3
########################
# Author: Falk Amelung
#######################

import os
import sys
import glob
import argparse
import h5py
import math
from pathlib import Path
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar.objects.auto_defaults import queue_config_file, supported_platforms

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

REMOTEHOST_INSARMAPS1 = os.getenv('REMOTEHOST_INSARMAPS1')
REMOTEHOST_INSARMAPS2 = os.getenv('REMOTEHOST_INSARMAPS2')
REMOTEHOST_INSARMAPS3 = os.getenv('REMOTEHOST_INSARMAPS3')

pathObj = PathFind()
############################################################
EXAMPLE = """example:
        create_insarmaps_jobfile.py miaplpy/network_single_reference --dataset geo
        create_insarmaps_jobfile.py miaplpy/network_single_reference --dataset PSDS
        create_insarmaps_jobfile.py miaplpy/network_single_reference --dataset PS --queue skx --walltime 0:45
"""
###########################################################################################
def create_parser():
    synopsis = 'Create jobfile for ingestion into insarmaps'
    epilog = EXAMPLE
    parser = argparse.ArgumentParser(description=synopsis, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('data_dir', nargs=1, help='Directory with hdf5eos file.\n')
    parser.add_argument('--dataset', dest='dataset', choices=['PS', 'DS', 'PSDS', 'filtDS','DSfiltDS','filt*DS','DSfilt*DS','geo','all'], default='geo', help='Dataset to upload (default: %(default)).')
    parser.add_argument("--queue", dest="queue", metavar="QUEUE", default=os.getenv('QUEUENAME'), help="Name of queue to submit job to")
    parser.add_argument('--walltime', dest='wall_time', metavar="WALLTIME (HH:MM)", default='1:00', help='job walltime (default=1:00)')
   
    inps = parser.parse_args()
    return inps

def get_file_length(file_path):
    file_length = os.path.getsize(file_path)
    print (file_path + ':', file_length)
    return file_length
    
def get_num_workers_hdf5eos(files, number_of_cores_per_node):

    # Define thresholds in GB and corresponding percentages
    thresholds = [1, 5, 10, 20]  # in GB
    percentage_of_cores = [40, 20, 10, 2]  # corresponding percentages in %

    file_lengths = [get_file_length(file[0]) for file in files]

    max_length = max(file_lengths)
    max_length_gb = max_length / (1024**3)

    for i, threshold in enumerate(thresholds):
        if max_length_gb < threshold:
            percentage = percentage_of_cores[i]
            break
   
    num_workers = math.ceil(number_of_cores_per_node * percentage / 100)
    return num_workers

def get_num_workers_json_mbtiles(files, number_of_cores_per_node):
    '''Distribute 98% of the available cores on the number on the files to be uploaded'''
    num_files = len(files)
    num_cores = int(0.98 * number_of_cores_per_node / 2)     #  change to 1 for uploading to one insarmaps server
    num_workers = int(num_cores / num_files)
    return num_workers
        
def main(iargs=None):
    
    inps = create_parser()
    inps.work_dir = os.getcwd()

    input_arguments = sys.argv[1::]
    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    all_files = glob.glob(inps.work_dir + '/' + inps.data_dir[0] + '/*.he5')

    file_geo = [file for file in all_files if 'DS'  not in file and 'PS' not in file]
    file_PS = [file for file in all_files if 'PS'  in file]
    file_DS = [file for file in all_files if 'DS'  in file and 'filt' not in file]
    file_filtDS = [file for file in all_files if 'DS'  in file and 'filt' in file]
        
    job_name = f"insarmaps"
    job_file_name = job_name
        
    with h5py.File(file_geo[0], 'r') as f:
        ref_lat = float(f.attrs['REF_LAT'])
        ref_lon = float(f.attrs['REF_LON'])

    files = []
    suffixes = []
    if inps.dataset == "geo":
        files.append(file_geo)
        suffixes.append("")
    if inps.dataset == "PS":
        files.append(file_PS)
        suffixes.append("_PS")
    if inps.dataset == "DS":
        files.append(file_DS)
        suffixes.append("_DS")
    if inps.dataset == "filt*DS" or inps.dataset == "filtDS"  :
        files.append(file_filtDS)
        suffixes.append("_filtDS")
    if inps.dataset == "DSfilt*DS" or inps.dataset == "DSfiltDS":
        files.append(file_DS)
        files.append(file_filtDS)
        suffixes.append("_DS")
        suffixes.append("_filtDS")
    if inps.dataset == "PSDS" or inps.dataset == "DSPS":
        files.append(file_PS)
        files.append(file_DS)
        suffixes.append("_PS")
        suffixes.append("_DS")
    if inps.dataset == "all":
        files.append(file_geo)
        files.append(file_PS)
        files.append(file_DS)
        suffixes.append("")
        suffixes.append("_PS")
        suffixes.append("_DS")

    inps.num_data = 1
    job_obj = JOB_SUBMIT(inps)

    number_of_cores_per_node = job_obj.number_of_cores_per_node
    num_workers_hdf5eos = get_num_workers_hdf5eos(files, number_of_cores_per_node)
    num_workers_json_mbtiles = get_num_workers_json_mbtiles(files, number_of_cores_per_node)

    command = []
    for file, suffix in zip(files, suffixes):
        command.append( f'rm -rf {inps.data_dir[0]}/JSON{suffix}' )
        command.append( f'hdfeos5_2json_mbtiles.py {file[0]} {inps.work_dir}/{inps.data_dir[0]}/JSON{suffix} --num-workers {num_workers_hdf5eos}' )
    
    command.append('wait\n')
    for file, suffix in zip(files, suffixes):
        path_obj = Path(file[0])
        mbtiles_file = f"{path_obj.parent}/JSON{suffix}/{path_obj.name}"
        mbtiles_file = mbtiles_file.replace('he5','mbtiles')
        command.append( f'json_mbtiles2insarmaps.py --num-workers {num_workers_json_mbtiles} -u {password.docker_insaruser} -p {password.docker_insarpass} --host {REMOTEHOST_INSARMAPS1} -P {password.docker_databasepass} -U {password.docker_databaseuser} --json_folder {inps.work_dir}/{inps.data_dir[0]}/JSON{suffix} --mbtiles_file {mbtiles_file} &' )
        command.append( f'json_mbtiles2insarmaps.py --num-workers {num_workers_json_mbtiles} -u {password.docker_insaruser} -p {password.docker_insarpass} --host {REMOTEHOST_INSARMAPS2} -P {password.docker_databasepass} -U {password.docker_databaseuser} --json_folder {inps.work_dir}/{inps.data_dir[0]}/JSON{suffix} --mbtiles_file {mbtiles_file} &' )
        #command.append( f'json_mbtiles2insarmaps.py --num-workers {num_workers_json_mbtiles} -u {password.docker_insaruser} -p {password.docker_insarpass} --host {REMOTEHOST_INSARMAPS3} -P {password.docker_databasepass} -U {password.docker_databaseuser} --json_folder {inps.work_dir}/{inps.data_dir[0]}/JSON{suffix} --mbtiles_file {mbtiles_file} &' )
    
    command.append('wait\n')
    str1 = [f'cat >> insarmaps.log<<EOF']
    str2 = [f'cat > {inps.work_dir}/{inps.data_dir[0]}/pic/insarmaps.log<<EOF']

    for file in files:
        base_name = os.path.basename(file[0])
        name_without_extension = os.path.splitext(base_name)[0]
        str1.append(f"https://{REMOTEHOST_INSARMAPS1}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")
        str1.append(f"http://{REMOTEHOST_INSARMAPS2}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")
        #str1.append(f"http://{REMOTEHOST_INSARMAPS3}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")
        str2.append(f"https://{REMOTEHOST_INSARMAPS1}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")
        str2.append(f"http://{REMOTEHOST_INSARMAPS2}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")
        #str2.append(f"http://{REMOTEHOST_INSARMAPS3}/start/{ref_lat:.1f}/{ref_lon:.1f}/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")

    str1.append( 'EOF' ) 
    str2.append( 'EOF' ) 

    command.append( '\n'.join(str1) )
    command.append( '\n'.join(str2) )
    final_command =[ '\n'.join(command) ]
    
    job_obj.submit_script(job_name, job_file_name, final_command, writeOnly='True')
    print('jobfile created: ',job_file_name + '.job')

    return None

###########################################################################################

if __name__ == "__main__":
    main()

