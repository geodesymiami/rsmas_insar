#!/usr/bin/env python3
########################
# Author: Falk Amelung
#######################

import os
import sys
import argparse
from pathlib import Path
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

pathObj = PathFind()

###########################################################################################
def create_parser():
    parser = argparse.ArgumentParser(description='create jobfile to run save_hdf5.py for data in radar coordinates (*template is not used)\n')
    parser = putils.add_common_parser(parser)
    parser.add_argument(dest='processing_dir', default=None, help='miaplpy network_* directory with data for hdf5 file\n')
    parser.add_argument('--filter', dest='filter_par', type=float, default=0.7, help='Set the filtering parameter (default: 0.7)')
    parser.add_argument('--no-filter', dest='filter_par', action='store_const', const=None, help='Disable filtering')

    return parser

def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    print(inps)
    
    return inps

def get_network_prefix(network_dir):
    network_name = network_dir.split('network_')[1]
    if 'delaunay_4' in network_name:
        prefix='Del4'
    elif 'single_reference' in network_name:
        prefix='Sing'  
    elif 'sequential_1' in network_name:
        prefix='Seq1'  
    elif 'sequential_2' in network_name:
        prefix='Seq2' 
    elif 'sequential_3' in network_name:
        prefix='Seq3'   
    elif 'sequential_4' in network_name:
        prefix='Seq4'  
    elif 'sequential_5' in network_name:
        prefix='Seq5'  
    elif 'sequential_6' in network_name:
        prefix='Seq6' 
    elif 'sequential_8' in network_name:
        prefix='Seq8' 
    elif 'mini_stacks' in network_name:
        prefix='Mini'  
    else:
        raise Exception("USER ERROR: network name not recognized")
    
    return prefix


def main(iargs=None):

    inps = cmd_line_parse()
    inps.work_dir = os.getcwd()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    inps.num_data = 1
    inps.prefix = 'tops'   # in create_runfiles.py it was just there

    job_obj = JOB_SUBMIT(inps)

    path_obj = Path(inps.processing_dir)
    network_dir = path_obj.name

    prefix = get_network_prefix(network_dir)

    processing_dir = inps.work_dir +  '/' + inps.processing_dir
    processing_dir = processing_dir.rstrip(os.path.sep)
    
    job_name = 'save_hdfeos5_radar'
    job_file_name = job_name

    mask_thresh = 0.7
    cmd0 = f'cd {processing_dir}'
    cmd1 = f'spatial_filter.py temporalCoherence.h5 -f lowpass_gaussian -p {inps.filter_par} &'
    cmd2 = f'generate_mask.py temporalCoherence_lowpass_gaussian.h5 -m {mask_thresh} &'
    cmd3 = f'save_hdfeos5.py timeseries_*demErr.h5 --tc temporalCoherence.h5 --asc avgSpatialCoh.h5 -m ../maskPS.h5 -g inputs/geometryRadar.h5 -t smallbaselineApp.cfg --suffix {prefix}PS &'

    #cmd4 = f'save_hdfeos5.py timeseries_*demErr.h5 --tc temporalCoherence.h5 --asc avgSpatialCoh.h5 -m maskTempCoh.h5 -g inputs/geometryRadar.h5 -t smallbaselineApp.cfg --suffix {prefix}DS &'
    cmd4 = f'save_hdfeos5.py timeseries_*demErr.h5 --tc temporalCoherence.h5 --asc avgSpatialCoh.h5 -m maskTempCoh_lowpass_gaussian.h5  -g inputs/geometryRadar.h5 -t smallbaselineApp.cfg --suffix {prefix}DS &'

    cmd_source = 'source ' + os.path.dirname(os.path.abspath(__file__)) + '/utils/minsar_functions.bash'

    cmd3a=f'h5file=`ls *_??????_??????_???????_???????*_{prefix}PS.he5` ; add_ref_lalo_to_file $h5file'
    cmd4a=f'h5file=`ls *_??????_??????_???????_???????*_{prefix}DS.he5` ; add_ref_lalo_to_file $h5file'
    
    command = []
    command.append(cmd0)
    command.append(cmd1)
    command.append("wait")
    command.append(cmd2)
    command.append("wait")
    command.append(cmd3)
    command.append(cmd4)
    command.append("wait")
    command.append(cmd_source)
    command.append(cmd3a)
    command.append(cmd4a)
    command.append("wait")
    # Join the list into a string with linefeeds
    final_command_str = '\n'.join(command)
    final_command = [final_command_str]

    job_obj.submit_script(job_name, job_file_name, final_command, writeOnly='True')
    print('jobfile created: ',job_file_name + '.job')

    return None

###########################################################################################


if __name__ == "__main__":
    main()
