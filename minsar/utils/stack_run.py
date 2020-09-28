#!/usr/bin/env python3
#####################################
#Author: Sara Mirzaee
# based on stackSentinel.py
#####################################
import os
import sys
import subprocess
from argparse import Namespace
import shutil
from minsar.utils.process_utilities import make_run_list
from minsar.objects.auto_defaults import PathFind
import contextlib
from minsar.objects import message_rsmas
import logging
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

pathObj = PathFind()
###########################################


class CreateRun:

    def __init__(self, inps):

        self.work_dir = inps.work_dir
        self.prefix = inps.prefix
        if inps.prefix == 'tops':
            self.workflow = inps.template['topsStack.workflow']
        self.geo_reference_dir = os.path.join(self.work_dir, pathObj.georeferencedir)
        self.minopy_dir = os.path.join(self.work_dir, pathObj.minopydir)

        self.inps = inps
        self.inps.custom_template_file = inps.custom_template_file

        self.command_options = []
        for item in inps.Stack_template:
            if item in ['useGPU', 'rmFilter', 'nofocus', 'zero', 'applyWaterMask']:
                if inps.Stack_template[item] in ['True', True]:
                    self.command_options.append('--' + item)
            elif item in ['bbox', 'swath_num']:
                self.command_options.append('--' + item)
                self.command_options.append('"{}"'.format(inps.Stack_template[item]))
            elif inps.Stack_template[item]:
                self.command_options.append('--' + item)
                self.command_options.append(inps.Stack_template[item])

        clean_list = pathObj.isce_clean_list()
        for item in clean_list[0]:
            if os.path.isdir(os.path.join(inps.work_dir, item)):
                shutil.rmtree(os.path.join(inps.work_dir, item))

        return

    def run_stack_workflow(self):        # This part is for isce stack run_files
               
        if self.prefix == 'tops':
            message_rsmas.log(self.work_dir, 'stackSentinel.py' + ' ' + ' '.join(self.command_options))
            cmd = 'export PATH=$ISCE_STACK/topsStack:$PATH; stackSentinel.py' + ' ' + ' '.join(self.command_options)

        else:
            message_rsmas.log(self.work_dir, 'stackStripMap.py' + ' ' + ' '.join(self.command_options))
            cmd = 'export PATH=$ISCE_STACK/stripmapStack:$PATH; stackStripMap.py' + ' ' + ' '.join(self.command_options)
        
        system_path = os.getenv('PATH')

        print (cmd)
        status = subprocess.Popen(cmd, shell=True).wait()
        if status is not 0:
             raise Exception('ERROR in create_runfiles.py')

        os.environ['PATH'] = system_path
        
        return

