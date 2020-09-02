#!/usr/bin/env python3
# Utility to count the number of bursts based on lat*.rdr files


import sys
import argparse
import glob
import minsar.utils.process_utilities as putils
from minsar.objects import message_rsmas

inps = None


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser.add_argument('template', metavar="FILE", help='template file to use.')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    return parser.parse_args(args)


if __name__ == "__main__":

    inps = command_line_parse(sys.argv[1:])

    inps.project_name = putils.get_project_name(custom_template_file=inps.template)
    inps.work_dir = putils.get_work_directory(None, inps.project_name)

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    itotal = 0
    lat_files = glob.glob(inps.work_dir + '/geom_reference/IW1/lat_*.rdr')
    if len(lat_files) > 0:
        print('bursts in IW1: ', len(lat_files))
        itotal = itotal + len(lat_files)
    lat_files = glob.glob(inps.work_dir + '/geom_reference/IW2/lat_*.rdr')
    if len(lat_files) > 0:
        print('bursts in IW2: ', len(lat_files))
        itotal = itotal + len(lat_files)
    lat_files = glob.glob(inps.work_dir + '/geom_reference/IW3/lat_*.rdr')
    if len(lat_files) > 0:
        print('bursts in IW3: ', len(lat_files))
        itotal = itotal + len(lat_files)
    print('Total nuber of bursts: ', itotal)
