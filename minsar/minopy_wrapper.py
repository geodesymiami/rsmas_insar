#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
import sys
import glob
import argparse
import time

import minopy
import minopy.workflow
import minopy_utilities as mnp
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar import email_results
import minsar.job_submission as js

pathObj = PathFind()

###########################################################################################
step_list, step_help = pathObj.minopy_help()
EXAMPLE = """example: 
      minopy_wrapper.py  <customTemplateFile>              # run with default and custom templates
      minopy_wrapper.py  <customTemplateFile>  --submit    # submit as job
      minopy_wrapper.py  -h / --help                       # help 
      minopy_wrapper.py  -H                                # print    default template options
      # Run with --start/stop/step options
      minopy_wrapper.py GalapagosSenDT128.template --step  crop         # run the step 'download' only
      minopy_wrapper.py GalapagosSenDT128.template --start crop         # start from the step 'download' 
      minopy_wrapper.py GalapagosSenDT128.template --stop  unwrap       # end after step 'interferogram'
      """


def minopy_wrapper_cmd_line_parse(iargs=None):

    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(description='MiNoPy Routine Non-Linear Inversion processing',
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=EXAMPLE)

    parser = mnp.add_common_parser(parser)
    parser = mnp.add_minopy_wrapper(parser)
    inps = parser.parse_args(args=iargs)
    inps = putils.create_or_update_template(inps)

    return inps


def main(iargs=None):

    inps = minopy_wrapper_cmd_line_parse(iargs)

    configs = putils.get_config_defaults(config_file='job_defaults.cfg')

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_file_name = 'minopy_wrapper'

        if inps.wall_time == 'None':
            inps.wall_time = configs[job_file_name]['walltime']

        job_name = inps.customTemplateFile.split(os.sep)[-1].split('.')[0]

        js.submit_script(job_name, job_file_name, sys.argv[:], inp.work_dir, inps.wall_time)
        sys.exit(0)

    os.chdir(inps.work_dir)

    inps.minopy_dir = os.path.join(inps.work_dir, pathObj.minopydir)

    if inps.remove_minopy_dir:
        putils.remove_directories(directories_to_delete=[inps.minopy_dir])

    # check input --start/end/step
    for key in ['startStep', 'endStep', 'step']:
        if key in vars(inps):
            value = vars(inps)[key]
            if value and value not in step_list:
                msg = 'Input step not found: {}'.format(value)
                msg += '\nAvailable steps: {}'.format(step_list)
                raise ValueError(msg)

    # ignore --start/end input if --step is specified
    if 'step' in vars(inps):
        inps.startStep = inps.step
        inps.endStep = inps.step

    # get list of steps to run
    if not 'startStep' in vars(inps):
        inps.startStep = step_list[0]
    if not 'endStep' in vars(inps):
        inps.endStep = step_list[-1]

    idx0 = step_list.index(inps.startStep)
    idx1 = step_list.index(inps.endStep)
    if idx0 > idx1:
        msg = 'input start step "{}" is AFTER input end step "{}"'.format(inps.startStep, inps.endStep)
        raise ValueError(msg)
    inps.runSteps = step_list[idx0:idx1 + 1]

    print('Run routine processing with {} on steps: {}'.format(os.path.basename(__file__), inps.runSteps))
    if len(inps.runSteps) == 1:
        print('Remaining steps: {}'.format(step_list[idx0 + 1:]))

    print('-' * 50)

    objInv = NoLI(inps)
    objInv.run(steps=inps.runSteps, config=configs)

    return None

###########################################################################################


