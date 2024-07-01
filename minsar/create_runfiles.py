#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import time
import shutil
import subprocess
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT
from minsar.objects.unpack_sensors import Sensors

pathObj = PathFind()


###########################################################################################


def main(iargs=None):
    inps = putils.cmd_line_parse(iargs, script='create_runfiles')
    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    os.chdir(inps.work_dir)

    #time.sleep(putils.pause_seconds(inps.wait_time))

    inps.out_dir = inps.work_dir
    inps.num_data = 1

    job_obj = JOB_SUBMIT(inps)
    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'create_runfiles'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)
        sys.exit(0)

    try:
       dem_dir = inps.template[inps.prefix + 'Stack.demDir']
    except:
       dem_dir = 'DEM'

    try:
        dem_file = glob.glob(dem_dir + '/*.wgs84')[0]
        inps.template[inps.prefix + 'Stack.demDir'] = dem_file
    except:
        raise SystemExit('DEM does not exist')

    slc_dir = inps.template[inps.prefix + 'Stack.slcDir']
    os.makedirs(slc_dir, exist_ok=True)

    if int(get_size(slc_dir)/1024**2) < 500:   # calculate slc_dir size in MB and see if there are SLCs according to size

        # Unpack Raw data:
        if not inps.template['raw_image_dir'] in [None, 'None']:
            #raw_image_dir = inps.template['raw_image_dir']               # FA 1/23: it would be better to have ORIG_DATA set in defaults for both CSK and TSX
            raw_image_dir = os.path.join(inps.work_dir, inps.template['raw_image_dir'])
        else:
            raw_image_dir = os.path.join(inps.work_dir, 'RAW_data')

        if os.path.exists(raw_image_dir):
            unpackObj = Sensors(raw_image_dir, slc_dir, remove_file='False',
                                multiple_raw_frame=inps.template['multiple_raw_frame'])
            unpack_run_file = unpackObj.start()
            unpackObj.close()

            job_obj.write_batch_jobs(batch_file=unpack_run_file)
            job_status = job_obj.submit_batch_jobs(batch_file=unpack_run_file)

            if not job_status:
                raise Exception('ERROR: Unpacking was failed')
        else:
            raise Exception('ERROR: No data (SLC or Raw) available')

    # make run file:
    run_files_dirname = "run_files"
    config_dirnane = "configs"

    if inps.copy_to_tmp:
        run_files_dirname += "_tmp"
        config_dirnane += "_tmp"

    run_dir = os.path.join(inps.work_dir, run_files_dirname)
    config_dir = os.path.join(inps.work_dir, config_dirnane)

    for directory in [run_dir, config_dir]:
        if os.path.exists(directory):
            shutil.rmtree(directory)

    inps.Stack_template = pathObj.correct_for_isce_naming_convention(inps)
    if inps.ignore_stack and os.path.exists(inps.work_dir + '/coreg_secondarys'):
            shutil.rmtree(inps.work_dir + '/tmp_coreg_secondarys', ignore_errors=True)
            shutil.move(inps.work_dir + '/coreg_secondarys', inps.work_dir + '/tmp_coreg_secondarys' ) 

    runObj = CreateRun(inps)
    runObj.run_stack_workflow()

    if inps.ignore_stack and os.path.exists(inps.work_dir + '/tmp_coreg_secondarys'):
            shutil.move(inps.work_dir + '/tmp_coreg_secondarys', inps.work_dir + '/coreg_secondarys' ) 

    if os.path.isfile(run_dir + '/run_06_extract_stack_valid_region'):
        with open(run_dir + '/run_06_extract_stack_valid_region', 'r') as f:
            line = f.readlines()
        with open(run_dir + '/run_06_extract_stack_valid_region', 'w') as f:
            f.writelines(['rm -rf ./stack; '] + line )

    run_file_list = putils.make_run_list(inps.work_dir)
    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    if inps.copy_to_tmp:
        run_file_list = [item.replace("/run_files/", "/run_files_tmp/") for item in run_file_list]
        with open(inps.work_dir + '/run_files_tmp_list', 'w') as run_file:
            for item in run_file_list:
                run_file.writelines(item + '\n')
        shutil.copytree(pathObj.rundir, run_dir)

    if inps.prefix == 'tops':
        # check for orbits
        orbit_dir = os.getenv('SENTINEL_ORBITS')
        local_orbit = os.path.join(inps.work_dir, 'orbits')
        precise_orbits_in_local = glob.glob(local_orbit + '/*/*POEORB*')
        if len(precise_orbits_in_local) > 0:
            for orbit_file in precise_orbits_in_local:
                os.system('cp {} {}'.format(orbit_file, orbit_dir))

    # Writing job files
    if inps.write_jobs:
        for item in run_file_list:
            job_obj.write_batch_jobs(batch_file=item)

        if inps.template['processingMethod'] == 'smallbaseline':
            job_name = 'smallbaseline_wrapper'
            job_file_name = job_name
            command = ['smallbaselineApp.py', inps.custom_template_file, '--dir', 'mintpy;']

            # pre_command = ["""[[ $(ls mintpy/time* | wc -l) -eq 1 ]] && rm mintpy/time*"""]
            pre_command = ["check_timeseries_file.bash --dir mintpy;"]
            post_command = ["create_html.py  mintpy/pic;"]
            command = pre_command + command + post_command

            job_obj.submit_script(job_name, job_file_name, command, writeOnly='True')
        else:
            job_name = 'miaplpy_wrapper'
            job_file_name = job_name
            command = ['miaplpyApp.py', inps.custom_template_file, '--dir', 'miaplpy']
            job_obj.submit_script(job_name, job_file_name, command, writeOnly='True')

    print("copy_to_tmp: {}".format(inps.copy_to_tmp))
    if inps.copy_to_tmp:
        #run_dir_tmp = os.path.join(inps.work_dir, 'run_files_tmp')
        config_dir_tmp = os.path.join(inps.work_dir, 'configs_tmp')
        shutil.copytree(os.path.join(inps.work_dir, "configs"), config_dir_tmp)
        
        cmd = "update_configs_for_tmp.bash {}".format(inps.work_dir)
        subprocess.Popen(cmd, shell=True)
        

    return None


def get_size(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


###########################################################################################


if __name__ == "__main__":
    main()
