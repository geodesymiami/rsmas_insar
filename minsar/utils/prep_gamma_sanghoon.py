#!/usr/bin/env python3
########################
# Author: Falk Amelung
#######################

import os
import sys
import glob
import shutil
import argparse
from pathlib import Path
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

sys.path.insert(0, os.getenv('SSARAHOME'))

pathObj = PathFind()
############################################################
EXAMPLE = """example:
        ATTENTION: Iceye data need to be in MaunaLoaTsxA1 directory as MintPy does not understand Ice or Iceye yet

        prep_gamma_sanghoon.py interferogram --slc-dir ./SLC --geometry-dir geometry
        prep_gamma_sanghoon.py $SCRATCHDIR/MaunaLoaTsxA1 
        prep_gamma_sanghoon.py $SCRATCHDIR/MaunaLoaTsxA1 --slc-dir 
"""
###########################################################################################
def create_parser():
    synopsis = 'Create jobfile for ingestion into insarmaps'
    epilog = EXAMPLE
    parser = argparse.ArgumentParser(description=synopsis, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(dest='project_dir', nargs=1, help='Directory with interferograms, SLC and geometry dirs.\n')

    parser.add_argument('--ifgram-dir', dest='ifgram_dir', default=None, help='directory with interferograms (default: %(default)s).')
    parser.add_argument('--slc-dir', dest='slc_dir', default=None, help='directory with SLCs (default: %(default)s).')
    parser.add_argument('--geometry-dir', dest='geometry_dir', default=None, help='directory with simulation/geometry files (default: %(default)s).')

    inps = parser.parse_args()

    if inps.ifgram_dir is None:
        inps.ifgram_dir = inps.project_dir[0] + '/interferograms'
    if inps.slc_dir is None:
        inps.slc_dir = inps.project_dir[0] + '/SLC'
    if inps.geometry_dir is None:
        inps.geometry_dir = inps.project_dir[0] + '/geometry'
   
    return inps

def main(iargs=None):
    
    inps = create_parser()
    inps.work_dir = os.getcwd()

    input_arguments = sys.argv[1::]
    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))
    
    ##### geometry: copy files
    print('\nCopying *files in geometry dir ...\n')
    dem_file = glob.glob(f"geometry/*.hgt")[0]
    date = os.path.basename(dem_file).split(".")[0]     # assumes name diff_filt_240401_240420_4rlks.unw
    dem_par_file = f"geometry/{date}.diff.par"
    lookup_table_file = glob.glob(f"geometry/*{date}.lt_fine")[0]
    lookup_table_par_file = glob.glob(f"geometry/*.dem.par")[0]

    new_dem_file =  f"geometry/sim_{date}.rdc.dem"
    new_dem_par_file = f"geometry/sim_{date}.diff_par"
    new_lookup_table_file = f"geometry/sim_{date}.UTM_TO_RDC"
    new_lookup_table_par_file = f"geometry/sim_{date}.utm.dem.par"

    if not os.path.isfile(dem_file):
        raise FileNotFoundError(f"No such file: {dem_file}")
    if not os.path.isfile(dem_par_file):
        raise FileNotFoundError(f"No such file: {dem_par_file}")
    if not os.path.isfile(lookup_table_file):
        raise FileNotFoundError(f"No such file: {lookup_table_file}")
    if not os.path.isfile(lookup_table_par_file):
        raise FileNotFoundError(f"No such file: {lookup_table_par_file}")

    shutil.copy(dem_file, new_dem_file)
    shutil.copy(dem_par_file, new_dem_par_file)
    shutil.copy(lookup_table_file, new_lookup_table_file)
    shutil.copy(lookup_table_par_file, new_lookup_table_par_file)
   
    ##### interferograms: copy files
    ifgram_dirs = glob.glob(inps.ifgram_dir + "/IFGRAM*")  
    ifgram_dirs = [dir for dir in ifgram_dirs if os.path.isdir(dir)]  

    print('Copying *par_files in',inps.ifgram_dir,':\n')
    print(ifgram_dirs) 

    for dir in ifgram_dirs:

        print('Working on: ',dir)
        unw_file =  os.path.basename(glob.glob(dir + "/diff*rlks.unw")[0])
        unw_file_without_ext = os.path.splitext(unw_file)[0]

        date1, date2, rlks_str = unw_file_without_ext.split("_")[2:5]     # assumes name diff_filt_240401_240420_4rlks.unw
                
        par_file1 = f"SLC/{date1}/{date1}.mli.par"
        par_file2 = f"SLC/{date2}/{date2}.mli.par"
        amp_par_file1 = f"{dir}/{date1}_{rlks_str}.amp.par"
        amp_par_file2 = f"{dir}/{date2}_{rlks_str}.amp.par"

        base_perp_file = f"{dir}/{date1}-{date2}.base_perp"
        baseline_file = f"{dir}/{date1}-{date2}.baseline"
        off_file =  f"{dir}/{date1}_{date2}.off"
        corner_file =  f"{dir}/{date1}_{date2}.corner"
        corner_full_file =  f"{dir}/{date1}_{date2}.corner_full"
        cor_file =  f"{dir}/{date1}_{date2}_{rlks_str}.cc"
        
        new_base_perp_file = f"{dir}/{date1}_{date2}_{rlks_str}.base_perp"
        new_baseline_file = f"{dir}/{date1}-{date2}_{rlks_str}.base_line"
        new_off_file =  f"{dir}/{date1}_{date2}_{rlks_str}.off"
        new_corner_file =  f"{dir}/{date1}_{rlks_str}.amp.corner"
        new_corner_full_file =  f"{dir}/{date1}_{rlks_str}.amp.corner_full"
        new_cor_file =  f"{dir}/filt_{date1}_{date2}_{rlks_str}.cor"
        
        # FA 5/2024: I am not sure this checking for file existence works.  I woudl think to use glob.glob in a try except structure but this was suggesed by copilot.
        if not os.path.isfile(par_file1):
            raise FileNotFoundError(f"No such file: '{par_file1}'")
        if not os.path.isfile(par_file2):
            raise FileNotFoundError(f"No such file: '{par_file2}'")
        if not os.path.isfile(base_perp_file):
            raise FileNotFoundError(f"No such file: '{base_perp_file}'")
        if not os.path.isfile(baseline_file):
            raise FileNotFoundError(f"No such file: '{baseline_file}'")
        if not os.path.isfile(off_file):
            raise FileNotFoundError(f"No such file: '{off_file}'")
        if not os.path.isfile(corner_file):
            raise FileNotFoundError(f"No such file: '{corner_file}'")
        if not os.path.isfile(corner_full_file):
            raise FileNotFoundError(f"No such file: '{corner_full_file}'")
        if not os.path.isfile(cor_file):
            raise FileNotFoundError(f"No such file: '{cor_file}'")
        
        shutil.copy(par_file1, amp_par_file1)
        shutil.copy(par_file2, amp_par_file2)
        shutil.copy(base_perp_file,new_base_perp_file)
        shutil.copy(baseline_file,new_baseline_file)
        shutil.copy(off_file,new_off_file)
        shutil.copy(corner_file,new_corner_file)
        shutil.copy(corner_full_file,new_corner_full_file)
        shutil.copy(cor_file,new_cor_file)
                 
    
    return None

###########################################################################################

if __name__ == "__main__":
    main()

