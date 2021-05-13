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
from pathlib import Path
from natsort import natsorted


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
    error_strings = [
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
    different_number_of_bursts_string = [
                    'has different number of bursts',
                    ]

    job_names=[]
    for job_file in inps.job_files:
        tmp=job_file.split('.')
        job_names.append('.'.join(tmp[0:-1]))

    job_file = inps.job_files[0]
    job_name = job_names[0]

    if 'run_' in job_name:
        run_file_base = '_'.join(job_name.split('_')[:-1])
    else:
        run_file_base = job_name

    matched_error_strings = []
    matched_data_problem_strings = []
    for job_name in job_names:
       print('checking *.e, *.o from ' + job_name + '.job')

       # preprocess *.e files
       if 'filter_coherence' in job_name or 'run_09_igram' in job_name:               # run_09_igram is for stripmap
           putils.remove_line_counter_lines_from_error_files(run_file=job_name)

       # 5/21: sometimes not working. Move before loop using run_file_base ??
       putils.remove_zero_size_or_length_error_files(run_file=job_name)
       putils.remove_launcher_message_from_error_file(run_file=job_name)
       putils.remove_zero_size_or_length_error_files(run_file=job_name)
       putils.remove_timeout_error_files(run_file=job_name)

       # analyze *.e and *.o files
       error_files = natsorted( glob.glob(job_name + '*.e') )
       out_files = natsorted( glob.glob(job_name + '*.o') )

       if 'extract_stack_valid_region' in job_name:               
          for file in out_files:
              string = different_number_of_bursts_string[0]
              if check_words_in_file(file, string):
                 matched_data_problem_strings.append('Warning: \"' + string + '\" found in ' + file + '\n')
                 print( 'Warning: \"' + string + '\" found in ' + file )

       for file in error_files + out_files:
           for error_string in error_strings:
               if check_words_in_file(file, error_string):
                   if skip_error(file, error_string):
                       break
                   matched_error_strings.append('Error: \"' + error_string + '\" found in ' + file + '\n')
                   print( 'Error: \"' + error_string + '\" found in ' + file )

    if len(matched_error_strings) != 0:
        with open(run_file_base + '_error_matches.e', 'w') as f:
            f.write(''.join(matched_error_strings))
    else:
        print("no known error found")

    if len(matched_data_problem_strings) != 0:
        with open(run_file_base + '_data_problem_matches.e', 'w') as f:
            f.write(''.join(matched_data_problem_strings))
    else:
        print("no known data problem found")
        
    if 'run_' in job_name:
       putils.concatenate_error_files(run_file=run_file_base, work_dir=project_dir)
    else:
       out_error_file = os.path.dirname(error_files[-1]) + '/out_' + os.path.basename(error_files[-1])
       #Path(out_error_file)
       shutil.copy(error_files[-1], out_error_file)

    if len(matched_error_strings) + len(matched_data_problem_strings) != 0:
        print('For known issues see https://github.com/geodesymiami/rsmas_insar/tree/master/docs/known_issues.md')
        raise RuntimeError('Error in run_file: ' + run_file_base)

    # move only if there was no error
    if len(os.path.dirname(run_file_base))==0:
       run_file = os.getcwd() + '/' + run_file_base
    putils.move_out_job_files_to_stdout(run_file=run_file_base)

    return

def skip_error(file, error_string):
    """ skip error for merge_reference step if contains has different number of bursts (7) than the reference (9)  """
    """ https://github.com/geodesymiami/rsmas_insar/issues/436  """
    """ prior to https://github.com/isce-framework/isce2/pull/195 it did not raise exception  """

    skip = False
    if 'merge_reference_secondary_slc' in file or 'merge_burst_igram' in file:
       with open(file) as f:
        lines=f.read()
        if 'has different number of bursts' in lines and 'than the reference' in lines:
           skip = True

    with open(file) as f:
       lines=f.read()
       if '--- Logging error ---' in lines or '---Loggingerror---' in lines:
            skip = True


    return skip

if __name__ == "__main__":
    main()


