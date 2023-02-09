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
    parser.add_argument('--tmp', dest='copy_to_tmp', action='store_true', default=True,
                            help='modifies jobfiles in run_files_tmp')
    parser.add_argument('--no-tmp', dest='copy_to_tmp', action='store_false',
                            help="modifies jobfiles in run_files")

    inps = parser.parse_args(args=iargs)

    return inps


def main(iargs=None):

    inps = cmd_line_parser(iargs)
    work_dir = os.path.dirname(os.path.abspath(inps.job_files[0]))

    project_dir = os.path.dirname(work_dir)
    if inps.copy_to_tmp:
        run_files_dir=project_dir + '/run_files_tmp'
    else:
        run_files_dir=project_dir + '/run_files'

    if 'miaplpy' in project_dir:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(project_dir)))

    known_issues_file = os.path.join(os.getenv('RSMASINSAR_HOME'), 'docs/known_issues.md')

    error_happened = False
    data_problems_strings_out_files = [
                    'There appears to be a gap between slices. Cannot stitch them successfully',
                    'SLCs are sliced differently with different versions of the processor',
                    'No annotation xml file found in zip file',
                    'mismatched tag: line 77, column 6',
                    'no element found: line',
                    'not well-formed (invalid token)'
                    ]
    data_problems_strings_error_files = [
                    'does not exist in the file system, and is not recognized as a supported dataset name'
                    ]
    data_problems_strings_run_04 = [
                    'FileNotFoundError: [Errno 2] No such file or directory:'
                    ]
    different_number_of_bursts_string = [
                    'has different number of bursts',
                    ]
    error_strings = [
                    'Segmentation fault',
                    'Bus',
                    'Aborted',
                    #'ERROR',          FA 11/21:  commented because
                    ' Error',
                    'FileNotFoundError',
                    'IOErr',
                    'Traceback',
                    'stripmapWrapper.py: command not found'
                    ]
                    #'Exiting ...',                # remove if above works fine (5/21)
                    #'FileNotFoundError: [Errno 2] No such file or directory: '/tmp/secondarys/20190917/IW2.xml'
