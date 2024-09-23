#!/usr/bin/env python3

import os
import sys
import re
import glob
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
from minsar.job_submission import JOB_SUBMIT

# pathObj = PathFind()
inps = None

##############################################################################
EXAMPLE = """example:
    ssara_listing_2_burst2safe_jobfile.py SLC/ssara_listing.txt --extent -91.24 -0.96 -91.08 -0.711

    Creates runfile for burst2stack for each acquisition. burst2stack or burst2safe creates *SAFE files from downloaded bursts. 
    This uses burst2stack because it seems to check for file existence before download what burst2safe does not seem
    to do  (I tried burst2safe --orbit but it always seems to download).  burst2safe requires --extent option. 

 """

DESCRIPTION = ("""
     Creates runfile and jobfile for burst2safe (run after downloading bursts)
""")

def create_parser():
    synopsis = 'Create run_file'
    parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EXAMPLE, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('ssara_listing_path', help='file name\n')
    parser.add_argument('--extent', required=True, type=str, nargs=4, metavar=('W', 'S', 'E', 'N'), help='Bounds in lat/lon describing spatial extent')
    parser.add_argument("--queue", dest="queue", metavar="QUEUE", help="Name of queue to submit job to")

    inps = parser.parse_args()

    inps.ssara_listing_path = Path(inps.ssara_listing_path).resolve()
    
    return inps

###############################################


def main(iargs=None):

    # parse
    inps = create_parser()

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(os.getcwd(), os.path.basename(__file__) + ' ' + ' '.join(input_arguments))


    inps.work_dir = os.getcwd()

    run_01_burst2safe_path = Path(inps.ssara_listing_path).resolve().with_name('run_01_burst2safe')

    absolute_orbits = []
    dates = []

    with open(inps.ssara_listing_path, 'r') as file:
        for line in file:
            if line.startswith("ASF"):
                parts = line.split(',')
                absolute_orbits.append(parts[2])
                date_time = parts[3]  # Extract the date-time string
                date = date_time.split('T')[0]  # Split at 'T' and take the first part (the date)
                dates.append(date)
    relative_orbit = (int(absolute_orbits[0]) - 73) % 175 + 1
    unique_dates = list(set(dates))
    dates = unique_dates
    
    dir = os.path.dirname(inps.ssara_listing_path)

    with open(run_01_burst2safe_path, 'w') as file:
        for orbit in absolute_orbits:
            command = f'cd {str(dir)}; burst2safe --orbit {orbit} --extent {" ".join(inps.extent)}\n'
            file.write(command)
    print("Created: ", run_01_burst2safe_path)

    with open(run_01_burst2safe_path, 'w') as file:
        for date in dates:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            new_date_obj = date_obj + timedelta(days=1)
            new_date = new_date_obj.strftime("%Y-%m-%d")
            command = f'cd {str(dir)}; burst2stack --rel-orbit {relative_orbit} --start-date {date} --end-date {new_date} --keep-files --all-anns --extent {" ".join(inps.extent)}\n'
            file.write(command)
    print("Created: ", run_01_burst2safe_path)
    
    # find *template file (needed currently for run_workflow.bash)
    current_directory = Path(os.getcwd())
    parent_directory = current_directory.parent
    template_files_current = glob.glob(str(current_directory / '*.template'))
    template_files_parent = glob.glob(str(parent_directory / '*.template'))
    template_files = template_files_current + template_files_parent
    if template_files:
        inps.custom_template_file = template_files[0]
    else:
        raise FileNotFoundError("No file found ending with *template")

    inps.out_dir = dir
    inps.num_data = 1
    job_obj = JOB_SUBMIT(inps)  
    job_obj.write_batch_jobs(batch_file = str(run_01_burst2safe_path) )

###############################################
if __name__ == "__main__":
    main()