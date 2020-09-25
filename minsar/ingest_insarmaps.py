#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################


import os
import subprocess
import sys
import glob
import time
import shutil
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar import email_results

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password


##############################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='ingest_insarmaps')

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_obj = JOB_SUBMIT(inps)
        job_name = 'ingest_insarmaps'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)

    os.chdir(inps.work_dir)

    hdfeos_file = glob.glob(inps.work_dir + '/mintpy/*.he5')
    hdfeos_file.append(glob.glob(inps.work_dir +'/mintpy/SUBSET_*/*.he5'))
    hdfeos_file = hdfeos_file[0]

    json_folder = inps.work_dir + '/mintpy/JSON'
    mbtiles_file = json_folder + '/' + os.path.splitext(os.path.basename(hdfeos_file))[0] + '.mbtiles'

    if os.path.isdir(json_folder):
        shutil.rmtree(json_folder)

    command1 = 'hdfeos5_2json_mbtiles.py ' + hdfeos_file + ' ' + json_folder 
    command2 = 'json_mbtiles2insarmaps.py -u ' + password.insaruser + ' -p ' + password.insarpass + ' --host ' + \
               'insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder ' + \
               json_folder + ' --mbtiles_file ' + mbtiles_file 

    with open(inps.work_dir + '/run_insarmaps', 'w') as f:
        f.write(command1 + '\n')
        f.write(command2 + '\n')

    out_file = 'out_ingest_insarmaps'
    message_rsmas.log(inps.work_dir, command1)
    #command1 = '('+command1+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    status = subprocess.Popen(command1, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR in hdfeos5_2json_mbtiles.py')

    # TODO: Change subprocess call to get back error code and send error code to logger
    message_rsmas.log(inps.work_dir, command2)
    #command2 = '('+command2+' | tee -a '+out_file+'.o) 3>&1 1>&2 2>&3 | tee -a '+out_file+'.e'
    status = subprocess.Popen(command2, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR in json_mbtiles2insarmaps.py')

    # Email insarmaps results:
    if inps.email:
        message_rsmas.log(inps.work_dir, 'email_results.py --insarmaps ' + inps.custom_template_file)
        email_results.main([inps.custom_template_file, '--insarmaps'])

    return None


if __name__ == "__main__":
    main()
