#!/usr/bin/env python3
########################
# Author: Sara Mirzaee
#######################

import os
from rinsar.objects.auto_defaults import PathFind

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

    def crop_sentinel(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('crop_sentinel : ' + '\n')
        self.f.write('input : ' + self.input + '\n')
        self.f.write('output : ' + self.output + '\n')
        self.f.write('bbox : ' + self.bbox + '\n')
        self.f.write('multilook : ' + self.multi_look + '\n')
        self.f.write('range_looks : ' + self.rangeLooks + '\n')
        self.f.write('azimuth_looks : ' + self.azimuthLooks + '\n')
        self.f.write('multilook_tool : ' + self.multilook_tool + '\n')

    def create_patch(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('create_patch : ' + '\n')
        self.f.write('slc_dir : ' + self.slcDir + '\n')
        self.f.write('squeesar_dir : ' + self.sqDir + '\n')
        self.f.write('patch_size : ' + self.patchSize + '\n')
        self.f.write('range_window : ' + self.rangeWindow + '\n')
        self.f.write('azimuth_window : ' + self.azimuthWindow + '\n')

    def phase_link(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('PSQ_sentinel : ' + '\n')
        self.f.write('patch_dir : ' + self.patchDir + '\n')
        self.f.write('range_window : ' + self.rangeWindow + '\n')
        self.f.write('azimuth_window : ' + self.azimuthWindow + '\n')
        self.f.write('plmethod : ' + self.plmethod + '\n')

    def generate_igram(self, function):
        self.f.write('###################################' + '\n')
        self.f.write(function + '\n')
        self.f.write('generate_ifgram_sq : ' + '\n')
        self.f.write('squeesar_dir : ' + self.sqDir + '\n')
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

    # def __init__(self):

    def configure(self, inps, runName):
        for k in inps.__dict__.keys():
            setattr(self, k, inps.__dict__[k])
        self.runDir = os.path.join(self.work_dir, pathObj.rundir)

        self.slcDir = os.path.join(self.work_dir, pathObj.mergedslcdir)

        if not os.path.exists(self.runDir):
            os.makedirs(self.runDir)

        self.run_outname = os.path.join(self.runDir, runName)
        print('writing ', self.run_outname)

        self.config_path = os.path.join(self.work_dir, pathObj.configdir)

        self.runf = open(self.run_outname, 'w')


    def downloadDataDEM(self, inps, download_flag):
        if download_flag == 1:
            self.runf.write('download_rsmas.py ' + inps.customTemplateFile + '\n')
            self.runf.write('dem_rsmas.py ' + inps.customTemplateFile + '\n')
        else:
            self.runf.write('dem_rsmas.py ' + inps.customTemplateFile + '\n')


    def cropMergedSlc(self, acquisitions, inps):
        for slc in acquisitions:
            cropDir = os.path.join(self.work_dir, pathObj.mergedslcdir, slc)
            configName = os.path.join(self.config_path, 'config_crop_' + slc)
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.input = os.path.join(cropDir, slc + '.slc.full')
            configObj.output = os.path.join(cropDir, slc + '.slc')
            configObj.bbox = inps.bbox_rdr
            configObj.multi_look = 'False'
            configObj.rangeLooks = inps.rangeLooks
            configObj.azimuthLooks = inps.azimuthLooks
            configObj.multilook_tool = 'gdal'
            configObj.crop_sentinel('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

        list_geo = ['lat', 'lon', 'los', 'hgt', 'shadowMask', 'incLocal']
        multiookToolDict = {'lat*rdr': 'gdal', 'lon*rdr': 'gdal', 'los*rdr': 'gdal', 'hgt*rdr': "gdal",
                            'shadowMask*rdr': "isce", 'incLocal*rdr': "gdal"}
        for item in list_geo:
            pattern = item + '*rdr'
            geoDir = os.path.join(self.work_dir, pathObj.geomasterdir)
            configName = os.path.join(self.config_path, 'config_crop_' + item)
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.input = os.path.join(geoDir, item + '.rdr.full')
            configObj.output = os.path.join(geoDir, item + '.rdr')
            configObj.bbox = inps.bbox_rdr
            configObj.multi_look = 'False'
            configObj.rangeLooks = inps.rangeLooks
            configObj.azimuthLooks = inps.azimuthLooks
            configObj.multilook_tool = multiookToolDict[pattern]
            configObj.crop_sentinel('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

    def createPatch(self, inps):
        configName = os.path.join(self.config_path, 'config_create_patch')
        configObj = rsmasConfig(self.config_path, configName)
        configObj.configure(self)
        configObj.slcDir = self.slcDir
        configObj.sqDir = inps.squeesar_dir
        configObj.patchSize = inps.patch_size
        configObj.rangeWindow = inps.range_window
        configObj.azimuthWindow = inps.azimuth_window
        configObj.create_patch('[Function-1]')
        configObj.finalize()
        self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

    def phaseLinking(self, inps):

        for patch in inps.patch_list:
            configName = os.path.join(self.config_path, 'config_phase_link_PATCH' + patch)
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.patchDir = os.path.join(inps.squeesar_dir, 'PATCH' + patch)
            configObj.rangeWindow = inps.range_window
            configObj.azimuthWindow = inps.azimuth_window
            configObj.plmethod = inps.plmethod
            configObj.phase_link('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

    def generateIfg(self, inps, acquisitions):
        ifgram_dir = os.path.dirname(self.slcDir) + '/interferograms'
        if not os.path.isdir(ifgram_dir):
            os.mkdir(ifgram_dir)
        index = 0
        for ifg in acquisitions[1::]:
            index += 1
            configName = os.path.join(self.config_path, 'config_generate_ifgram_{}_{}'.format(acquisitions[0], ifg))
            configObj = rsmasConfig(self.config_path, configName)
            configObj.configure(self)
            configObj.sqDir = inps.squeesar_dir
            configObj.ifgDir = os.path.join(ifgram_dir, '{}_{}'.format(acquisitions[0], ifg))
            configObj.ifgIndex = str(index)
            configObj.rangeWindow = inps.range_window
            configObj.azimuthWindow = inps.azimuth_window
            configObj.acq_num = str(len(acquisitions))
            configObj.rangeLooks = inps.rangeLooks
            configObj.azimuthLooks = inps.azimuthLooks
            configObj.generate_igram('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')
        configName = os.path.join(self.config_path, 'config_generate_quality_map')
        configObj = rsmasConfig(self.config_path, configName)
        configObj.configure(self)
        configObj.sqDir = inps.squeesar_dir
        configObj.ifgDir = inps.geo_master_dir
        configObj.ifgIndex = str(0)
        configObj.rangeWindow = inps.range_window
        configObj.azimuthWindow = inps.azimuth_window
        configObj.acq_num = str(len(acquisitions))
        configObj.rangeLooks = inps.rangeLooks
        configObj.azimuthLooks = inps.azimuthLooks
        configObj.plmethod = inps.plmethod
        configObj.generate_igram('[Function-1]')
        configObj.finalize()
        self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

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
            configObj.unwMethod = inps.unwMethod
            configObj.unwrap('[Function-1]')
            configObj.finalize()
            self.runf.write(self.text_cmd + pathObj.wrappercommand + configName + '\n')

    def pysarCorrections(self, inps):
        self.runf.write(self.text_cmd + 'timeseries_corrections.py ' + inps.customTemplateFile + '\n')

    def pysarSB(self, inps):
        self.runf.write(self.text_cmd + 'pysarApp.py ' + inps.customTemplateFile + '\n')

    def exportAmplitude(self, inps):
        self.runf.write(self.text_cmd + 'export_ortho_geo.py ' + inps.customTemplateFile + '\n')

    def emailPySAR(self, inps):
        self.runf.write(self.text_cmd + 'email_results.py ' + inps.customTemplateFile + '\n')

    def ingestInsarmaps(self, inps):
        self.runf.write(self.text_cmd + 'ingest_insarmaps.py ' + inps.customTemplateFile + '\n')

    def emailInsarmaps(self, inps):
        self.runf.write(self.text_cmd + 'email_results.py ' + inps.customTemplateFile + ' --insarmap\n')

    def finalize(self):
        self.runf.close()

#######################################################


