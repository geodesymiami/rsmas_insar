#!/usr/bin/env python3
"""This script converts boundingBox coordinates from ASF vertex to topsStack format
   Author: Falk Amelung
      Created:5/2019
"""

EXAMPLE = """example:
  convert_boundingbox.py 103.2,30.95,103.85,30.95,103.85,31.54,103.2,31.54,103.2,30.95
  convert_boundingbox.py '39.46 39.82 118.2 118.9'
"""

import os
import sys
import time
import subprocess
import argparse
import glob
from rinsar import messageRsmas
import rinsar._process_utilities as putils

inps = None

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='Utility to convert boundingBox formats.',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument('boundingBox', nargs='?', help='coordinates of bounding box to convert')

    return parser

def command_line_parse(args):
    """ Parses command line agurments into inps variable. """
    parser = create_parser()
    return parser.parse_args(args)

def run_convert_boundingbox(input):
    """ converts
    ASF Vertex boundingBox:
    103.2,30.95,103.85,30.95,103.85,31.54,103.2,31.54,103.2,30.95  
    103.2,   30.95,   103.85,  30.95,   103.85,  31.54,   103.2,   31.54,   103.2,   30.95  
    min_lon, min_lat, max_lon, min_lat, max_lon, max_lat, min_lon, max_lat, min_lon, min_lat

    topsStack boundingBox (bbox):
    39.46   39.82   118.2   118.9
    min_lat max_lat min_lon max_lon
    """

    # Compute SSARA options to use

    if ',' in input[0]:
        toks=input[0].split(',')
    else:
        toks=input[0].split(' ')

    if len(toks) == 10:     # ASF Vertex
        min_lon = toks[0]
        min_lat = toks[1]
        max_lon = toks[2]
        max_lat = toks[5]
    elif len(toks) == 4:    # topsStack boundingBox 
        min_lat = toks[0]
        max_lat = toks[1]
        min_lon = toks[2]
        max_lon = toks[3]

    out_asf = min_lon + ',' + min_lat + ',' + max_lon + ',' + min_lat + ',' + max_lon + ',' + max_lat + ',' + min_lon + ',' + max_lat + ',' + min_lon + ',' + min_lat
    out_sentinel_stack = min_lat +' '+ max_lat +' '+ min_lon +' '+ max_lon 
    
    print('\n'+'ASF Vertex and topsStack formats:'+'\n')
    print(out_asf)
    print(out_sentinel_stack)

    return 

###########################################################################################

if __name__ == '__main__':
    inps = command_line_parse(sys.argv[1:])
    run_convert_boundingbox(sys.argv[1:])

