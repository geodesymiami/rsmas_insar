#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import argparse
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun
import minsar.utils.process_utilities as putils

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    config = putils.get_config_defaults(config_file='job_defaults.cfg')

    os.chdir(inps.work_dir)

    #########################################
    # Submit job
    #########################################
    if inps.submit_flag:
        job_file_name = 'create_runfiles'
        job_name = job_file_name
        if inps.wall_time == 'None':
            inps.wall_time = config[job_file_name]['walltime']

        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir, inps.wall_time)
        sys.exit(0)


    try:
        dem_file = glob.glob('DEM/*.wgs84')[0]
        inps.template['topsStack.demDir'] = dem_file
    except:
        print('DEM not exists!')
        sys.exit(1)

    pathObj.correct_for_isce_naming_convention(inps)
    runObj = CreateRun(inps)
    runObj.run_stack_workflow()

    run_file_list = putils.make_run_list(inps.work_dir)

    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    if inps.template['workflow'] in ['interferogram', 'slc']:
        runObj.run_post_stack()

    return None

###########################################################################################


if __name__ == "__main__":
    main()
