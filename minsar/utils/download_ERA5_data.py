#!/usr/bin/env python3
#################################################################
# Program is used for downloading ERA5 data                      #
# Author: Lv Xiaoran                                            #
# Created: September 2020                                       #
#################################################################

import os
import argparse
import numpy as np

import mintpy
from mintpy import tropo_pyaps3
from mintpy.utils import readfile
######################################################################################
EXAMPLE = """example:
  
  download_ERA5_data.py -d SAFE_files.txt -b 36.63 41.05 -3.45 0.5 -w $WEATHER_DIR
  download_ERA5_data.py $TE/KashgarSenDT107.template -d SAFE_files.txt -w $WEATHER_DIR  

"""
SAFE_FILE = """SAFE_files.txt:
    /data/SanAndreasSenDT42/SLC/S1B_IW_SLC__1SDV_20191117T140737_20191117T140804_018968_023C8C_82DC.zip
    /data/SanAndreasSenDT42/SLC/S1A_IW_SLC__1SDV_20191111T140819_20191111T140846_029864_036803_69CA.zip
    ...
"""

Statement = """statement:
Some function of this script is modified based on MintPy tropo_pyaps3.py script!
"""

def create_parser():
    parser = argparse.ArgumentParser(description='Download ERA5 data',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE+'\n'+Statement)
    
    parser.add_argument('template_file', nargs='?', type=str,
                        help='the template file which contains topsStack.boundingBox or weather.boundingBox parameter.')

    parser.add_argument('-d', '--date_list', dest='date_list', nargs=1, type=str, 
                        help='a text file with Sentinel-1 SAFE filenames\ne.g.:SAFE_FILE')

    parser.add_argument('-b', '--bbox', dest='SNWE', type=float, nargs=4, metavar=('S', 'N','W','E'),
                        help='Bounding box of interesting area\n'+
                        'Include the uppler left corner of the area' + 
                        'and the lower right corner of the area')
    
    parser.add_argument('-w','--weather_dir',dest='weather_dir',default=os.getenv('WEATHER_DIR'),
                       help='parent directory of downloaded weather data file (default: %(default)s)')
    
    return parser

def cmd_line_parse(iargs=None):
    parser = create_parser()
    inps = parser.parse_args(args=iargs)  
   
    return inps

def get_date_list(inps):
    """read SAFE_list.txt into date list"""
    safe_list = inps.date_list[0]
    
    if safe_list.startswith('SAFE_'):
        print('read safe_list %s and get the date and hour' % safe_list)
        inps.date_list, inps.hour = tropo_pyaps3.safe2date_time(safe_list, inps.tropo_model)

    else:
        raise Exception('The safe list has wrong fime name! Please rename the file as SAFE_**')
    
    return inps

def get_grib_info(inps):
    """Read the following info from inps
        inps.grib_dir
        inps.atr
        inps.snwe
        inps.grib_files
    """
    # grib data directory, under weather_dir
    inps.grib_dir = os.path.join(inps.weather_dir, inps.tropo_model)
    if not os.path.isdir(inps.grib_dir):
        os.makedirs(inps.grib_dir)
        print('make directory: {}'.format(inps.grib_dir))

    # area extent for ERA5 grib data download
    if inps.SNWE:
        inps.snwe = get_snwe(inps)
    elif inps.template_file:
        inps.snwe = get_snwe(inps)
    else:
        raise Exception('No defined bounding box. Please define your bounding box')

    # grib file list
    inps.grib_files = tropo_pyaps3.get_grib_filenames(date_list=inps.date_list,
                                         hour=inps.hour,
                                         model=inps.tropo_model,
                                         grib_dir=inps.grib_dir,
                                         snwe=inps.snwe)
    return inps
    

def get_snwe(inps, min_buffer=2, step=10):
    # get bounding box

    if inps.SNWE:
        SNWE = inps.SNWE
    else:
        custom_template = readfile.read_template(inps.template_file) 
        if ('weather.boundingBox' in custom_template):
            SNWE = custom_template['weather.boundingBox'].split(' ')
        else:
            SNWE = custom_template['topsStack.boundingBox'].split(' ')

    lat0 = float(SNWE[0])
    lat1 = float(SNWE[1])
    lon0 = float(SNWE[2])
    lon1 = float(SNWE[3])
    
    # lat/lon0/1 --> SNWE
    S = np.floor(min(lat0, lat1) - min_buffer).astype(int)
    N = np.ceil( max(lat0, lat1) + min_buffer).astype(int)
    W = np.floor(min(lon0, lon1) - min_buffer).astype(int)
    E = np.ceil( max(lon0, lon1) + min_buffer).astype(int)

    # SNWE in multiple of 10
    if step > 1:
        S = tropo_pyaps3.floor2multiple(S, step=step)
        W = tropo_pyaps3.floor2multiple(W, step=step)
        N = tropo_pyaps3.ceil2multiple(N, step=step)
        E = tropo_pyaps3.ceil2multiple(E, step=step)
    return (S, N, W, E)
    


######################################################################################
def main(iargs=None):
    inps = cmd_line_parse(iargs)   
    
    inps.tropo_model = 'ERA5'

    # get corresponding grib files info
    get_date_list(inps)
    get_grib_info(inps)

    # download
    inps.grib_files = tropo_pyaps3.dload_grib_files(inps.grib_files, 
                                       tropo_model=inps.tropo_model,
                                       snwe=inps.snwe)
        
######################################################################################
if __name__ == '__main__':
    main()
