#!/usr/bin/env python3

import os
import sys
import re
import argparse
from pathlib import Path
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind

# pathObj = PathFind()
inps = None

##############################################################################
EXAMPLE = """example:
    ssara_listing_2_burst2safe_jobfile.py SLC/ssara_listing.txt --extent -91.24 -0.96 -91.08 -0.711

    burst2safe is currently limited. It requires --extent option. Download bursts using asf_search_args.py and then use
    modified burst2safe that downloads only the *xml file. 

 """

DESCRIPTION = ("""
     Creates runfile and jobfile for burst2safe (modified version)
""")

def create_parser():
    synopsis = 'Create run_file'
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('ssara_listing_path', help='file name\n')
    parser.add_argument('--extent', required=True, type=str, nargs=4, metavar=('W', 'S', 'E', 'N'), help='Bounds in lat/lon describing spatial extent')
    inps = parser.parse_args()

    return inps

###############################################


def main(iargs=None):

    # parse
    inps = create_parser()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(os.getcwd(), os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    # dir = inps.ssara_listing_path.parent
    # run_01_burst2safe_path = dir / 'run_01_burst2safe'

    dir = os.path.dirname(inps.ssara_listing_path)
    run_01_burst2safe_path = os.path.join(dir, 'run_01_burst2safe')


    absolute_orbits = []
    with open(inps.ssara_listing_path, 'r') as file:
        for line in file:
            if line.startswith("ASF"):
                parts = line.split(',')
                absolute_orbits.append(parts[2])
    
    with open(run_01_burst2safe_path, 'w') as file:
        for orbit in absolute_orbits:
            command = f'burst2safe --orbit {orbit} --extent {" ".join(inps.extent)}\n'
            file.write(command)
    # for orbit in absolute_orbits:
    #     print('burst2safe --orbit ',orbit,' --extent',' '.join(inps.extent))

###############################################
if __name__ == "__main__":
    main()
