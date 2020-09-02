#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
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
    parser.add_argument('batch_job', nargs='?', help='batch job name:\n')
    inps = parser.parse_args(args=iargs)

    return inps


def main(iargs=None):

    inps = cmd_line_parser(iargs)
    work_dir = os.path.dirname(os.path.abspath(inps.batch_job))
    project_dir = os.path.dirname(work_dir)
    job_name = inps.batch_job.split('.')[0]
    known_issues_file = os.path.join(os.getenv('RSMASINSAR_HOME'), 'minsar/docs/known_issues.md')

    error_happened = False
    error_strings  = [
                    'Segmentation fault',
                    'Aborted',
                    'ERROR',
                    'Error',
                    'FileNotFoundError',
                    'IOErr',
                    'Bus',
                    'Exiting ...'
                   ]

    error_files = glob.glob(job_name + '*.e')
    out_files = glob.glob(job_name + '*.o')
    for file in error_files + out_files:
        job_exits = []
        for error_string in error_strings:
            job_exits.append(check_words_in_file(file, error_string))
        if np.array(job_exits).any():
            print('ERROR: String \"' + error_string + '\" occurs in ' + file)
            print('For known issues see https://github.com/geodesymiami/rsmas_insar/blob/master/minsar/docs/known_issues.md')
            raise RuntimeError('Error in job: {}'.format(inps.batch_job))

    #putils.remove_zero_size_or_length_error_files(run_file=job_name)
    #putils.raise_exception_if_job_exited(run_file=job_name)
    #putils.concatenate_error_files(run_file=job_name, work_dir=project_dir)

    out_folder = work_dir + '/stdout_' + os.path.basename(inps.batch_job)
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    putils.move_out_job_files_to_stdout(run_file=job_name)

    return


if __name__ == "__main__":
    main()


