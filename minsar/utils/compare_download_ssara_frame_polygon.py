#!/usr/bin/env python3

import os
import sys
import subprocess
import argparse
import glob
import difflib
from minsar.objects.dataset_template import Template
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password

inps = None


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser()
    parser.add_argument('template', metavar="FILE", help='template file to use.')
    parser.add_argument( '--submit', dest='submit_flag', action='store_true', help='submits job')
    parser.add_argument('--delta_lat', dest='delta_lat', default='0.0', type=float,
                        help='delta to add to latitude from boundingBox field, default is 0.0')

    return parser


def command_line_parse(args):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    return parser.parse_args(args)


def run_ssara(work_dir, template, delta_lat):
    """ Runs ssara_federated_query.py and checks for differences
    """

    # Compute SSARA options to use

    dataset_template = Template(template)

    ssaraopt = dataset_template.generate_ssaraopt_string()
    ssaraopt = ssaraopt.split(' ')

    # add intersectWith to ssaraopt string
    ssaraopt_polygon = add_polygon_to_ssaraopt(dataset_template, ssaraopt.copy(), delta_lat)

    # get kml file and create listing
    compare_ssara_listings(work_dir, ssaraopt, ssaraopt_polygon)

    return 0


def compare_ssara_listings(work_dir, ssaraopt_frame, ssaraopt_polygon):
    """download the ssara kml file and generate a file listing of granules to be downloaded"""

    ssaraopt_frame_kml = ['--kml' if x.startswith('--parallel') else x for x in ssaraopt_frame]
    ssaraopt_frame_print = ['--print' if x.startswith('--parallel') else x for x in ssaraopt_frame]
    ssaraopt_frame_print.append('>')
    ssaraopt_frame_print.append('ssara_listing_frame.txt')

    ssara_call    = ['ssara_federated_query.py'] + ssaraopt_frame_kml
    message_rsmas.log(work_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)
    rename_latest_kml(suffix ='frame')
    ssara_call    = ['ssara_federated_query.py'] + ssaraopt_frame_print
    message_rsmas.log(work_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)

    ssaraopt_polygon_kml = ['--kml' if x.startswith('--parallel') else x for x in ssaraopt_polygon]
    ssaraopt_polygon_print = ['--print' if x.startswith('--parallel') else x for x in ssaraopt_polygon]
    ssaraopt_polygon_print.append('>')
    ssaraopt_polygon_print.append('ssara_listing_polygon.txt')

    ssara_call    = ['ssara_federated_query.py'] + ssaraopt_polygon_kml
    message_rsmas.log(work_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)
    rename_latest_kml(suffix ='polygon')
    ssara_call    = ['ssara_federated_query.py'] + ssaraopt_polygon_print
    message_rsmas.log(work_dir, ' '.join(ssara_call))
    ssara_process = subprocess.run(' '.join(ssara_call), shell=True)

    with open('ssara_listing_frame.txt', 'r') as file0:
       with open('ssara_listing_polygon.txt', 'r') as file1:
        diff = difflib.unified_diff(
            file0.readlines(),
            file1.readlines(),
            fromfile='file0',
            tofile='file1',
        )
        print('\ndiff ssara_listing_frame.txt ssara_listing_polygon.txt:')
        for line in diff:
            sys.stdout.write(line)
        print(' ')
    return None


def rename_latest_kml( suffix ):
    """Inserts a string prior to the extension"""
    list_of_files = glob.glob(os.getcwd() + '/*') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)
    fname = os.path.basename(latest_file)
    new_fname = os.getcwd() + '/' + fname.split('.')[0] + '_' + suffix + '.' + fname.split('.')[1]
    os.rename(latest_file,new_fname)

    return


def add_polygon_to_ssaraopt( dataset_template, ssaraopt, delta_lat ):
    """calculates intersectsWith polygon from bbox and replace frame in ssaraopt if give"""
    bbox_list = dataset_template.get_options()['topsStack.boundingBox'][1:-1].split(' ')
    delta_lon = delta_lat * 0.2
    min_lat = float( bbox_list[0] ) - delta_lat
    max_lat = float( bbox_list[1] ) + delta_lat
    min_lon = float( bbox_list[2] ) - delta_lon
    max_lon = float( bbox_list[3] ) + delta_lon

    polygon = '--intersectsWith=\'Polygon(({:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}, {:.2f} {:.2f}))\'' .format(
        min_lon, min_lat, min_lon, max_lat, max_lon, max_lat, max_lon, min_lat, min_lon, min_lat)

    # add --polygon and remove --frame option
    ssaraopt.insert(2,polygon)
    ssaraopt = [ x for x in ssaraopt if not x[0:7]=='--frame']

    return ssaraopt


if __name__ == "__main__":
    inps = command_line_parse(sys.argv[1:])

    inps.project_name = putils.get_project_name(custom_template_file=inps.template)
    inps.work_dir = putils.get_work_directory(None, inps.project_name)
    inps.slc_dir = inps.work_dir + "/SLC"

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'download_ssara_rsmas'
        job_name = inps.template.split(os.sep)[-1].split('.')[0]
        inps.wall_time = '24:00'
        job_obj = JOB_SUBMIT(inps)
        job_obj.submit_script(job_name, job_file_name, sys.argv[:])
        sys.exit(0)

    os.chdir(inps.work_dir)
    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))
    if not os.path.isdir(inps.slc_dir):
        os.makedirs(inps.slc_dir)
    os.chdir(inps.slc_dir)

    succesful = run_ssara(inps.work_dir, inps.template, inps.delta_lat)
