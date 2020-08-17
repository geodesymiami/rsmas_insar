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
    knwon_issues_file = os.path.join(os.getenv('RSMASINSAR_HOME'), 'minsar/docs/known_issues.md')

    error_happened = False

    error_files = glob.glob(job_name + '*.e')
    for errfile in error_files:
        job_exit = [check_words_in_file(errfile, 'Segmentation fault'),
                    check_words_in_file(errfile, 'Aborted'),
                    check_words_in_file(errfile, 'ERROR'),
                    check_words_in_file(errfile, 'Error')]
        if np.array(job_exit).any():
            error_happened = True
            shutil.copy2(knwon_issues_file, project_dir)
            with open(knwon_issues_file, 'r') as f:
                known_issues = f.read()
            print(known_issues)

    putils.remove_zero_size_or_length_error_files(run_file=job_name)
    putils.raise_exception_if_job_exited(run_file=job_name)
    putils.concatenate_error_files(run_file=job_name, work_dir=project_dir)

    out_folder = work_dir + '/stdout_' + os.path.basename(inps.batch_job)
    if os.path.exists(out_folder):
        shutil.rmtree(out_folder)

    putils.move_out_job_files_to_stdout(run_file=job_name)

    if error_happened:
        raise RuntimeError('Error terminating job: {}'.format(inps.batch_job))

    return


if __name__ == "__main__":
    main()


