#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import argparse
import time
import subprocess
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun
import minsar.utils.process_utilities as putils
import minsar.job_submission as js

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs)

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    os.chdir(inps.work_dir)

    job_file_name = 'create_runfiles'
    job_name = job_file_name
    if inps.wall_time == 'None':
        inps.wall_time = config[job_file_name]['walltime']

    wait_seconds, new_wall_time = putils.add_pause_to_walltime(inps.wall_time, inps.wait_time)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:

        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, new_wall_time)
        sys.exit(0)

    time.sleep(wait_seconds)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    stack_prefix = os.path.basename(os.getenv('ISCE_STACK'))
    try:
        dem_file = glob.glob('DEM/*.wgs84')[0]
        dem_par = stack_prefix + '.demDir'
        inps.template[dem_par] = dem_file
    except:
        raise SystemExit('DEM does not exist')

    if not inps.template['raw_image_dir'] is None:
        unpack_script = pathObj.stripmap_unpack_script(inps.template['raw_image_dir'],
                                                       inps.template['multiple_raw_frame'])
        raw_images = glob.glob(os.path.abspath(inps.template['raw_image_dir']) + '/*')
        with open(os.path.abspath(inps.template['raw_image_dir'])+'/dates.txt', 'r') as f:
            dates = f.readlines()
        dates = [x.split('\n')[0] for x in dates]
        for raw_image in raw_images:
            for date in dates:
                if date in raw_image:
                    out_dir = '{}/{}'.format(os.path.abspath(inps.template[stack_prefix + '.slcDir']), date)
                    if not os.path.exists(out_dir):
                        os.mkdir(out_dir)
                    command_unpack = unpack_script + ' -i {} -o {}'.format(raw_image, out_dir)
                    message_rsmas.log(inps.work_dir, command_unpack)
                    if not os.path.exists(out_dir + '/{}.slc'.format(date)):
                        proc = subprocess.Popen(command_unpack, shell=True).wait()
                        if proc is not 0:
                            raise Exception('ERROR in unpacking {} image'.format(date))

    inps.stack_template = pathObj.correct_for_isce_naming_convention(inps)
    runObj = CreateRun(inps)
    runObj.run_stack_workflow()

    run_file_list = putils.make_run_list(inps.work_dir)

    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    if inps.template[stack_prefix + '.workflow'] in ['interferogram', 'slc', 'ionosphere']:
        runObj.run_post_stack()

    return None

###########################################################################################


if __name__ == "__main__":
    main()
