#!/usr/bin/env python3
############################################################
# Copyright(c) 2019, Lv Xiaoran                            #
# Author:  Lv Xiaoran                                    #
############################################################

import os
import glob
import sys
import argparse
import zipfile


EXAMPLE = """example:
  check_download.py  $TESTDATA_ISCE/project/SLC/
  check_download.py  $TESTDATA_ISCE/project/SLC/ --delete yes
"""

def create_parser():
    parser = argparse.ArgumentParser(description='delete broken zipfiles in $TESTDATA_ISCE/project/SLC/.',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser.add_argument('slcDir', nargs=1, help='directory for download zipfiles')
    parser.add_argument('--delete', nargs='?', help='whether delete files')

    return parser

def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps

def check_data(inps):
    """
    check download data and get the reports
    """
    inputdir = "".join(inps.inputdir)
    os.chdir(inputdir)
    filelist = glob.glob('*.zip')
    brokenlist = []
    for file in filelist:
        try:
            zf = zipfile.ZipFile(file,'r')
        except zipfile.BadZipFile:
            #print(zipfile.BadZipFile)
            brokenlist.append(file)
    print('The broken zipfiles are:')
    for filename in brokenlist:
        print(filename)
    return brokenlist

def delete_data(inps,brokenlist):
    """delete data"""
    inputdir = "".join(inps.inputdir)
    os.chdir(inputdir)
    for file in brokenlist:
        realpath = os.path.realpath(file)
        os.remove(realpath)
    return

##############################################################################
def main(iargs=None):
    inps = cmd_line_parse(iargs)

    brokenfiles=check_data(inps)

    if inps.delete == 'yes':
        delete_data(inps,brokenfiles)

##########################################################################
if __name__ == '__main__':
    main(sys.argv[1:])

