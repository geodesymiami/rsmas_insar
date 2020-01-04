#!/usr/bin/env python3
############################################################
# Program is part of MintPy                                #
# Copyright(c) 2019, Lv Xiaoran                            #
# Author:  Lv Xiaoran                                      #
############################################################



import os
import glob
import sys
import argparse
import zipfile
from minsar.objects import message_rsmas


EXAMPLE = """example:
  check_downloads.py  $TESTDATA_ISCE/project/SLC/
  check_downloads.py  $TESTDATA_ISCE/project/SLC/ --delete
"""

def create_parser():
    parser = argparse.ArgumentParser(description='delete broken zipfiles in $TESTDATA_ISCE/project/SLC/.',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser.add_argument('inputdir', nargs=1, help='directory for download zipfiles')
    parser.add_argument('--delete', action='store_true', default=False, help='whether delete data.')

    return parser


def cmd_line_parse(iargs=None):

    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    
    return inps


def check_zipfiles(inps):
    """
    check download zipfiles and get the reports
    """
    inputdir = "".join(inps.inputdir)
    os.chdir(inputdir)
    filelist = glob.glob('*.zip')
    broken_list = []
    for file in filelist:
        try:
            zf = zipfile.ZipFile(file,'r')
        except zipfile.BadZipFile:
            broken_list.append(file)
    if broken_list:
        print('Broken zipfiles:')
        for filename in broken_list:
            print(filename)
    return broken_list


def delete_files(inps,broken_list):
    """delete bad files"""
    inputdir = "".join(inps.inputdir)
    os.chdir(inputdir)
    for file in broken_list:
        real_path = os.path.realpath(file)
        if os.path.exists(real_path):
            os.remove(real_path)
            message_rsmas.log(os.getcwd(), os.path.basename(__file__) + ': deleting ' + real_path )
    return

def check_size(inps):
    """check file size equal to 0 bit and 1568 bit"""
    inputdir = "".join(inps.inputdir)
    os.chdir(inputdir)
    filelist = glob.glob('*.zip')
    bit_0_list = []
    bit_1568_list = []
    for file in filelist:
        real_path = os.path.realpath(file)
        size_byte = os.path.getsize(real_path)
        size_bit = size_byte / 8
        if size_bit == 0:
            bit_0_list.append(file)
        if size_bit == 1568:
            bit_1568_list.append(file)
    if bit_0_list:
        print('Files with 0-bit size:')
        for file_0 in bit_0_list:
            print(file_0)
    if bit_1568_list:
        print('Files with 1568-bit size:')
        for file_1568 in bit_1568_list:
            print(file_1568)
    return bit_0_list,bit_1568_list       
             
##############################################################################
def main(iargs=None):
    inps = cmd_line_parse(iargs)

    broken_files = check_zipfiles(inps)
    bit_0_files,bit_1568_files = check_size(inps)

    bad_files = broken_files + bit_0_files + bit_1568_files
    bad_files = list(set(bad_files))
    number_of_files = len(bad_files)
    print ('Number of bad files: ', number_of_files)

    if inps.delete and number_of_files > 0:
        print ('Number of files deleted: ', number_of_files)
        delete_files(inps,bad_files)
        

##########################################################################
if __name__ == '__main__':
    main(sys.argv[1:])

