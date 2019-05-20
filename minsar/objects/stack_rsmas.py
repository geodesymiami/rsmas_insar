#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
from minsar.objects.auto_defaults import PathFind

noMCF = 'False'
defoMax = '2'
maxNodes = 72

pathObj = PathFind()
###################################

class rsmasConfig(object):
    """
       A class representing the config file
    """

    def __init__(self, config_path, outname):
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        self.f = open(outname, 'w')
        self.f.write('[Common]' + '\n')
        self.f.write('')
        self.f.write('##########################' + '\n')

    def configure(self, inps):
        for k in inps.__dict__.keys():
            setattr(self, k, inps.__dict__[k])
        self.plot = 'False'
        self.misreg_az = None
        self.misreg_rng = None
        self.multilook_tool = None
        self.no_data_value = None
        self.cleanup = None


    def phase_link(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('phase_linking_app : ' + '\n')
        self.f.write('patch_dir : ' + self.patchDir + '\n')
        self.f.write('range_window : ' + self.rangeWindow + '\n')
        self.f.write('azimuth_window : ' + self.azimuthWindow + '\n')
        self.f.write('plmethod : ' + self.plmethod + '\n')

    def generate_igram(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('generate_ifgram_sq : ' + '\n')
        self.f.write('minopy_dir : ' + self.sqDir + '\n')
        self.f.write('ifg_dir : ' + self.ifgDir + '\n')
        self.f.write('ifg_index : ' + self.ifgIndex + '\n')
        self.f.write('range_window : ' + self.rangeWindow + '\n')
        self.f.write('azimuth_window : ' + self.azimuthWindow + '\n')
        self.f.write('acquisition_number : ' + self.acq_num + '\n')
        self.f.write('range_looks : ' + self.rangeLooks + '\n')
        self.f.write('azimuth_looks : ' + self.azimuthLooks + '\n')
        if 'geom_master' in self.ifgDir:
            self.f.write('plmethod : ' + self.plmethod + '\n')

    def unwrap(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('unwrap : ' + '\n')
        self.f.write('ifg : ' + self.ifgName + '\n')
        self.f.write('unw : ' + self.unwName + '\n')
        self.f.write('coh : ' + self.cohName + '\n')
        self.f.write('nomcf : ' + self.noMCF + '\n')
        self.f.write('master : ' + self.master + '\n')
        # self.f.write('defomax : ' + self.defoMax + '\n')
        self.f.write('alks : ' + self.rangeLooks + '\n')
        self.f.write('rlks : ' + self.azimuthLooks + '\n')
        self.f.write('method : ' + self.unwMethod + '\n')

    def unwrapSnaphu(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('unwrapSnaphu : ' + '\n')
        self.f.write('ifg : ' + self.ifgName + '\n')
        self.f.write('unw : ' + self.unwName + '\n')
        self.f.write('coh : ' + self.cohName + '\n')
        self.f.write('nomcf : ' + self.noMCF + '\n')
        self.f.write('master : ' + self.master + '\n')
        # self.f.write('defomax : ' + self.defoMax + '\n')
        self.f.write('alks : ' + self.rangeLooks + '\n')
        self.f.write('rlks : ' + self.azimuthLooks + '\n')

    def finalize(self):
        self.f.close()



################################################

class rsmasRun(object):
    """
       A class representing a run which may contain several functions
    """

    def configure(self, inps, runName):
        for k in inps.__dict__.keys():
            setattr(self, k, inps.__dict__[k])

        self.customTemplateFile = os.path.expandvars(inps.customTemplateFile)
        
        self.runDir = os.path.join(self.work_dir, pathObj.rundir)

        self.slcDir = os.path.join(self.work_dir, pathObj.mergedslcdir)

        if not os.path.exists(self.runDir):
            os.makedirs(self.runDir)

        self.run_outname = os.path.join(self.runDir, runName)
        print('writing ', self.run_outname)

        self.config_path = os.path.join(self.work_dir, pathObj.configdir)

        self.runf = open(self.run_outname, 'w')

        self.insarmap_flag = inps.insarmap_flag

    def downloadDataDEM(self):
        self.runf.write('download_rsmas.py ' + self.customTemplateFile + '\n')
        self.runf.write('dem_rsmas.py ' + self.customTemplateFile + ' --boundingBox \n')

    def cropMergedSlc(self):
        self.runf.write(self.text_cmd + 'crop_sentinel.py ' + self.customTemplateFile + '\n')

    def createPatch(self):
        self.runf.write(self.text_cmd + 'create_patch.py ' + self.customTemplateFile + '\n')

    def phaseLinking(self):
        self.runf.write(self.text_cmd + 'phase_linking_app.py ' + self.customTemplateFile + '\n')

    def generateIfg(self, inps, pairs):
        ifgram_dir = os.path.dirname(self.slcDir) + '/interferograms'
        for ifg in pairs:
            configName = os.path.join(self.config_path, 'config_generate_ifgram_{}_{}'.format(ifg[0], ifg[1]))
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.sqDir = os.path.join(inps.work_dir, pathObj.minopydir)
            configObj.ifgDir = os.path.join(ifgram_dir, '{}_{}'.format(ifg[0], ifg[1]))
            configObj.ifgIndex = str(pairs.index(ifg))
            configObj.rangeWindow = inps.template['minopy.range_window']
            configObj.azimuthWindow = inps.template['minopy.azimuth_window']
            configObj.acq_num = str(len(pairs) + 1)
            configObj.rangeLooks = inps.template['topsStack.rangeLooks']
            configObj.azimuthLooks = inps.template['topsStack.azimuthLooks']
            configObj.generate_igram('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommandtops + configName + '\n')
        configName = os.path.join(self.config_path, 'config_generate_quality_map')
        configObj = rsmasConfig(self.config_path, configName)
        configObj.configure(self)
        configObj.sqDir = os.path.join(inps.work_dir, pathObj.minopydir)
        configObj.ifgDir = os.path.join(inps.work_dir, pathObj.geomasterdir)
        configObj.ifgIndex = str(0)
        configObj.rangeWindow = inps.template['minopy.range_window']
        configObj.azimuthWindow = inps.template['minopy.azimuth_window']
        configObj.acq_num = str(len(pairs) + 1)
        configObj.rangeLooks = inps.template['topsStack.rangeLooks']
        configObj.azimuthLooks = inps.template['topsStack.azimuthLooks']
        configObj.plmethod = inps.template['minopy.plmethod']
        configObj.generate_igram('[Function-1]')
        configObj.finalize()
        self.runf.write(self.text_cmd + pathObj.wrappercommandtops + configName + '\n')

    def unwrap(self, inps, pairs):
        for pair in pairs:
            master = pair[0]
            slave = pair[1]
            mergedDir = os.path.join(self.work_dir, pathObj.mergedintdir, master + '_' + slave)
            configName = os.path.join(self.config_path, 'config_igram_unw_' + master + '_' + slave)
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.ifgName = os.path.join(mergedDir, 'filt_fine.int')
            configObj.cohName = os.path.join(mergedDir, 'filt_fine.cor')
            configObj.unwName = os.path.join(mergedDir, 'filt_fine.unw')
            configObj.noMCF = noMCF
            configObj.master = os.path.join(self.work_dir, 'master')
            configObj.defoMax = defoMax
            configObj.unwMethod = inps.template['topsstack.unwMethod']
            configObj.unwrap('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommandtops + configName + '\n')

    def mintpyCorrections(self):
        self.runf.write(self.text_cmd + 'timeseries_corrections.py ' + self.customTemplateFile + '\n')

    def mintpySB(self):
        self.runf.write(self.text_cmd + 'smallbaselineApp.py ' + self.customTemplateFile + '\n')

    def generateHazardProducts(self):
        self.runf.write(self.text_cmd + 'export_ortho_geo.py ' + self.customTemplateFile + '\n')
        self.runf.write(self.text_cmd + 'ifgramStack_to_ifgram_and_coherence.py ' + self.customTemplateFile + '\n')
 
    def ingestInsarmaps(self):
        self.runf.write(self.text_cmd + 'ingest_insarmaps.py ' + self.customTemplateFile + '\n')

    def emailResults(self):
        self.runf.write(self.text_cmd + 'email_results.py ' + self.customTemplateFile + '\n')
        if self.insarmap_flag == 'True':
            self.runf.write(self.text_cmd + 'email_results.py ' + self.customTemplateFile + ' --insarmap\n')

    def finalize(self):
        self.runf.close()

#######################################################


