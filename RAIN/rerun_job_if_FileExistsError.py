#! /usr/bin/env python3
###############################################################################
# Author: Falk Amelung
# Created: 11/2018
###############################################################################
"""
check for existence of directories and empty files for run_operations.py,
create them as needed
"""
import os
import glob
import subprocess

def email_rerun_message(file_name):
    long_name = os.getcwd().split('/')[-2] + '/' + os.getcwd().split('/')[-1] + '/' + file_name
    text_str = 'Now rerunning because of FileExists error:' + file_name
    mail_cmd = 'echo \"'+text_str+'\" | mail -s RERUNNING:_' + long_name + ' ' +  os.getenv('NOTIFICATIONEMAIL')  
    command = 'ssh pegasus.ccs.miami.edu \"cd '+os.getcwd()+'; '+mail_cmd+'\"'
    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
       raise Exception('ERROR in email_rerun_message')

def main():
    """ 
    Checks in error files of run_*_merge_master_slave_slc for FileExistsError. 
    Rerun job if found using createBatch. 
    """

    error_files=glob.glob('run_*_merge_master_slave_slc_*.e')
    for file in error_files:
        job_file=glob.glob(file.rsplit('_', 1)[0] + '*.job')[0]
        for line in open(job_file, "r").read().split('\n'):
            if 'SentinelWrapper' in line:
               print(line)
               with open('run_rerun_FileExistsError', 'w') as out_file:
                   out_file.write(line + '\n')

        email_rerun_message(file_name=job_file)
        os.remove(file)
        os.remove(file.split('.e')[0] + '.o')
        cmd = 'createBatch.pl ' + os.getcwd() + '/run_rerun_FileExistsError'
        status=0
        status = subprocess.Popen(cmd, shell=True).wait()
        if status is not 0:
            #logger.error('ERROR submitting jobs using createBatch.pl run_rerun_FileExistsError')  # FA 11/18: need to be initialized?
            raise Exception('ERROR submitting jobs using createBatch.pl run_rerun_FileExistsError')

###########################################################################################
if __name__ == '__main__':
    main()
