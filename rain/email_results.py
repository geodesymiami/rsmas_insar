#! /usr/bin/env python3
"""
   Author: Falk Amelung, Sara Mirzaee
"""
###############################################################################

import os
import sys
import glob
import argparse
import subprocess
from pysar.utils import readfile
from rain.utils.process_utilities import _remove_directories, clean_list

###############################################################################
EXAMPLE = '''example:
  email_results.py 
  email_results.py $SAMPLESDIR/GalapagosSenDT128.template --insarmap
'''

def command_line_parse(iargs=None):
    """Command line parser."""
    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    return inps

def create_parser():
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(description='Email results (by default pysar results)',
                                     formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('template_file', help='template file containing ssaraopt field')
    parser.add_argument('--insarmap', action='store_true', dest='insarmap', default=False,
                    help = 'Email insarmap results')
    return parser


###################################################

def email_insarmaps_results(custom_template):
    """ email link to insarmaps.miami.edu """

    if 'email_insarmaps' not in custom_template:
        return

    cwd = os.getcwd()

    hdfeos_file = glob.glob('./PYSAR/S1*.he5')
    hdfeos_file = hdfeos_file[0]
    hdfeos_name = os.path.splitext(os.path.basename(hdfeos_file))[0]

    textStr = 'http://insarmaps.miami.edu/start/-0.008/-78.0/7"\?"startDataset=' + hdfeos_name

    mailCmd = 'echo \"' + textStr + '\" | mail -s Miami_InSAR_results:_' + os.path.basename(cwd) + ' ' + \
              custom_template['email_insarmaps']
    command = 'ssh pegasus.ccs.miami.edu \" ' + mailCmd + '\"'

    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        sys.exit('Error in email_insarmaps_results')

    return


def email_pysar_results(custom_template):
    """ email pysar results """

    textStr = 'email pysar results'

    if 'email_pysar' not in custom_template:
        return

    cwd = os.getcwd()

    fileList1 = ['velocity.png', 'avgSpatialCoherence.png', 'temporalCoherence.png', 'maskTempCoh.png', 'mask.png',
                 'demRadar_error.png', 'velocityStd.png', 'geo_velocity.png', 'coherence*.png', 'unwrapPhase*.png',
                 'rms_timeseriesResidual_quadratic.pdf', 'CoherenceHistory.pdf', 'CoherenceMatrix.pdf', 'bl_list.txt',
                 'Network.pdf', 'geo_velocity_masked.kmz']

    fileList2 = ['timeseries*.png','geo_timeseries*.png']

    if os.path.isdir('PYSAR/PIC'):
        prefix = 'PYSAR/PIC'

    template_file = glob.glob('PYSAR/INPUTS/*.template')[0]

    i = 0
    for fileList in [fileList1, fileList2]:
        attachmentStr = ''
        i = i + 1
        for fname in fileList:
            fList = glob.glob(prefix + '/' + fname)
            for fileName in fList:
                attachmentStr = attachmentStr + ' -a ' + fileName

        if i == 1 and len(template_file) > 0:
            attachmentStr = attachmentStr + ' -a ' + template_file

        mailCmd = 'echo \"' + textStr + '\" | mail -s ' + cwd + ' ' + attachmentStr + ' ' + custom_template[
            'email_pysar']
        command = 'ssh pegasus.ccs.miami.edu \"cd ' + cwd + '; ' + mailCmd + '\"'
        print(command)
        status = subprocess.Popen(command, shell=True).wait()
        if status is not 0:
            sys.exit('Error in email_pysar_results')

    return

###########################################################################################
def main(iargs=None):
    """ email pysar or insarmap results """

    inps = command_line_parse(iargs)

    custom_template = readfile.read_template(inps.template_file)

    if inps.insarmap:
        email_insarmaps_results(custom_template)

        if int(custom_template['cleanopt']) == 4:
            cleanlist = clean_list()
            _remove_directories(cleanlist[4])

    else:
        email_pysar_results(custom_template)


###########################################################################################
if __name__ == '__main__':
    main(sys.argv[1:])