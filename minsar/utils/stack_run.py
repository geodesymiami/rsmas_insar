#!/usr/bin/env python3
#####################################
#Author: Sara Mirzaee
# based on stackSentinel.py
#####################################

import os
import sys
import numpy as np
import datetime
from argparse import Namespace
import shutil
from stackSentinel import *
from Stack import sentinelSLC
from matplotlib.path import Path as Path
from minsar.objects.stack_rsmas import rsmasRun
from minsar.utils.process_utilities import make_run_list
from minsar.objects.auto_defaults import PathFind

pathObj = PathFind()
###########################################


def run_download(inps):

    if os.path.exists(os.path.join(inps.work_dir, pathObj.rundir)):
        shutil.rmtree(os.path.join(inps.work_dir, pathObj.rundir))
        configdir = os.path.join(inps.work_dir, pathObj.configdir)
        if os.path.isdir(configdir):
            shutil.rmtree(configdir)

    cleanlist = pathObj.isce_clean_list()
    for item in cleanlist[0]:
        if os.path.isdir(os.path.join(inps.work_dir, item)):
            shutil.rmtree(os.path.join(inps.work_dir, item))

    i = 0
    runObj = rsmasRun()
    runObj.configure(inps, 'run_' + str(i) + "_download_data_and_dem")
    runObj.downloadDataDEM(inps)
    runObj.finalize()

    return

##############################################


class CreateRun:

    def __init__(self, inps):

        self.work_dir = inps.work_dir
        self.workflow = inps.template['workflow']
        self.geo_master_dir = os.path.join(self.work_dir, pathObj.geomasterdir)
        self.squeesar_dir = os.path.join(self.work_dir, pathObj.squeesardir)

        self.inps = Namespace(**inps.template)
        self.inps.customTemplateFile = inps.customTemplateFile

        clean_list = pathObj.isce_clean_list()
        for item in clean_list[0]:
            if os.path.isdir(os.path.join(inps.work_dir, item)):
                shutil.rmtree(os.path.join(inps.work_dir, item))
                
        if os.path.exists(os.path.join(inps.work_dir, pathObj.rundir)):
            del_command = 'find {} -type f -not -name {} -delete'.format(os.path.join(inps.work_dir, pathObj.rundir), '"run_0_*"')
            os.system(del_command)

        if self.workflow not in ['interferogram', 'offset', 'correlation', 'slc', 'fmratecorrection']:
            print('')
            print('**************************')
            print('Error: workflow ', self.workflow, ' is not valid.')
            print('Please choose one of these workflows: interferogram, offset, correlation, slc')
            print('Use argument "-W" or "--workflow" to choose a specific workflow.')
            print('**************************')
            print('')
            sys.exit(1)

        if self.workflow == 'fmratecorrection':
            self.coregistration = 'geometry'
            print('')
            print('**************************')
            print('NOTE: fmrate correction procedure only compatible with geometry coregistration.')
            print('')
            print('**************************')
        else:
            self.coregistration = inps.template['coregistration']
            
        [self.acquisitionDates, self.stackMasterDate, self.slaveDates, self.safe_dict, self.updateStack] = checkCurrentStatus(self.inps)

        if self.updateStack:
            print('')
            print('Updating an existing stack ...')
            print('')
            if inps.template['force']:
                print('')
                print('Force connections using all dates...')
                print('')
                print(self.allSLCs)
                self.pairs = selectNeighborPairs(self.allSLCs, inps.template['num_connections'], self.updateStack)  # based on stackSentinel.py
            else:
                print('')
                print('Connections using only new dates...')
                print('')
                self.pairs = selectNeighborPairs(self.slaveDates, inps.template['num_connections'], self.updateStack)  # based on stackSentinel.py
        else:
            self.pairs = selectNeighborPairs(self.acquisitionDates, inps.template['num_connections'], self.updateStack)

        print('*****************************************')
        print('Coregistration method: ', self.coregistration)
        print('Workflow: ', self.workflow)
        print('*****************************************')

        self.iter = 0
        self.pairs_sm = []

        return

    def run_stack_workflow(self):        ### This part is for isceStack run_files

        if self.workflow == 'interferogram':
            interferogramStack(self.inps, self.acquisitionDates, self.stackMasterDate, self.slaveDates,
                               self.safe_dict, self.pairs, self.updateStack)
            
        elif self.workflow == 'slc':
            slcStack(self.inps, self.acquisitionDates, self.stackMasterDate, self.slaveDates, self.safe_dict,
                     self.updateStack, mergeSLC=True)
            
        elif self.workflow == 'offset':
            offsetStack(self.inps, self.acquisitionDates, self.stackMasterDate, self.slaveDates, self.safe_dict,
                        self.pairs, self.updateStack)
            
        elif self.workflow == 'correlation':
            correlationStack(self.inps, self.acquisitionDates, self.stackMasterDate, self.slaveDates, self.safe_dict,
                             self.pairs, self.updateStack)

        elif self.workflow == 'fmratecorrection':
            fmrateerrorStack(self.inps, self.acquisitionDates, self.stackMasterDate, self.slaveDates, self.safe_dict,
                             self.pairs, self.updateStack, self.allSLCs)

        run_list = make_run_list(self.work_dir)

        if 'run_0' in run_list[0]:
            self.iter = len(run_list)
        else:
            self.iter = len(run_list) + 1



        return

    def general_stack(self, inps):

        i = self.iter + 1

        if inps.hazard_products_flag == 'True':
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_hazard_products")
            runObj.generateHazardProducts(inps)
            runObj.finalize()

            i += 1

        runObj = rsmasRun()
        runObj.configure(inps, 'run_' + str(i) + "_ingest_insarmaps")
        runObj.ingestInsarmaps(inps)
        runObj.finalize()

        i += 1
        runObj = rsmasRun()
        runObj.configure(inps, 'run_' + str(i) + "_email_results")
        runObj.emailResults(inps)
        runObj.finalize()

        self.iter = i

        return

    def run_post_stack(self):

        inps = self.inps

        if inps.processingMethod == 'smallbaseline':

            i = self.iter

            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_pysar_small_baseline")
            runObj.pysarSB(inps)
            runObj.finalize()

            self.iter = i
            self.general_stack(inps)

        elif inps.processingMethod == 'squeesar' or inps.workflow == 'slc':

            for i in range(len(self.acquisitionDates) - 1):
                self.pairs_sm.append((self.acquisitionDates[0], self.acquisitionDates[i + 1]))

            i = self.iter 

            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_crop_merged_slc")
            runObj.cropMergedSlc(inps)
            runObj.finalize()

            i += 1
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_create_patch")
            runObj.createPatch(inps)
            runObj.finalize()

            i += 1
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_phase_linking")
            runObj.phaseLinking(inps)
            runObj.finalize()

            i += 1
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_generate_interferogram_and_coherence")
            runObj.generateIfg(inps, self.pairs_sm)
            runObj.finalize()

            i += 1
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_unwrap")
            runObj.unwrap(inps, self.pairs_sm)
            runObj.finalize()

            i += 1
            runObj = rsmasRun()
            runObj.configure(inps, 'run_' + str(i) + "_corrections_and_velocity")
            runObj.pysarCorrections(inps)
            runObj.finalize()

            self.iter = i
            self.general_stack(inps)

        return




