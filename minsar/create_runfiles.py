#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import time
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.utils.stack_run import CreateRun
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

pathObj = PathFind()

###########################################################################################


def main(iargs=None):

    inps = putils.cmd_line_parse(iargs)

    os.chdir(inps.work_dir)

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_obj = JOB_SUBMIT(inps)
        job_name = 'create_runfiles'
        job_file_name = job_name
        job_obj.submit_script(job_name, job_file_name, sys.argv[:])
        sys.exit(0)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))
    try:
        dem_file = glob.glob('DEM/*.wgs84')[0]
        inps.template['topsStack.demDir'] = dem_file
    except:
        raise SystemExit('DEM does not exist')
    
    # check for orbits
    orbit_dir = os.getenv('SENTINEL_ORBITS')
    print ('Updating orbits...')
    orbit_command = 'dloadOrbits.py --dir {}'.format(orbit_dir)
    if not inps.template['ssaraopt.startDate'] == 'None':
        orbit_command += ' --start {}'.format(inps.template['ssaraopt.startDate'])
    if not inps.template['ssaraopt.endDate'] == 'None':
        orbit_command += ' --end {}'.format(inps.template['ssaraopt.endDate'])
    message_rsmas.log(inps.work_dir, orbit_command)
    os.system(orbit_command)

    # make run file
    inps.topsStack_template = pathObj.correct_for_isce_naming_convention(inps)
    runObj = CreateRun(inps)
    runObj.run_stack_workflow()

    run_file_list = putils.make_run_list(inps.work_dir)

    with open(inps.work_dir + '/run_files_list', 'w') as run_file:
        for item in run_file_list:
            run_file.writelines(item + '\n')

    return None

###########################################################################################


if __name__ == "__main__":
    main()