# Explanation 11/2021 for 'ERROR' removal from error_strings
# The data problem error message below appeared in a run_02*.e file.  I therefore separated into  data_problems_strings_out_files and data_problems_strings_error_files.
# I had to remove 'ERROR' as `ERROR 4` remains in an run_*.e file it still raises an exception. 
# If `ERROR` needs to be in `error_strings` an alternative could be to remove the problem run_02*.e file 
# ERROR 4: `/vsizip/S1A_IW_SLC__1SDV_20161115T141647_20161115T141714_013954_016796_D68D.zip/S1A_IW_SLC__1SDV_20161115T141647_20161115T141714_013954_016796_D68D.SAFE/measurement/s1a-iw2-slc-vv-20161115t141647-20161115t141712-013954-016796-005.tiff' does not exist in the file system, and is not recognized as a supported dataset name.
# FA 12/22: same error message ca be productde by miaplpy_load_data (changed to "if 'unpack_secondary_slc' in job_name or or 'miaplpy_generate_ifgram' in job_name:")
    miaplpy_error_strings = [
                    'ERROR 4: ',
                    'NaN or infinity found in input float data',
                    'Traceback'
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
       if 'filter_coherence' in job_name or 'run_09_igram' in job_name or 'miaplpy_generate_ifgram' in job_name:               # run_09_igram is for stripmap
           putils.remove_line_counter_lines_from_error_files(run_file=job_name)

       # 5/21: sometimes not working. Move before loop using run_file_base ??
       putils.remove_zero_size_or_length_error_files(run_file=job_name)
       putils.remove_launcher_message_from_error_file(run_file=job_name)
       putils.remove_ssh_warning_message_from_error_file(run_file=job_name)
       putils.remove_zero_size_or_length_error_files(run_file=job_name)
       putils.remove_timeout_error_files(run_file=job_name)

       # analyze *.e and *.o files
       error_files = natsorted( glob.glob(job_name + '*.e') )
       out_files = natsorted( glob.glob(job_name + '*.o') )

       # FA 12/22:  add miaplpy_load_data here (and remove below) once miaplpyApp.py supports run_files_tmp`
       #if 'unpack_secondary_slc' in job_name or 'miaplpy_load_data' in job_name:               
       if 'unpack_secondary_slc' in job_name:               
          for file in out_files:
              for string in data_problems_strings_out_files:
                  if check_words_in_file(file, string):
                      date = file.split("_")[-2]
                      print( 'WARNING: \"' + string + '\" found in ' + os.path.basename(file) + ': removing ' + date + ' from run_files ')
                      putils.run_remove_date_from_run_files(run_files_dir=run_files_dir, date=date, start_run_file = 3 )
                      with open(run_files_dir + '/removed_dates.txt', 'a') as rd:
                          rd.writelines('run_02: removing ' + date + ', \"' + string + '\" found in ' + os.path.basename(file) + ' \n')
                      num_lines = sum(1 for line in open(run_files_dir + '/removed_dates.txt'))
          for file in error_files:
              for string in data_problems_strings_error_files:
                  if check_words_in_file(file, string):
                      date = file.split("_")[-2]
                      print( 'WARNING: \"' + string + '\" found in ' + os.path.basename(file) + ': removing ' + date + ' from run_files ')
                      putils.run_remove_date_from_run_files(run_files_dir=run_files_dir, date=date, start_run_file = 3 )
                      with open(run_files_dir + '/removed_dates.txt', 'a') as rd:
                          rd.writelines('run_02: removing ' + date + ', \"' + string + '\" found in ' + os.path.basename(file) + ' \n')

          try: 
              num_lines = sum(1 for line in open(run_files_dir + '/removed_dates.txt'))
              if (num_lines >= 10):
                 shutil.copy(run_files_dir + '/removed_dates.txt', project_dir + '/out_' + os.path.basename(job_name) + '.e')
                 raise RuntimeError('Too many bad data: ', num_lines)
          except:
               pass

       # this covers missing frames: run_files are generated although a frame in the middle is missing
       if 'fullBurst_geo2rdr' in job_name:               
          for file in error_files:
              for string in data_problems_strings_run_04:
                  if check_words_in_file(file, string):
                      date = file.split("_")[-2]
                      print( 'WARNING: \"' + string + '\" found in ' + os.path.basename(file) + ': removing ' + date + ' from run_files ')
                      putils.run_remove_date_from_run_files(run_files_dir=run_files_dir, date=date, start_run_file = 5 )
                      secondary_date_dir = project_dir + '/coreg_secondarys/' + date
                      try:
                         shutil.rmtree(secondary_date_dir)
                      except:
                         pass
                      with open(run_files_dir + '/removed_dates.txt', 'a') as rd:
                          rd.writelines('run_04: removing ' + date + ', \"' + string + '\" found in ' + os.path.basename(file) + ' \n')
                          rd.writelines('run_04: removing directory ' + secondary_date_dir + ' \n')

                      out_dir = run_files_dir + '/stdout_run_04_fullBurst_geo2rdr'
                      os.makedirs(out_dir, exist_ok=True)
                      shutil.move(file, out_dir + '/' + os.path.basename(file))
                      error_files.remove(file)

       if 'extract_stack_valid_region' in job_name:               
          for file in out_files:
              string = different_number_of_bursts_string[0]
              if check_words_in_file(file, string):
                 #matched_data_problem_strings.append('Warning: \"' + string + '\" found in ' + file + '\n')
                 print( 'Warning: \"' + string + '\" found in ' + file )
                 with open(file) as fo:
                      problem_dates=[]
                      lines = fo.readlines()
                      for line in lines:
                          if 'WARNING:' in line:
                              date = line.split(' ')[1]
                              problem_dates.append(date)
                 
                 problem_dates = list(set(problem_dates))
                 problem_dates = natsorted(problem_dates)
                 for date in problem_dates:
                      print( 'WARNING: \"' + string + '\" found in ' + os.path.basename(file) + ': removing ' + date + ' from run_files ')
                      putils.run_remove_date_from_run_files(run_files_dir=run_files_dir, date=date, start_run_file = 7 )
                      with open(run_files_dir + '/removed_dates.txt', 'a') as rd:
                          rd.writelines('run_06: removing ' + date + ', \"' + string + '\" found in ' + os.path.basename(file) + ' \n')

                 # exit if too many removed dates
                 num_lines = sum(1 for line in open(run_files_dir + '/removed_dates.txt'))
                 if (num_lines >= 30):
                    #shutil.copy(run_files_dir + '/removed_dates.txt', project_dir + '/out_run_06_removed_dates.txt')
                    shutil.copy(run_files_dir + '/removed_dates.txt', project_dir + '/out_' + os.path.basename(job_name) + '.e')
                    raise RuntimeError('Too many dates with missing bursts (limit is 30): ', num_lines)

       for file in error_files + out_files:
           for error_string in error_strings:
               if check_words_in_file(file, error_string):
                   if skip_error(file, error_string):
                       break
                   matched_error_strings.append('Error: \"' + error_string + '\" found in ' + file + '\n')
                   print( 'Error: \"' + error_string + '\" found in ' + file )

       # FA 12/22: this covers the following data problem error (move to run_02 above once miaplpyApp supports run_files_tmp)
       # ERROR 4: `/vsizip//scratch/05861/tg851601/MiamiSenAT48/SLC/S1A_IW_SLC__1SDV_20150921T232737_20150921T232806_007820_00AE3B_0A60.zip/S1A_IW_SLC__1SDV_20150921T232737_20150921T232806_007820_00AE3B_0A60.SAFE/
       # measurement/s1a-iw3-slc-vv-20150921t232739-20150921t232806-007820-00ae3b-006.tiff' does not exist in the file system, and is not recognized as a supported dataset name.
       if 'miaplpy' in job_name:
           for file in error_files + out_files:
               for error_string in miaplpy_error_strings:          # FA 12/22  We need to do this check only for run_05_miaplpy_unwrap_ifgram
                   if check_words_in_file(file, error_string):
                       if skip_error(file, error_string):
                           break
                       matched_error_strings.append('Error: \"' + error_string + '\" found in ' + file + '\n')
                       print( 'Error: \"' + error_string + '\" found in ' + file )

    if len(matched_data_problem_strings) != 0:
        with open(run_file_base + '_data_problem_matches.e', 'w') as f:
            f.write(''.join(matched_data_problem_strings))
    elif len(matched_error_strings) != 0:
        with open(run_file_base + '_error_matches.e', 'w') as f:
            f.write(''.join(matched_error_strings))
    else:
        print("no error found")
        
    if 'run_' in job_name:
       putils.concatenate_error_files(run_file=run_file_base, work_dir=project_dir)
    else:
       out_error_file = project_dir + '/out_' + os.path.basename(job_name) + '.e'
       if len(error_files) == 0:
           Path(out_error_file).touch()
       else:
           shutil.copy(error_files[-1], out_error_file)

    # exit for errors
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
       #if '--- Logging error ---' in lines or '---Loggingerror---' in lines:
       # 2/23: thought I need to add 'DUE TO TIME LIMIT' but files containing this string are removed earlier
       # 2/23: added string to skip unexplained dask error which does not appear fatal
       if '--- Logging error ---' in lines or '---Loggingerror---' in lines or 'distributed.comm.core.CommClosedError: in <TCP' in lines:
            skip = True


    return skip

if __name__ == "__main__":
    main()


