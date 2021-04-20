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

    job_file = inps.job_files[0]
    job_name = job_file.split('.')[0]
    job_files = inps.job_files

    if 'run_' in job_name:
        run_file = '_'.join(job_name.split('_')[:-1])
    else:
        run_file = job_name

    matched_error_strings = []
    for job_file in job_files:
       print('checking *.e, *.o from: ' + job_file)
       job_name = job_file.split('.')[0]

       if 'filter_coherence' in job_name:
           putils.remove_line_counter_lines_from_error_files(run_file=job_name)

       if 'run_' in job_name:
           putils.remove_launcher_message_from_error_file(run_file=job_name)
       
       if 'run_' in job_name:
           putils.remove_zero_size_or_length_error_files(run_file=job_name)
       
       error_files = glob.glob(job_name + '*.e')
       out_files = glob.glob(job_name + '*.o')
       error_files = natsorted(error_files)
       out_files = natsorted(out_files)

       for file in error_files + out_files:
           for error_string in error_strings:
               if check_words_in_file(file, error_string):
                   if skip_error(file, error_string):
                       break
                   matched_error_strings.append('Error: \"' + error_string + '\" found in ' + file + '\n')
                   print( 'Error: \"' + error_string + '\" found in ' + file )

    if len(matched_error_strings) != 0:
        with open(run_file + '_error_matches.e', 'w') as f:
            f.write(''.join(matched_error_strings))
    else:
        print("no error found")
        
    if 'run_' in job_name:
         putils.concatenate_error_files(run_file=run_file, work_dir=project_dir)
    else:
         out_error_file = os.path.dirname(error_files[-1]) + '/out_' + os.path.basename(error_files[-1])
         shutil.copy(error_files[-1], out_error_file)

    if len(matched_error_strings) != 0:
        print('For known issues see https://github.com/geodesymiami/rsmas_insar/tree/master/docs/known_issues.md')
        raise RuntimeError('Error in run_file: ' + run_file)

    # move only if there was no error
    if len(os.path.dirname(run_file))==0:
       run_file = os.getcwd() + '/' + run_file
    putils.move_out_job_files_to_stdout(run_file=run_file)

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


