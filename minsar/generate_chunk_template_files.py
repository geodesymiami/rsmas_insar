#! /usr/bin/env python3
"""
   Author: Falk Amelung, Sara Mirzaee
"""
###############################################################################

import os
import sys
import glob
import subprocess
import h5py
import math
import shutil

from mintpy.utils import readfile
import minsar.utils.process_utilities as putils
from minsar.objects.auto_defaults import PathFind
from minsar.objects import message_rsmas
from minsar.objects.dataset_template import Template

pathObj = PathFind()


###########################################################################################


def main(iargs=None):
    """ create template files for chunk processing """

    inps = putils.cmd_line_parse(iargs, script='generate_chunk_template_files')

    os.chdir(inps.work_dir)

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    run_generate_chunk_template_files(inps)

    return

###################################################


def  run_generate_chunk_template_files(inps):
    """ create e*chunk*.template files """

    project_name = putils.get_project_name(inps.custom_template_file)

    location_name, sat_direction, sat_track = putils.split_project_name(project_name)

    chunk_templates_dir = inps.work_dir + '/chunk_templates'
    os.makedirs(chunk_templates_dir, exist_ok=True)
 
    commands_file = inps.work_dir + '/minsar_commands.txt'
    f = open(commands_file, "w")

    if inps.download_flag == True:
        minsarApp_option = '--start download'
    else:
        minsarApp_option = '--start dem'

    prefix = 'tops'
    bbox_list = inps.template[prefix + 'Stack.boundingBox'].split(' ')

    bbox_list[0] = bbox_list[0].replace("\'", '')   # this does ["'-8.75", '-7.8', '115.0', "115.7'"] (needed for run_operations.py, run_operations
    bbox_list[1] = bbox_list[1].replace("\'", '')   # -->       ['-8.75',  '-7.8', '115.0', '115.7']  (should be modified so that this is not needed)
    bbox_list[2] = bbox_list[2].replace("\'", '')
    bbox_list[3] = bbox_list[3].replace("\'", '')

    tmp_min_lat = float(bbox_list[0]) 
    tmp_max_lat = float(bbox_list[1])
 
    min_lat = math.ceil(tmp_min_lat)
    max_lat = math.floor(tmp_max_lat)
  
    lat = min_lat
    while lat < max_lat:
        tmp_min_lat = lat
        tmp_max_lat = lat + inps.lat_step

        chunk_name =[ location_name + 'Chunk' +  str(int(lat)) + sat_direction + sat_track ] 
        chunk_template_file = chunk_templates_dir + '/' + chunk_name[0] + '.template'
        shutil.copy(inps.custom_template_file, chunk_template_file)

        chunk_bbox_list = bbox_list
        chunk_bbox_list[0] = str(float(tmp_min_lat-inps.lat_margin))
        chunk_bbox_list[1] = str(float(tmp_max_lat+inps.lat_margin))
        print(chunk_name,tmp_min_lat, tmp_max_lat,chunk_bbox_list)

        custom_tempObj = Template(inps.custom_template_file)
        custom_tempObj.options['topsStack.boundingBox'] = ' '.join(chunk_bbox_list)
        
        if inps.download_flag in [ True , 'True']:
           del(custom_tempObj.options['topsStack.slcDir'])
          
        putils.write_template_file(chunk_template_file, custom_tempObj)
        putils.beautify_template_file(chunk_template_file)

        minsar_command = 'minsarApp.bash ' + chunk_template_file + ' ' + minsarApp_option

        f.write(minsar_command + '\n')
        
        lat = lat + inps.lat_step
    
    return

###########################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
