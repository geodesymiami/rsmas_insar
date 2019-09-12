#!/usr/bin/env python3
#####################################
#Author: Sara Mirzaee
# based on stackSentinel.py
#####################################

import os
import sys
from argparse import Namespace
import shutil
from minsar.objects.stack_rsmas import rsmasRun
from minsar.utils.process_utilities import make_run_list
from minsar.objects.auto_defaults import PathFind
import contextlib
from minsar.objects import message_rsmas

stack_prefix = os.path.basename(os.getenv('ISCE_STACK'))
if stack_prefix == 'topsStack':
    import stackSentinel as StSc
else:
    import stackStripMap as StSc

pathObj = PathFind()
###########################################


class CreateRun:

    def __init__(self, inps):

        self.work_dir = inps.work_dir
        self.workflow = inps.template[stack_prefix + '.workflow']
        self.geo_master_dir = os.path.join(self.work_dir, pathObj.geomasterdir)
        self.minopy_dir = os.path.join(self.work_dir, pathObj.minopydir)

        self.inps = inps
        self.inps.custom_template_file = inps.custom_template_file

        self.command_options = []

        flag_options = ['useGPU', 'zero', 'nofocus']
        for item in inps.stack_template:
            if item in flag_options:
                if inps.stack_template[item] == 'True':
                    self.command_options = self.command_options + ['--' + item]
            elif not inps.stack_template[item] is None:
                self.command_options = self.command_options + ['--' + item] + [inps.stack_template[item]]

        clean_list = pathObj.isce_clean_list()
        for item in clean_list[0]:
            if os.path.isdir(os.path.join(inps.work_dir, item)):
                shutil.rmtree(os.path.join(inps.work_dir, item))        

        return

    def run_stack_workflow(self):        # This part is for isceStack run_files
        
        if stack_prefix == 'topsStack': 
            stack_script = 'stackSentinel'
            message_rsmas.log(self.work_dir, 'stackSentinel.py' + ' ' + ' '.join(self.command_options))
        else:
            stack_script = 'stackStripMap'
            message_rsmas.log(self.work_dir, 'stackStripMap.py' + ' ' + ' '.join(self.command_options))

        try:
            with open('out_{}.o'.format(stack_script), 'w') as f:
                with contextlib.redirect_stdout(f):
                    StSc.main(self.command_options)
        except:
            with open('out_{}.e'.format(stack_script), 'w') as g:
                with contextlib.redirect_stderr(g):
                    StSc.main(self.command_options)

        return

    def run_post_stack(self):

        inps = self.inps

        if inps.template['processingMethod'] == 'minopy' or inps.template['{}.workflow'.format(stack_prefix)] == 'slc':

            if not os.path.exists(self.minopy_dir):
                os.mkdir(self.minopy_dir)

            os.chdir(self.minopy_dir)

            inps_stack = StSc.cmdLineParse(self.command_options)
            acquisitionDates, stackMasterDate, slaveDates = StSc.get_dates(inps_stack)

            pairs_sm = []

            for i in range(len(acquisitionDates) - 1):
                pairs_sm.append((acquisitionDates[0], acquisitionDates[i + 1]))

            runObj = rsmasRun()
            runObj.configure(inps, 'run_single_master_interferograms')
            runObj.generateIfg(inps, pairs_sm)
            runObj.finalize()

            runObj = rsmasRun()
            runObj.configure(inps, 'run_unwrap')
            runObj.unwrap(inps, pairs_sm)
            runObj.finalize()

        return




