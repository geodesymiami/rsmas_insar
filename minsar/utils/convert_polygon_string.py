#!/usr/bin/env python3
# This script converts a polygon form the ASF vertex GUI into a miaplpy.subset.lalo string for MintPy and MiaplPy
# Author: Falk Amelung
# Created:8/2023
#######################################

import sys
import os
import argparse
from minsar.objects import message_rsmas

inps = None


EXAMPLE = """example:
  convert_polygon_string.py   "POLYGON((-86.581 12.3995,-86.4958 12.3995,-86.4958 12.454,-86.581 12.454,-86.581 12.3995))"
  convert_polygon_string.py   "48.1153435942954,32.48224314182711,0 48.1460783620229,32.49847964019297,0 48.1153435942954,32.48224314182711,0"
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(description='Utility to convert POLYGON string from ASF vertex GUI or GoogleEarth kml-file to topsStack, subsets strings for minsar, miaplpy \
                                                  \nFor GoogleEarth a line consisting of two points works fine.',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)
    parser.add_argument('polygon_str', nargs='?', help='POLYGON string')

    # Add arguments with default values
    parser.add_argument('--lat_delta', type=float, default=0.15, help='Latitude delta value')
    parser.add_argument('--lon_delta', type=float, default=1.5, help='Longitude delta value')

    return parser


def cmd_line_parse(args):
    """ Parses command line agurments into inps variable. """
    parser = create_parser()
    return parser.parse_args(args)


def run_convert_polygon_str(input_str, lat_delta, lon_delta):
    """ converts polygon string of the form:
        POLYGON((-86.581 12.3995,-86.4958 12.3995,-86.4958 12.454,-86.581 12.454,-86.581 12.3995))
        48.1153435942954,32.48224314182711,0 48.1460783620229,32.49847964019297,0 48.1153435942954,32.48224314182711,0
    """

    longs = []
    lats = []

    if "POLYGON" in input_str:
        modified_str = input_str.removeprefix('POLYGON((')
        modified_str = modified_str.removesuffix('))')

        points = modified_str.split(',')

        # Split each coordinate point to get longitude and latitude
        for point in points:
            long, lat = point.split()
            longs.append(float(long))
            lats.append(float(lat))
    else:
        points = input_str.split(' ')
        for point in points:
            long, lat, z = point.split(',')
            longs.append(float(long))
            lats.append(float(lat))

    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(longs)
    max_lon = max(longs)

    min_lat = round(min_lat,3)
    max_lat = round(max_lat,3)
    min_lon = round(min_lon,3)
    max_lon = round(max_lon,3)

    min_lat_bbox = round(min_lat - lat_delta,1)
    max_lat_bbox = round(max_lat + lat_delta,1)
    min_lon_bbox = round(min_lon - lon_delta,1)
    max_lon_bbox = round(max_lon + lon_delta,1)

    bbox_str = str(min_lat_bbox) + ' ' + str(max_lat_bbox) + ' ' + str(min_lon_bbox) + ' ' + str(max_lon_bbox)
    subset_str = str(min_lat) + ':' + str(max_lat) + ',' + str(min_lon) + ':' + str(max_lon)

    tops_stack_bbox_str = 'topsStack.boundingBox                = ' + bbox_str  

    mintpy_subset_str  = 'mintpy.subset.lalo                   = ' + subset_str + '    #[S:N,W:E / no], auto for no'  
    miaplpy_subset_str = 'miaplpy.subset.lalo                  = ' + subset_str + '    #[S:N,W:E / no], auto for no'  

    print("Desired strings: ")
    print('')
    print(tops_stack_bbox_str)
    print('')
    print(mintpy_subset_str)
    print(miaplpy_subset_str)
    print('')

    return 

###########################################################################################

def main(iargs=None):
    #message_rsmas.log('.', os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    inps = cmd_line_parse(sys.argv[1:])
    run_convert_polygon_str(inps.polygon_str, inps.lat_delta, inps.lon_delta)
    

###########################################################################################

if __name__ == '__main__':
    main()
