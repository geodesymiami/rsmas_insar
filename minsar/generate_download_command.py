#!/usr/bin/env python3

import os
import sys
import re
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

   OPTIONS NEED TO REVISTED (they don't work)
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

DESCRIPTION = ("""
     Creates download command ssara_command.txt containing intersectsWith='Polygon((...))'. 
     If the string is not given in *template file, it will be created based on (in that order):
         miaplpy.subset.lalo
         mintpy.subset.lalo
         topsStack.boundingBox
""")

def create_parser():
    synopsis = 'Create download commands'
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('custom_template_file', help='custom template with option settings.\n')
    parser.add_argument('--triplets', dest='triplets_flag', action='store_true', default=True, help='uploads numTriNonzeroIntAmbiguity.h5')
    parser.add_argument('--delta_lat', dest='delta_lat', default='0.0', type=float, help='delta to add to latitude from boundingBox field, default is 0.0')
    parser.add_argument('--seasonalStartDate', dest='seasonalStartDate', type=str,
                             help='seasonal start date to specify download dates within start and end dates, example: a seasonsal start date of January 1 would be added as --seasonalEndDate 0101')
    parser.add_argument('--seasonalEndDate', dest='seasonalEndDate', type=str,
                             help='seasonal end date to specify download dates within start and end dates, example: a seasonsal end date of December 31 would be added as --seasonalEndDate 1231')

    inps = parser.parse_args()
    inps = putils.create_or_update_template(inps)

    return inps

###############################################
def generate_intersects_string(dataset_template, delta_lat=0.0):
    """generates intersectsWith polygon string from miaplpy.subset.lalo, mintpy.subset.lalo or *Stack.boundingBox"""
    
    if not 'acquisition_mode' in dataset_template.get_options():
        print('WARNING: "acquisition_mode" is not given --> default: tops  (available options: tops, stripmap)')
        prefix = 'tops'
    else:
        prefix = dataset_template.get_options()['acquisition_mode']


    if 'miaplpy.subset.lalo' in dataset_template.get_options():
       print("Creating intersectsWith string using miaplpy.subset.lalo: ", dataset_template.get_options()['miaplpy.subset.lalo'])
       intersects_string = convert_subset_lalo_to_intersects_string(dataset_template.get_options()['miaplpy.subset.lalo'], delta_lat)
    elif 'mintpy.subset.lalo' in dataset_template.get_options():
       print("Creating intersectsWith string using mintpy.subset.lalo: dataset_template.get_options()['mintpy.subset.lalo']")
       intersects_string = convert_subset_lalo_to_intersects_string(dataset_template.get_options()['mintpy.subset.lalo'], delta_lat)
    else:
       print("Creating intersectsWith string using *Stack.boundingBox: ", dataset_template.get_options()[prefix + 'Stack.boundingBox'])
       intersects_string = convert_bounding_box_to_intersects_string(dataset_template.get_options()[prefix + 'Stack.boundingBox'], delta_lat)

    return intersects_string

###############################################
def convert_subset_lalo_to_intersects_string(subset_lalo, delta_lat=0):
   """ Converts a subset.lalo string in S:N,E:W format (e.g., "2.7:2.8,125.3:125.4") to an intersectsWith polygon string."""

   lat_string = subset_lalo.split(',')[0] 
   lon_string = subset_lalo.split(',')[1] 

   min_lat = float(lat_string.split(':')[0]) - delta_lat
   max_lat = float(lat_string.split(':')[1]) + delta_lat
   min_lon = float(lon_string.split(':')[0]) - delta_lat/2
   max_lon = float(lon_string.split(':')[1]) + delta_lat/2

   min_lat = round(min_lat, 2)
   max_lat = round(max_lat, 2)
   min_lon = round(min_lon, 2)
   max_lon = round(max_lon, 2)

   intersects_string = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, ' \
         '{:.2f} {:.2f}))\''.format(min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat, min_lon, min_lat)
   intersects_string = '--intersectsWith=\'Polygon(({0} {1}, {0} {3}, {2} {3}, {2} {1}, {0} {1}))\''\
                                        .format(min_lon, min_lat, max_lon, max_lat)

   return intersects_string

