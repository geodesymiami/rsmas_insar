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
import argparse
from minsar.objects.rsmas_logging import loglevel
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils
import minsar.job_submission as js
from minsar import email_results

sys.path.insert(0, os.getenv('SSARAHOME'))
import password_config as password


##############################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='ingest_insarmaps')

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    job_file_name = 'ingest_insarmaps'
    job_name = job_file_name

    if inps.wall_time == 'None':
        inps.wall_time = config[job_file_name]['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)

    time.sleep(wait_seconds)

    os.chdir(inps.work_dir)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    hdfeos_file = glob.glob(inps.work_dir + '/mintpy/S1*.he5')
    hdfeos_file.append(glob.glob(inps.work_dir +'/mintpy/SUBSET_*/S1*.he5'))
    hdfeos_file = hdfeos_file[0]

    json_folder = inps.work_dir + '/mintpy/JSON'
    mbtiles_file = json_folder + '/' + os.path.splitext(os.path.basename(hdfeos_file))[0] + '.mbtiles'

    if os.path.isdir(json_folder):
        shutil.rmtree(json_folder)

    command1 = 'hdfeos5_2json_mbtiles.py ' + hdfeos_file + ' ' + json_folder + ' |& tee out_insarmaps.log'
    command2 = 'json_mbtiles2insarmaps.py -u ' + password.insaruser + ' -p ' + password.insarpass + ' --host ' + \
               'insarmaps.miami.edu -P rsmastest -U rsmas\@gmail.com --json_folder ' + \
               json_folder + ' --mbtiles_file ' + mbtiles_file + ' |& tee -a out_insarmaps.log'
    command3 = 'upload_data_products.py --mintpy-products ' + ' ' + inps.custom_template_file + ' |& tee out_insarmaps.log'

    with open(inps.work_dir + '/mintpy/run_insarmaps', 'w') as f:
        f.write(command1 + '\n')
        f.write(command2 + '\n')
        f.write(command3 + '\n')

    out_file = 'out_insarmaps'
    message_rsmas.log(inps.work_dir, command1)
    command1 = '('+command1+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    status = subprocess.Popen(command1, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR in hdfeos5_2json_mbtiles.py')

    # TODO: Change subprocess call to get back error code and send error code to logger
    message_rsmas.log(inps.work_dir, command2)
    command2 = '('+command2+' | tee -a '+out_file+'.o) 3>&1 1>&2 2>&3 | tee -a '+out_file+'.e'
    status = subprocess.Popen(command2, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR in json_mbtiles2insarmaps.py')

    message_rsmas.log(inps.work_dir, command3)
    command3 = '('+command3+' | tee -a '+out_file+'.o) 3>&1 1>&2 2>&3 | tee -a '+out_file+'.e'
    status = subprocess.Popen(command3, shell=True).wait()
    if status is not 0:
        raise Exception('ERROR in upload_data_products.py')

    # Email insarmaps results:
    if inps.email:
        email_results.main([inps.custom_template_file, '--insarmaps'])

    return None


if __name__ == "__main__":
    main()
