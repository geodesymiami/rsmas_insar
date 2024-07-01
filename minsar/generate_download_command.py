#!/usr/bin/env python3

import os
import sys
import time
import datetime
import argparse
from minsar.objects.dataset_template import Template
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils import process_utilities as putils

pathObj = PathFind()
inps = None

##############################################################################
EXAMPLE = """example:
    generate_download_command.py $TE/GalapagosSenDT128.template

   very  old  download data options (don't work)
       --delta_lat DELTA_LAT
                        delta to add to latitude from boundingBox field, default is 0.0
       --seasonalStartDate SEASONALSTARTDATE
                        seasonal start date to specify download dates within start and end dates, example: a seasonsal start date of January 1 would be added as --seasonalEndDate 0101
       --seasonalEndDate SEASONALENDDATE
                        seasonal end date to specify download dates within start and end dates, example: a seasonsal end date of December 31 would be added as --seasonalEndDate 1231
       --parallel PARALLEL   determines whether a parallel download is required with a yes/no
       --processes PROCESSES
                        specifies number of processes for the parallel download, if no value is provided then the number of processors from os.cpu_count() is used
"""

DESCRIPTION = (
    "Creates data download commands"
)

def create_parser():
    synopsis = 'Create download commands'
    parser = argparse.ArgumentParser(description=synopsis, epilog=EXAMPLE, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('custom_template_file', nargs='?', help='custom template with option settings.\n')
    parser.add_argument('--triplets', dest='triplets_flag', action='store_true', default=True, help='uploads numTriNonzeroIntAmbiguity.h5')
    parser.add_argument('--delta_lat', dest='delta_lat', default='0.0', type=float, help='delta to add to latitude from boundingBox field, default is 0.0')
    parser.add_argument('--seasonalStartDate', dest='seasonalStartDate', type=str,
                             help='seasonal start date to specify download dates within start and end dates, example: a seasonsal start date of January 1 would be added as --seasonalEndDate 0101')
    parser.add_argument('--seasonalEndDate', dest='seasonalEndDate', type=str,
                             help='seasonal end date to specify download dates within start and end dates, example: a seasonsal end date of December 31 would be added as --seasonalEndDate 1231')

    inps = parser.parse_args()

    inps.project_name = putils.get_project_name(inps.custom_template_file)
    print("Project Name: ", inps.project_name)

    inps.work_dir = putils.get_work_directory(None, inps.project_name)
    print("Work Dir: ", inps.work_dir)


    return inps

def main(iargs=None):

    # parse
    inps = create_parser()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    #if not inps.template[inps.prefix + 'Stack.slcDir'] is None:
    #    inps.download_dir = inps.template[inps.prefix + 'Stack.slcDir']
 
    #if 'COSMO' in inps.template['ssaraopt.platform']:
    #    inps.download_dir = os.path.join(inps.work_dir, 'RAW_data')
    #elif 'TSX' in inps.template['ssaraopt.collectionName']:
    #    inps.download_dir = os.path.join(inps.work_dir, 'SLC_ORIG')
    #else:
    #    inps.download_dir = os.path.join(inps.work_dir, 'SLC')

    #if not os.path.isdir(inps.download_dir):
    #    os.makedirs(inps.download_dir)
    #os.chdir(inps.download_dir)

    generate_command(inps.custom_template_file)

    return None

def generate_command(template):
    """ generate ssara download options to use """

    dataset_template = Template(template)
    dataset_template.options.update(pathObj.correct_for_ssara_date_format(dataset_template.options))

    ssaraopt_string = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt_string.split(' ')

    if 'ssaraopt.intersectsWith' not in dataset_template.get_options():
       intersects_string = generate_intersects_string(dataset_template)
       ssaraopt.insert(2, intersects_string)
       ssaraopt.append('--maxResults=20000')

    ssara_cmd_bash = ['ssara_federated_query.bash'] + ssaraopt 
    ssara_cmd_python = ['ssara_federated_query.py'] + ssaraopt + ['--asfResponseTimeout=300', '--kml', '--print', '--download']
    asf_cmd_python = ['asf_search_args.py'] + ssaraopt + ['--Product', 'SLC', '--print', '--download']

    with open('ssara_command_bash.txt', 'w') as f:
        f.write(' '.join(ssara_cmd_bash) + '\n')
    with open('ssara_command_python.txt', 'w') as f:
        f.write(' '.join(ssara_cmd_python) + '\n')
    with open('asf_command_python.txt', 'w') as f:
        f.write(' '.join(ssara_cmd_python) + '\n')

    return 

def generate_intersects_string(dataset_template, delta_lat=0.0):
    """generates intersectsWith polygon string from miaplpy.subset.lalo or *Stack.boundingBox"""
    
    if not 'acquisition_mode' in dataset_template.get_options():
        print('WARNING: "acquisition_mode" is not given --> default: tops  (available options: tops, stripmap)')
        prefix = 'tops'
    else:
        prefix = dataset_template.get_options()['acquisition_mode']

    intersects_string_subset_lalo = convert_subset_lalo_to_intersects_string(dataset_template.get_options()['miaplpy.subset.lalo'])
    intersects_string_boundingBox = convert_bounding_box_to_intersects_string(dataset_template.get_options()[prefix + 'Stack.boundingBox'], delta_lat)

    if 'miaplpy.subset.lalo' in dataset_template.get_options():
       print("Creating intersectsWith string using miaplpy.subset.lalo")
       intersects_string = intersects_string_subset_lalo 
    else:
       print("Creating intersectsWith string using *Stack.boundingBox")
       intersects_string = intersects_string_boundingBox

    return intersects_string

def convert_subset_lalo_to_intersects_string(subset_lalo):
   """ Converts a subset.lalo string in S:N,E:W format (e.g., "2.7:2.8,125.3:125.4") to an intersectsWith polygon string."""

   lat_string = subset_lalo.split(',')[0] 
   lon_string = subset_lalo.split(',')[1] 

   min_lat = float(lat_string.split(':')[0])
   max_lat = float(lat_string.split(':')[1])
   min_lon = float(lon_string.split(':')[0])
   max_lon = float(lon_string.split(':')[1])

   intersects_string = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, ' \
         '{:.2f} {:.2f}))\''.format(min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat, min_lon, min_lat)

   return intersects_string

def convert_bounding_box_to_intersects_string(string_bbox, delta_lat):
   """ Converts a topsStack.boundingBox string  (e.g., 2.5 3.1 124.0 127.0) to an intersectsWith polygon string."""
   # removing double whitespaces, FA 10/21: should be done where *template input is examined

   string_bbox =  ' '.join(string_bbox.split())
   bbox_list = string_bbox.split(' ')

   bbox_list[0] = bbox_list[0].replace("\'", '')   # this does ["'-8.75", '-7.8', '115.0', "115.7'"] (needed for run_operations.py, run_operations
   bbox_list[1] = bbox_list[1].replace("\'", '')   # -->       ['-8.75',  '-7.8', '115.0', '115.7']  (should be modified so that this is not needed)
   bbox_list[2] = bbox_list[2].replace("\'", '')
   bbox_list[3] = bbox_list[3].replace("\'", '')

   delta_lon = delta_lat * 0.2
   min_lat = float(bbox_list[0]) - delta_lat
   max_lat = float(bbox_list[1]) + delta_lat
   min_lon = float(bbox_list[2]) - delta_lon
   max_lon = float(bbox_list[3]) + delta_lon

   intersects_string = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, ' \
          '{:.2f} {:.2f}))\''.format(min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat, min_lon, min_lat)

   return intersects_string
   
if __name__ == "__main__":
    main()