###############################################
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

###############################################
def convert_intersects_string_to_extent_string(intersects_string):
    """ Converts a intersectsWith string  to an extent string."""

    match = re.search(r"Polygon\(\((.*?)\)\)", intersects_string)
    if match:
        polygon_str = match.group(1)
    else:
        polygon_str = None
    
    lon_list = []
    lat_list = []
    bbox_list = polygon_str.split(',')
    for bbox in bbox_list:
        lon, lat = map(float, bbox.split())
        lon_list.append(lon)
        lat_list.append(lat)
    lon_list.sort()
    lat_list.sort()

    extent_list = [lon_list[0], lat_list[0], lon_list [-1], lat_list[-1]]
    extent_str = ' '.join(map(str, extent_list))

    return extent_str, extent_list

###############################################
def generate_download_command(template,inps):
    """ generate ssara download options to use """

    dataset_template = Template(template)
    dataset_template.options.update(pathObj.correct_for_ssara_date_format(dataset_template.options))

    ssaraopt_string, ssaraopt_dict = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt_string.split(' ')
    if 'end' not in ssaraopt_dict:
        ssaraopt_dict['end'] = '2099-12-31'

    if not any(option.startswith('ssaraopt.intersectsWith') for option in dataset_template.get_options()):
       intersects_string = generate_intersects_string(dataset_template, delta_lat=0.1)
       ssaraopt.insert(2, intersects_string)
    
    extent_str, extent_list = convert_intersects_string_to_extent_string(intersects_string)
    print('New intersectsWith sting using delta_lat=0.1: ', intersects_string)
    print('New extent sting using delta_lat=0.1: ', extent_str)

    ssara_cmd_slc_download_bash = ['ssara_federated_query.bash'] + ssaraopt 
    ssara_cmd_kml_download_python = ['ssara_federated_query.py'] + ssaraopt + ['--maxResults=20000','--asfResponseTimeout=300', '--kml','--print','>','ssara_listing.txt','2> ssara.e']
    ssara_cmd_slc_download_python = ['ssara_federated_query.py'] + ssaraopt + ['--maxResults=20000','--asfResponseTimeout=300', '--kml', '--print','--download']

    asf_cmd_slc_download = ['asf_search_args.py', '--product=SLC'] + ssaraopt + ['--print', '--download']
    asf_cmd_burst_download = ['asf_search_args.py', '--product=BURST'] + ssaraopt + ['--print', '--download']
    asf_cmd_burst2safe1 = ['ssara_listing_2_burst2safe_jobfile.py', ' ssara_listing.txt' + ' --extent', extent_str]
    asf_cmd_burst2safe2 = [f'run_workflow.bash {template} --jobfile {inps.work_dir}/SLC/run_01_burst2safe']

    with open('ssara_command.txt', 'w') as f:
        f.write(' '.join(ssara_cmd_slc_download_bash) + '\n')

    with open('asf_slc_download.txt', 'w') as f:
        f.write(' '.join(asf_cmd_slc_download) + '\n')

    with open('asf_burst_download.txt', 'w') as f:
        f.write(' '.join(ssara_cmd_kml_download_python) + '\n')
        f.write(' '.join(asf_cmd_burst_download) + '\n')
        f.write(' '.join(asf_cmd_burst2safe1 ) + '\n')
        f.write(' '.join(asf_cmd_burst2safe2 ) + '\n')

    ssara_cmd_python = ['ssara_federated_query.py'] + ssaraopt + ['--maxResults=20000','--asfResponseTimeout=300', '--kml', '--print']
    with open('ssara_command_python.txt', 'w') as f:
       f.write(' '.join(ssara_cmd_python) + '\n')

    return 
   
###############################################
def main(iargs=None):

    # parse
    inps = create_parser()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    generate_download_command(inps.custom_template_file,inps)

    return None

###############################################
if __name__ == "__main__":
    main()
