#! /usr/bin/env python3
"""This script downloads SAR data and deals with various errors produced by download clients
   Author: Falk Amelung
   Created:12/2018
"""
###############################################################################

import os
import sys
import glob
import argparse
import subprocess

import messageRsmas
import _process_utilities as putils

from dataset_template import Template

###############################################################################
EXAMPLE = '''example:
  email_pysar_results.py 
  email_pysar_results.py $SAMPLESDIR/GalapagosSenDT128.template
'''

def command_line_parse(iargs=None):
    """Command line parser."""
    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    return inps

def create_parser():
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(description='Email pysar results',
                                     formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('template_file', help='template file containing ssaraopt field')
    #parser.add_argument('template_file', help='template file containing ssaraopt field', nargs='?')
    return parser

###############################################################################
def generate_file_lists(number_of_files=2):

    if number_of_files is 2:
        file_list1 = ['velocity.png',\
                 'avgSpatialCoherence.png',\
                 'temporalCoherence.png',\
                 'coherence*.png',\
                 'unwrapPhase*.png',\
                 #'mask.png',\
                 'maskTempCoh.png',\
                 'demRadar_error.png',\
                 'geo_velocity.png',\
                 'rms_timeseriesResidual_quadratic.pdf',\
                 'CoherenceHistory.pdf',\
                 'CoherenceMatrix.pdf',\
                 'bl_list.txt',\
                 'Network.pdf',\
                 'geo_velocity_masked.kmz']

        file_list2 = ['timeseries*.png']
    
        file_lists = [file_list1, file_list2]

    elif number_of_files is 3:
        file_list1 = ['velocity.png',\
                 #'avgSpatialCoherence.png',\
                 #'temporalCoherence.png',\
                 #'coherence*.png']
                 ]

        #file_list2 = [ 'unwrapPhase*.png',\
        file_list2 = ['unwrapPhase_wrap_*.png', 'geo_velocity_masked.kmz' ]                    
                 #'maskTempCoh.png',\
                 #'demRadar_error.png',\
                 #'geo_velocity.png',\
                 #'rms_timeseriesResidual_quadratic.pdf',\
                 #'CoherenceHistory.pdf',\
                 #'CoherenceMatrix.pdf',\
                 #'bl_list.txt',\
                 #'Network.pdf',\
                 # 'geo_velocity_masked.kmz']

        file_list3 = ['timeseries*.png']
    
        file_lists = [file_list1, file_list2, file_list3]

    else:
        raise Exception('ERROR number_of_files of xx not supported')
        
    return file_lists

###########################################################################################
def main(iargs=None, text_string='email pysar results'):
    """ email pysar results """

    template_file = glob.glob('PYSAR/INPUTS/*.template')[0]
    email_list = Template(template_file).get_options()['email_pysar']
    if not  email_list:
        return

    if os.path.isdir('PYSAR/PIC'):
       prefix='PYSAR/PIC'

    file_lists = generate_file_lists(number_of_files=3)

    i = 0
    cwd = os.getcwd()
    #import pdb; pdb.set_trace()
    for file_list in file_lists:
       print ('###')
       attachment_string = ''
       i = i + 1
       for fname in file_list:
           files = glob.glob(prefix+'/'+fname)
           for file in files:
               attachment_string = attachment_string+' -a '+file

       if i==1 and len(template_file)>0:
          attachment_string = attachment_string+' -a '+template_file

       mail_command = 'echo \"'+text_string+'\" | mail -s '+cwd+' '+attachment_string+' '+ email_list
       command = 'ssh pegasus.ccs.miami.edu \"cd '+cwd+'; '+mail_command+'\"'
       print(command)
       status = subprocess.Popen(command, shell=True).wait()
       if status is not 0:
          sys.exit('Error in email_pysar_results')


###########################################################################################
if __name__ == '__main__':
    main(sys.argv[1:])
