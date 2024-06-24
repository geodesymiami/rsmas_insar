#!/usr/bin/env python3
########################
# Author: Falk Amelung
#######################

import os
import sys
import glob
import argparse
from pathlib import Path
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

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
    parser.add_argument('--dataset', dest='dataset', choices=['PS', 'DS', 'PSDS', 'geo', 'all'], default='PS', help='Plot data as image or scatter (default: %(default)s).')
    parser.add_argument("--queue", dest="queue", metavar="QUEUE", default=os.getenv('QUEUENAME'), help="Name of queue to submit job to")
    parser.add_argument('--walltime', dest='wall_time', metavar="WALLTIME (HH:MM)", default='1:00', help='job walltime (default=1:00)')
   
    inps = parser.parse_args()
    return inps

def main(iargs=None):
    
    inps = create_parser()
    inps.work_dir = os.getcwd()

    input_arguments = sys.argv[1::]
    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    inps.num_data = 1
    job_obj = JOB_SUBMIT(inps)

    files = glob.glob(inps.work_dir + '/' + inps.data_dir[0] + '/*.he5')

    file_DS = None
    file_PS = None

    for file in files:
        if 'DS' in file:
            file_DS = file
        elif 'PS' in file:
            file_PS = file
        else:
            file_geo = file
    
    job_name = f"insarmaps_{inps.dataset}"
    job_file_name = job_name

    files = []
    if inps.dataset == "geo":
        files.append(file_geo)
    if inps.dataset == "PS":
        files.append(file_PS)
    if inps.dataset == "DS":
        files.append(file_DS)
    if inps.dataset == "PSDS":
        files.append(file_PS)
        files.append(file_DS)
    if inps.dataset == "all":
        files.append(file_geo)
        files.append(file_PS)
        files.append(file_DS)

    command = []
    i = 0
    for file in files:
        command.append( f'rm -r {inps.data_dir[0]}/JSON_{i}\n' )
        command.append( f'hdfeos5_2json_mbtiles.py {file} {inps.work_dir}/{inps.data_dir[0]}/JSON_{i} --num-workers 8\n' )
        i+=1
    
    command.append('wait\n\n')
    i = 0
    for file in files:
        path_obj = Path(file)
        mbtiles_file = f"{path_obj.parent}/JSON_{i}/{path_obj.name}"
        mbtiles_file = mbtiles_file.replace('he5','mbtiles')
        command.append( f'json_mbtiles2insarmaps.py --num-workers 8 -u {password.insaruser} -p {password.insarpass} --host insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder {inps.work_dir}/{inps.data_dir[0]}/JSON_{i} --mbtiles_file {mbtiles_file}\n' )
        i+=1
    
    command.append('wait\n\n')
    str = [f'cat >> insarmaps.log<<EOF\n']
    str.append(f"\n{inps.data_dir[0]}:\n")
    for file in files:
        base_name = os.path.basename(file)
        name_without_extension = os.path.splitext(base_name)[0]
        str.append(f"https://insarmaps.miami.edu/start/25.78/-80.3/11.0?flyToDatasetCenter=true&startDataset={name_without_extension}")

    str.append( 'EOF' ) 
    command.append( "".join(str) )
    
    job_obj.submit_script(job_name, job_file_name, command, writeOnly='True')
    print('jobfile created: ',job_file_name + '.job')

    return None

###########################################################################################

if __name__ == "__main__":
    main()