class NoLI:
    """ Routine processing workflow for time series analysis of small baseline InSAR stacks
    """

    def __init__(self, inps):
        self.customTemplateFile = inps.customTemplateFile
        self.work_dir = inps.work_dir
        self.run_dir = os.path.join(inps.work_dir, pathObj.rundir)
        self.cwd = os.path.abspath(os.getcwd())
        self.minopy_dir = inps.minopy_dir

        return

    def run_crop(self):
        """ Cropping images using crop_sentinel.py script.
        """
        minopy.crop_sentinel.main([self.customTemplateFile, '--submit'])
        return

    def run_create_patch(self):
        """ Dividing the area into patches.
        """
        minopy.create_patch.main([self.customTemplateFile, '--submit'])
        return

    def run_phase_linking(self):
        """ Non-Linear phase inversion.
        """
        minopy.phase_linking_app.main([self.customTemplateFile])
        return

    def run_interferogram(self, config):
        """ Export single master interferograms
        """
        run_file_int = os.path.join(self.run_dir, 'run_single_master_interferograms')
        step_name = 'single_master_interferograms'
        try:
            memorymax = config[step_name]['memory']
        except:
            memorymax = config['DEFAULT']['memory']

        try:
            if config[step_name]['adjust'] == 'True':
                walltimelimit = putils.walltime_adjust(inps, config[step_name]['walltime'])
            else:
                walltimelimit = config[step_name]['walltime']
        except:
            walltimelimit = config['DEFAULT']['walltime']

        queuename = os.getenv('QUEUENAME')

        putils.remove_last_job_running_products(run_file=run_file_int)

        jobs = js.submit_batch_jobs(batch_file=run_file_int, out_dir=self.run_dir,
                                    work_dir=self.work_dir, memory=memorymax, walltime=walltimelimit,
                                    queue=queuename)

        putils.remove_zero_size_or_length_error_files(run_file=run_file_int)
        putils.raise_exception_if_job_exited(run_file=run_file_int)
        putils.concatenate_error_files(run_file=run_file_int, work_dir=self.work_dir)
        putils.move_out_job_files_to_stdout(run_file=run_file_int)

        return

    def run_unwrap(self, config):
        """ Unwrapps single master interferograms
        """
        run_file_int = os.path.join(self.run_dir, 'run_unwrap')
        step_name = 'unwrap'
        try:
            memorymax = config[step_name]['memory']
        except:
            memorymax = config['DEFAULT']['memory']

        try:
            if config[step_name]['adjust'] == 'True':
                walltimelimit = putils.walltime_adjust(inps, config[step_name]['walltime'])
            else:
                walltimelimit = config[step_name]['walltime']
        except:
            walltimelimit = config['DEFAULT']['walltime']

        queuename = os.getenv('QUEUENAME')

        putils.remove_last_job_running_products(run_file=run_file_int)

        jobs = js.submit_batch_jobs(batch_file=run_file_int, out_dir=self.run_dir,
                                    work_dir=self.work_dir, memory=memorymax, walltime=walltimelimit,
                                    queue=queuename)

        putils.remove_zero_size_or_length_error_files(run_file=run_file_int)
        putils.raise_exception_if_job_exited(run_file=run_file_int)
        putils.concatenate_error_files(run_file=run_file_int, work_dir=self.work_dir)
        putils.move_out_job_files_to_stdout(run_file=run_file_int)

        return

    def run_mintpy(self):
        """ Time series corrections
        """

        minopy.timeseries_corrections.main([self.customTemplateFile, '--submit'])
        return

    def run_email_results(self):
        """ Time series corrections
        """

        email_results.main([self.customTemplateFile])
        return

    def run(self, steps, config):
        # run the chosen steps
        for sname in steps:

            print('\n\n******************** step - {} ********************'.format(sname))

            if sname == 'crop':
                self.run_crop()

            elif sname == 'patch':
                self.run_create_patch()

            elif sname == 'inversion':
                self.run_phase_linking()

            elif sname == 'ifgrams':
                self.run_interferogram(config)

            elif sname == 'unwrap':
                self.run_unwrap(config)

            elif sname == 'mintpy':
                self.run_mintpy()

            elif sname == 'email':
                self.run_email_results()

        # message
        msg = '\n###############################################################'
        msg += '\nNormal end of Non-Linear time series processing workflow!'
        msg += '\n##############################################################'
        print(msg)
        return

###########################################################################################


if __name__ == "__main__":
    main()


