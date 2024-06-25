#!/usr/bin/env python3
# Authors:  Falk Amelung
# This script creates an index.html file o display mintpy results.
###############################################################################
import os  
import sys
import re
import argparse
from minsar.objects import message_rsmas

EXAMPLE = """example:
    create_html.py MaunaLoaSenDT87/mintpy_5_20/pic
"""

DESCRIPTION = (
    "Creates index.html file to display images in the mintpy/pic folder."
)

def create_parser():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EXAMPLE,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "dir", type=str, help="mintpy/pic directory path"
    )
    inps = parser.parse_args()
    return inps

###################################################################################  
def main(iargs=None):

    message_rsmas.log(os.getcwd(), os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1:]))

    # parse
    inps = create_parser()

    # import  (remove the directory of script from sys.path)
    sys.path.pop(0)
    from minsar.create_html import create_html
   
    # run
    create_html(inps)

   ################################################################################
if __name__ == '__main__':
    main()
