#! /usr/bin/env python3
"""
   Author: Falk Amelung, Sara Mirzaee
"""
###############################################################################

import os
import sys
import glob
import subprocess
import h5py
from mintpy.utils import readfile
import minsar.utils.process_utilities as putils
from minsar.objects.auto_defaults import PathFind
from minsar.objects import message_rsmas

pathObj = PathFind()


###########################################################################################


def main(iargs=None):
    """ email mintpy or insarmaps results """

    inps = putils.cmd_line_parse(iargs, script='email_results')

    email_address = os.getenv('NOTIFICATIONEMAIL')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    if inps.email_insarmaps_flag:
        email_insarmaps_results(email_address)

        if int(inps.template['cleanopt']) == 4:
            cleanlist = pathObj.isce_clean_list
            putils.remove_directories(cleanlist[4])

        return

    if inps.email_mintpy_flag:
        email_mintpy_results(email_address)
        return

    return None

###################################################


def email_insarmaps_results(email_address):
    """ email link to insarmaps.miami.edu """

    cwd = os.getcwd()

    hdfeos_file = glob.glob('./mintpy/S1*.he5')
    hdfeos_file = hdfeos_file[0]
    hdfeos_name = os.path.splitext(os.path.basename(hdfeos_file))[0]

    ref_lat = putils.extract_attribute_from_hdf_file(file=hdfeos_file, attribute='REF_LAT')
    ref_lon = putils.extract_attribute_from_hdf_file(file=hdfeos_file, attribute='REF_LON')
    ref_lat = str(round(float(ref_lat),1))
    ref_lon = str(round(float(ref_lon),1))
         
    textStr = 'http://insarmaps.miami.edu/start/' + ref_lat + '/' + ref_lon + '/7"\?"startDataset=' + hdfeos_name

    mailCmd = 'echo \"' + textStr + '\" | mail -s Miami_InSAR_results:_' + os.path.basename(cwd) + ' ' + email_address

    command = prepend_ssh_command_if_needed(mailCmd)
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
    mailCmd = 'cd ' + cwd + '; ' + mailCmd 

    command = prepend_ssh_command_if_needed(mailCmd)
    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
        sys.exit('Error in email_mintpy_results')

    return

def prepend_ssh_command_if_needed(command):
    """ prepend ssh mail_host if needed """

    PLATFORM_NAME = os.getenv('PLATFORM_NAME')
    if  PLATFORM_NAME == 'pegasus':
        command = 'ssh pegasus.ccs.miami.edu \"' + command + '\"'

    return command

###########################################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
