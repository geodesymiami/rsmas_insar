#! /usr/bin/env python3
###############################################################################
#
# Project: dem_rsmas.py
# Author: Kawan & Falk Amelung
# Created:9/2018
#
# Notes for refactoring:
#   - use topsStack defaults (scurrently 'ssara' is given but ignored
#   - use datast_template
#   - for boundingBox create a call_isce_dem function
#   - in ssara part, use GDAL class instead of  parsing the gdalinfo output

###############################################################################

import os
import sys
import glob
import shutil
import re
import subprocess
import math
import argparse
from minsar.objects import message_rsmas
from minsar.utils import process_utilities as putils
from minsar.utils import get_boundingBox_from_kml
from minsar.objects.dataset_template import Template
import sardem.dem

EXAMPLE = """
  example:
  dem_rsmas.py  $SAMPLES/GalapagosSenDT128.template
  dem_rsmas.py  $SAMPLES/GalapagosSenDT128.template --ssara_kml
"""

DESCRIPTION = (""" Creates a DEM based on ssara_*.kml file """)

def create_parser():
    synopsis = 'Create download commands'
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('custom_template_file', help='template file with option settings.\n')
    parser.add_argument('--ssara_kml', action='store_true', help='Deprecated and not required anymore.')

    inps = parser.parse_args()
    inps = putils.create_or_update_template(inps)

    return inps

def format_bbox(bbox):
    west, south, east, north = bbox

    # Determine hemisphere for each coordinate
    south_str = f"S{abs(south):02d}" if south < 0 else f"N{abs(south):02d}"
    north_str = f"S{abs(north):02d}" if north < 0 else f"N{abs(north):02d}"
    west_str = f"W{abs(west):03d}" if west < 0 else f"E{abs(west):03d}"
    east_str = f"W{abs(east):03d}" if east < 0 else f"E{abs(east):03d}"

    # Format the output string
    name = f"{south_str}_{north_str}_{west_str}_{east_str}"
    return name

##########################################
def main(iargs=None):

    # parse
    inps = create_parser()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))
    
    dem_dir = os.path.join(inps.work_dir, 'DEM')
    if not exist_valid_dem_dir(dem_dir):
        os.mkdir(dem_dir)

    try:
       inps.slc_dir = inps.template['topsStack.slcDir']
    except:
       inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    # 10/21: inps.template['topsStack.slcDir'] may contain ./SLC  (it would be better to change where topsStack.slcDir is assigned)
    if '.' in inps.slc_dir:
       inps.slc_dir = inps.slc_dir.replace(".",os.getcwd())

    ## 7/2024: using inps.template.values() to avoid using  dataset_template=Template(inps.custom_template_file). Previous code:
    # dataset_template = Template(inps.custom_template_file)
    # ssaraopt_string = dataset_template.generate_ssaraopt_string()
    # inps.ssaraopt = ssaraopt_string.split(' ')
    #
    # if 'COSMO-SKYMED' in inps.ssaraopt:
    #   inps.slc_dir = inps.slc_dir.replace('SLC','RAW_data')
    # if 'TSX' in inps.ssaraopt:
    #   inps.slc_dir = inps.slc_dir.replace('SLC','SLC_ORIG')
      
    values = inps.template.values()
    if any("COSMO-SKYMED" in str(value).upper() for value in values):
       inps.slc_dir = inps.slc_dir.replace('SLC','RAW_data')
    if any("TSX" in str(value).upper() for value in values):
       inps.slc_dir = inps.slc_dir.replace('SLC','SLC_ORIG')

    # FA 10/2021: We probably should check here whether a DEM/*wgs84 file exist and exit if it does.
    # That could save time. On the other hand, most steps allow to be run even if data exist
    os.chdir(dem_dir)

    print('DEM generation using ISCE based on *kml file')
    try:
       ssara_kml_file=sorted( glob.glob(inps.slc_dir + '/ssara_search_*.kml') )[-1]
    except:
       # FA 7/2024: If there is no kml it should rerun generate_download_command 
       # and then a ssara command to get the kml file
       # generate_download_command.main([inps.custom_template_file])
       raise FileExistsError('No SLC/ssara_search_*.kml found')

    print('using kml file:',ssara_kml_file)

    try:
        bbox = get_boundingBox_from_kml.main( [ssara_kml_file, '--delta_lon' , '0'] )
    except:
        raise Exception('Problem with *kml file: does not contain bbox information')

    bbox = bbox.split('SNWE:')[1]
    print('bbox:',bbox)
    bbox = [val for val in bbox.split()]

    south = bbox[0]
    north = bbox[1]
    west = bbox[2]
    east = bbox[3].split('\'')[0]

    south = math.floor(float(south) - 0.5)
    north = math.ceil(float(north) + 0.5)
    west = math.floor(float(west) - 0.5)
    east = math.ceil(float(east) + 0.5)

    # demBbox = str(int(south)) + ' ' + str(int(north)) + ' ' + str(int(west)) + ' ' + str(int(east))
    # 
    # command = 'dem.py -a stitch --filling --filling_value 0 -b ' + demBbox + ' -c -u https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/'
    # 
    # message_rsmas.log(os.getcwd(), command)
    # 
    # try:
    #     #FA 8/2024: dem.main()  did not work, because it does not accept an argument list (I think).
    #     proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
    #                             universal_newlines=True)
    #     output, error = proc.communicate()
    #     print(error)
    #     if proc.returncode is not 0:
    #         print('FA 8/23: dem.py returns error. SKIPPING because it may happen because of poor dem.py call')
    #         print(output)
    #         print(error, file=sys.stderr)
    # except subprocess.CalledProcessError as exc:
    #     print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
    #     sys.exit('Error produced by dem.py')
    # else:
    #     if 'Could not create a stitched DEM. Some tiles are missing' in output:
    #         os.chdir('..')
    #         shutil.rmtree('DEM')
    #         sys.exit('Error in dem.py: Tiles are missing. Ocean???')

    bbox_LeftBottomRightTop = [int(west), int(south), int(east), int(north)]
    output_name = f"elevation_{format_bbox(bbox_LeftBottomRightTop)}.dem.wgs84"

    command = f"sardem --bbox {int(west)} {int(south)} {int(east)}  {int(north)} --data COP --make-isce-xml --output_name {output_name}"
    message_rsmas.log(os.getcwd(), command)
    
    try:
        sardem.dem.main(bbox=bbox_LeftBottomRightTop, data_source="COP", make_isce_xml=True, output_name=output_name)
    except KeyboardInterrupt:
        raise   
    except Exception as e:
        print(f"ERROR message: {e}")

    print('\n###############################################')
    print('End of dem_rsmas.py')
    print('################################################\n')

    return None

def exist_valid_dem_dir(dem_dir):
    """ Returns True of a valid dem dir exist. Otherwise remove die and return False """
    if os.path.isdir(dem_dir):
        products = glob.glob(os.path.join(dem_dir, '*dem.wgs84*'))
        if len(products) >= 3:
            print('DEM products already exist. if not satisfying, remove the folder and run again')
            return True
        else:
            shutil.rmtree(dem_dir)
            return False
    else:
        return False

###########################################################################################
if __name__ == '__main__':
    main()
