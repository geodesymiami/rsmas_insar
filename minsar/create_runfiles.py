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

###############################################
def convert_subset_lalo_to_boundingBox_string(subset_lalo, delta_lat, delta_lon):
    """ Converts a subset.lalo string in SNEW format (e.g. "2.7:2.8,125.3:125.4") to a boundingBox string."""

    lat_string = subset_lalo.split(',')[0]
    lon_string = subset_lalo.split(',')[1]

    min_lat = float(lat_string.split(':')[0]) - delta_lat
    max_lat = float(lat_string.split(':')[1]) + delta_lat
    min_lon = float(lon_string.split(':')[0]) - delta_lon
    max_lon = float(lon_string.split(':')[1]) + delta_lon

    boundingBox_string = '{:.1f} {:.1f} {:.1f} {:.1f}'.format(min_lat, max_lat, min_lon, max_lon)

    return boundingBox_string

###############################################
def convert_intersectsWith_string_to_boundingBox_string(intersectsWith_str, delta_lat, delta_lon):
    """ converts polygon string of the form:
        POLYGON((-86.581 12.3995,-86.4958 12.3995,-86.4958 12.454,-86.581 12.454,-86.581 12.3995))
        48.1153435942954,32.48224314182711,0 48.1460783620229,32.49847964019297,0 48.1153435942954,32.48224314182711,0
           same functions convert_polygon_str() in convert_polygon_string.py, should move into ustilities
    """
    longs = []
    lats = []

    if "POLYGON" in intersectsWith_str:
        modified_str = intersectsWith_str.removeprefix('POLYGON((')
        modified_str = modified_str.removesuffix('))')

        points = modified_str.split(',')

        # Split each coordinate point to get longitude and latitude
        for point in points:
            long, lat = point.split()
            longs.append(float(long))
            lats.append(float(lat))
    else:
        points = intersectsWith_str.split(' ')
        for point in points:
            long, lat, z = point.split(',')
            longs.append(float(long))
            lats.append(float(lat))

    min_lat = min(lats)
    max_lat = max(lats)
    min_lon = min(longs)
    max_lon = max(longs)

    min_lat = round(min_lat,3)
    max_lat = round(max_lat,3)
    min_lon = round(min_lon,3)
    max_lon = round(max_lon,3)

    min_lat_bbox = round(min_lat - delta_lat,1)
    max_lat_bbox = round(max_lat + delta_lat,1)
    min_lon_bbox = round(min_lon - delta_lon,1)
    max_lon_bbox = round(max_lon + delta_lon,1)

    bbox_str = str(min_lat_bbox) + ' ' + str(max_lat_bbox) + ' ' + str(min_lon_bbox) + ' ' + str(max_lon_bbox)
    subset_str = str(min_lat) + ':' + str(max_lat) + ',' + str(min_lon) + ':' + str(max_lon)

    tops_stack_bbox_str = 'topsStack.boundingBox                = ' + bbox_str

    mintpy_subset_str  = 'mintpy.subset.lalo                   = ' + subset_str + '    #[S:N,W:E / no], auto for no'
    miaplpy_subset_str = 'miaplpy.subset.lalo                  = ' + subset_str + '    #[S:N,W:E / no], auto for no'

    #print("Desired strings: ")
    #print(tops_stack_bbox_str)
    #print(mintpy_subset_str)
    #print(miaplpy_subset_str)
    return bbox_str
###########################################################################################
def get_bbox_from_template(inps, delta_lat, delta_lon):
    """generates boundingBox string from miaplpy.subset.lalo, mintpy.subset.lalo or intersectsWith POLYGON string"""

    if 'miaplpy.subset.lalo' in inps.template.keys():
        print("Creating topsStack.boundingBox using miaplpy.subset.lalo")
        boundingBox_string = convert_subset_lalo_to_boundingBox_string(inps.template['miaplpy.subset.lalo'], delta_lat, delta_lon)
    elif 'mintpy.subset.lalo' in inps.template.keys():
        print("Creating topsStack.boundingBox using mintpy.subset.lalo")
        boundingBox_string = convert_subset_lalo_to_boundingBox_string(inps.template['mintpy.subset.lalo'], delta_lat, delta_lon)
    else:
        print("Creating topsStack.boundingBox using ssaraopt.intersectsWith")
        #boundingBox_string = convert_intersectsWith_string_to_boundingBox_string(inps.template['ssaraopt.intersectsWith'], delta_lat=0.0, delta_lon=0.0)
        boundingBox_string = convert_intersectsWith_string_to_boundingBox_string(inps.template['ssaraopt.intersectsWith'], delta_lat, delta_lon)

    return boundingBox_string

###########################################################################################
def main(iargs=None):
    inps = putils.cmd_line_parse(iargs, script='create_runfiles')

    
    if 'topsStack.boundingBox' in inps.template:
        if inps.template['topsStack.boundingBox'] == 'None':
            inps.template['topsStack.boundingBox'] = get_bbox_from_template(inps, delta_lat=0.15, delta_lon=3)
            print('QQ0',inps.template['topsStack.boundingBox'])

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

    if inps.template[inps.prefix + 'Stack.demDir'] == 'None':
       dem_dir = 'DEM'
    else:
       dem_dir = inps.template[inps.prefix + 'Stack.demDir']

    try:
        dem_file = glob.glob(dem_dir + '/*.wgs84')[0]
        inps.template[inps.prefix + 'Stack.demDir'] = dem_file
    except:
        raise SystemExit('DEM does not exist')

    slc_dir = inps.template[inps.prefix + 'Stack.slcDir']
    os.makedirs(slc_dir, exist_ok=True)

    if int(get_size(slc_dir)/1024**2) < 500:   # calculate slc_dir size in MB and see if there are SLCs according to size
    #if int(get_size(slc_dir)/1024**2) < -1:    # calculate slc_dir size in MB and see if there are SLCs according to size

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
