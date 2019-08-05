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
from mintpy.utils import readfile
import minsar.utils.process_utilities as putils
from minsar.objects.auto_defaults import PathFind
from minsar.objects import message_rsmas

pathObj = PathFind()


###########################################################################################


def main(iargs=None):
    """ email mintpy or insarmap results """

    inps = putils.cmd_line_parse(iargs, script='email_results')

    email_address = os.getenv('NOTIFICATIONEMAIL')

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))

    if inps.insarmaps:
        email_insarmaps_results(email_address)

        if int(inps.template['cleanopt']) == 4:
            cleanlist = pathObj.isce_clean_list
            putils.remove_directories(cleanlist[4])

    else:
        email_mintpy_results(email_address)

    return None

###################################################


def email_insarmaps_results(email_address):
    """ email link to insarmaps.miami.edu """

    cwd = os.getcwd()

    hdfeos_file = glob.glob('./mintpy/S1*.he5')
    hdfeos_file = hdfeos_file[0]
    hdfeos_name = os.path.splitext(os.path.basename(hdfeos_file))[0]

    textStr = 'http://insarmaps.miami.edu/start/-0.008/-78.0/7"\?"startDataset=' + hdfeos_name

    mailCmd = 'echo \"' + textStr + '\" | mail -s Miami_InSAR_results:_' + os.path.basename(cwd) + ' ' + email_address
    command = 'ssh pegasus.ccs.miami.edu \" ' + mailCmd + '\"'

    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        sys.exit('Error in email_insarmaps_results')

    return


def email_mintpy_results(email_address):
    """ email mintpy results """

    textStr = 'email mintpy results'

    cwd = os.getcwd()

    file_list = pathObj.get_email_file_list()

    if os.path.isdir('mintpy/pic'):
        prefix = 'mintpy/pic'

    template_file = glob.glob('mintpy/inputs/*.template')[0]

    i = 0
    for fileList in file_list:
        attachmentStr = ''
        i = i + 1
        for fname in fileList:
            fList = glob.glob(prefix + '/' + fname)
            for fileName in fList:
                attachmentStr = attachmentStr + ' -a ' + fileName

        if i == 1 and len(template_file) > 0:
            attachmentStr = attachmentStr + ' -a ' + template_file

    mailCmd = 'echo \"' + textStr + '\" | mail -s ' + cwd + ' ' + attachmentStr + ' ' + email_address
    command = 'ssh pegasus.ccs.miami.edu \"cd ' + cwd + '; ' + mailCmd + '\"'
    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        sys.exit('Error in email_mintpy_results')

    return

###########################################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
