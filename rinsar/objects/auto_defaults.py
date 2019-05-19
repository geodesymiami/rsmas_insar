## ALL path and default strings used in the program
# Author: Sara Mirzaee

import os
import glob
import datetime


class PathFind:
    def __init__(self):
        self.logdir = os.getenv('OPERATIONS') + '/LOGS'
        self.scratchdir = os.getenv('SCRATCHDIR')
        self.required_template_options = ['topsStack.subswath', 'topsStack.boundingBox']
        self.defaultdir = os.path.expandvars('${RSMAS_INSAR}/rinsar/defaults')
        self.orbitdir = os.path.expandvars('$SENTINEL_ORBITS')
        self.auxdir = os.path.expandvars('$SENTINEL_AUX')
        self.geomasterdir = 'merged/geom_master'
        self.squeesardir = 'squeesar'
        self.rundir = 'run_files'
        self.configdir = 'configs'
        self.mergedslcdir = 'merged/SLC'
        self.mergedintdir = 'merged/interferograms'
        self.geomlatlondir = 'geom_master_noDEM'
        self.wrappercommandtops = 'topsWrapper.py -c '
        self.wrappercommandstripmap = 'stripmapWrapper.py -c '
        self.masterdir = 'master'
        self.stackdir = 'stack'
        self.tiffdir = 'hazard_products'
        self.daskconfig = os.path.expandvars('${RSMAS_INSAR}/rinsar/defaults/dask/dask.yaml')
        return

    def set_isce_defaults(self, inps):

        inps_dict = vars(inps)

        inps_dict['template']['topsStack.slcDir'] = inps.work_dir + '/SLC'

        inps_dict['template']['topsStack.demDir'] = inps.work_dir + '/DEM'

        if 'cleanopt' not in inps.template:
            inps_dict['template']['cleanopt'] = '0'

        inps_dict['template']['topsStack.workingDir'] = inps.work_dir
        inps_dict['template']['topsStack.orbitDir'] = self.orbitdir
        inps_dict['template']['topsStack.auxDir'] = self.auxdir

        return

    @staticmethod
    def grab_cropbox(inps):
        try:
            if inps.template['processingMethod'] == 'smallbaseline':
                subset = inps['template']['pysar.subset.lalo']
            else:
                subset = inps.template['squeesar.subset']
            cropbox = '{} {} {} {}'.format(subset[0], subset[1].split(',')[0], subset[1].split(',')[1],
                                                     subset[2])
        except:
            cropbox = inps.template['topsStack.boundingBox']

        return cropbox

    @staticmethod
    def correct_for_ssara_date_format(template_options):

        inps_dict = template_options
        
        if 'ssaraopt.startDate' in inps_dict:
            inps_dict['ssaraopt.startDate'] = \
                datetime.datetime.strptime(inps_dict['ssaraopt.startDate'], '%Y%m%d').strftime('%Y-%m-%d')
        
        if 'ssaraopt.endDate' in inps_dict:
            inps_dict['ssaraopt.endDate'] = \
                datetime.datetime.strptime(inps_dict['ssaraopt.endDate'], '%Y%m%d').strftime('%Y-%m-%d')
        
        return inps_dict

    @staticmethod
    def isce_clean_list():
        cleanlist = []
        cleanlist.append(['stack',  'misreg', 'orbits', 'coarse_interferograms', 'ESD',
                          'interferograms', 'slaves'])
        cleanlist.append(['merged', 'master', 'coreg_slaves', 'baselines', 'geom_master'])
        cleanlist.append(['SLC'])
        cleanlist.append(['PYSAR', 'run_files', 'configs', 'DEM'])

        return cleanlist

    @staticmethod
    def get_email_file_list():

        fileList = ['velocity.png', 'avgSpatialCoherence.png', 'temporalCoherence.png', 'maskTempCoh.png', 'mask.png',
                     'demRadar_error.png', 'velocityStd.png', 'geo_velocity.png', 'coherence*.png', 'unwrapPhase*.png',
                     'rms_timeseriesResidual_quadratic.pdf', 'CoherenceHistory.pdf', 'CoherenceMatrix.pdf',
                     'bl_list.txt', 'Network.pdf', 'geo_velocity_masked.kmz', 'timeseries*.png', 'geo_timeseries*.png']
        return fileList

    @staticmethod
    def get_geom_master_lists():
        list_geo = ['lat', 'lon', 'los', 'hgt', 'shadowMask', 'incLocal']
        return list_geo

    @staticmethod
    def correct_for_isce_naming_convention(inps):

        inps_dict = vars(inps)

        isceKey = ['slc_dirname', 'orbit_dirname', 'aux_dirname', 'work_dir', 'dem', 'master_date', 'num_connections',
                   'num_overlap_connections', 'swath_num', 'bbox', 'text_cmd', 'exclude_dates', 'include_dates',
                   'azimuthLooks', 'rangeLooks', 'filtStrength', 'esdCoherenceThreshold', 'snrThreshold', 'unwMethod',
                   'polarization', 'coregistration', 'workflow', 'startDate', 'stopDate', 'useGPU']

        templateKey = ['slcDir', 'orbitDir', 'auxDir', 'workingDir', 'demDir', 'master', 'numConnections',
                       'numOverlapConnections', 'subswath', 'boundingBox', 'textCmd', 'excludeDates', 'includeDates',
                       'azimuthLooks', 'rangeLooks', 'filtStrength', 'esdCoherenceThreshold', 'snrMisregThreshold',
                       'unwMethod', 'polarization', 'coregistration', 'workflow', 'startDate', 'stopDate', 'useGPU']

        stackprefix = os.path.basename(os.getenv('ISCE_STACK'))
        templateKey = [stackprefix + '.' + x for x in templateKey]

        for old_key, new_key in zip(templateKey, isceKey):
            inps_dict['template'][new_key] = inps_dict['template'].pop(old_key)
            if inps_dict['template'][new_key] == 'None':
                inps_dict['template'][new_key] = None

        if not inps_dict['template']['startDate'] in [None, 'auto']:
            print(inps_dict['template']['startDate'])
            inps_dict['template']['startDate'] = datetime.datetime.strptime(inps_dict['template']['startDate'],
                                                                            '%Y%m%d').strftime('%Y-%m-%d')

        if not inps_dict['template']['stopDate'] in [None, 'auto']:
            inps_dict['template']['stopDate'] = datetime.datetime.strptime(inps_dict['template']['stopDate'],
                                                                           '%Y%m%d').strftime('%Y-%m-%d')

        return


