#!/usr/bin/env python3
########################
# Authors: Sara Mirzaee, Falk Amelung
#######################
import argparse
import os
from minsar.job_submission import check_words_in_file
import minsar.utils.process_utilities as putils
import numpy as np
import shutil
import glob


def cmd_line_parser(iargs=None):

    parser = argparse.ArgumentParser(description='Check job outputs')
    parser.add_argument('job_files', nargs='+', type=str, help='batch job name:\n')
    inps = parser.parse_args(args=iargs)

    return inps


def main(iargs=None):

    inps = cmd_line_parser(iargs)
    work_dir = os.path.dirname(os.path.abspath(inps.job_files[0]))
    project_dir = os.path.dirname(work_dir)
    known_issues_file = os.path.join(os.getenv('RSMASINSAR_HOME'), 'docs/known_issues.md')

    error_happened = False
    error_strings  = [
                    'No annotation xml file found in zip file',
                    'There appears to be a gap between slices. Cannot stitch them successfully',
                    'no element found: line',
                    'Exiting ...',
                    'Segmentation fault',
                    'Bus',
                    'Aborted',
                    'ERROR',
                    'Error',
                    'FileNotFoundError',
                    'IOErr',
                    'Traceback'
                   ]


    for job_file in inps.job_files:
       print('checking:  ' + job_file)
       job_name = job_file.split('.')[0]
       error_files = glob.glob(job_name + '*.e')
       out_files = glob.glob(job_name + '*.o')

       for file in error_files + out_files:
           job_exits = []
           for error_string in error_strings:
               job_exits.append(check_words_in_file(file, error_string))
               if np.array(job_exits).any():
                   print('For known issues see https://github.com/geodesymiami/rsmas_insar/tree/master/docs/known_issues.md')
                   raise RuntimeError('Error: \"' + error_string + '\" found in ' + file)

       putils.remove_zero_size_or_length_error_files(run_file=job_name)

    print("no error found")
    run_file = '_'.join(job_name.split('_')[:-1])
    putils.concatenate_error_files(run_file=run_file, work_dir=project_dir)

    out_folder = work_dir + '/stdout_' + os.path.basename(run_file)
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    putils.move_out_job_files_to_stdout(run_file=job_name)

    return

if __name__ == "__main__":
    main()


