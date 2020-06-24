#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import time
import subprocess
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar import email_results
from mintpy import smallbaselineApp
from mintpy import prep_isce
import contextlib

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs, script='smallbaseline_wrapper')

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    time.sleep(putils.pause_seconds(inps.wait_time))
    
    #########################################
    # stripmap prep to isce
    #########################################
    if inps.template['acquisition_mode']=='stripmap':
        inps.dsetDir = inps.work_dir +'/Igrams';
        inps.slcDir  = inps.work_dir +'/merged/SLC';
        inps.geometryDir = inps.work_dir +'/geom_master';
        inps.baselineDir = inps.work_dir +'/baselines';
        masterDate= inps.template['stripmapStack.master']
        if masterDate=='None':
            command1= 'cp -r '+inps.slcDir+'/'+os.listdir(inps.slcDir)[0]+'/'+'masterShelve '+inps.work_dir+'/.';
        else:
            command1= 'cp -r '+inps.slcDir+'/' + masterDate+'/'+'masterShelve '+inps.work_dir+'/.';
        print(command1);subprocess.Popen(command1, shell=True).wait();
        inps.metaFile= inps.work_dir+'/' +'masterShelve/data.dat';
        command2= 'prep_isce.py -d '+inps.dsetDir+' -m '+inps.metaFile+' -b '+inps.baselineDir+' -g '+inps.geometryDir; 
        print(command2)
        subprocess.Popen(command2, shell=True).wait();
    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_obj = JOB_SUBMIT(inps)
        job_name = 'smallbaseline_wrapper'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)
        sys.exit(0)

    os.chdir(inps.work_dir)

    try:
        with open('out_mintpy.o', 'w') as f:
            with contextlib.redirect_stdout(f):
                smallbaselineApp.main([inps.custom_template_file])
    except:
        with open('out_mintpy.e', 'w') as g:
            with contextlib.redirect_stderr(g):
                smallbaselineApp.main([inps.custom_template_file])

    inps.mintpy_dir = os.path.join(inps.work_dir, pathObj.mintpydir)
    putils.set_permission_dask_files(directory=inps.mintpy_dir)

    # Email Mintpy results
    if inps.email:
        email_results.main([inps.custom_template_file, '--mintpy'])

    return None

###########################################################################################


if __name__ == "__main__":
    main()


