## ALL path used in the program
# Author: Sara Mirzaee

import os
import glob

##################################################################################################################

def correct_for_isce_naming_convention(inps):

    inps_dict = vars(inps)

    isceKey = ['slc_dirname', 'orbit_dirname', 'aux_dirname', 'work_dir', 'dem', 'master_date', 'num_connections',
               'num_overlap_connections', 'swath_num', 'bbox', 'text_cmd', 'exclude_dates', 'include_dates',
               'azimuthLooks', 'rangeLooks', 'filtStrength', 'esdCoherenceThreshold', 'snrThreshold', 'unwMethod',
               'polarization', 'coregistration', 'workflow', 'startDate', 'stopDate', 'useGPU', 'ilist', 'ilistonly',
               'cleanup', 'layovermsk', 'watermsk', 'useVirtualFiles', 'force']
    
    templateKey = ['slcDir', 'orbitDir', 'auxDir', 'workingDir', 'demDir', 'master', 'numConnections',
                   'numOverlapConnections', 'subswath', 'boundingBox', 'textCmd', 'excludeDates', 'includeDates',
                   'azimuthLooks', 'rangeLooks', 'filtStrength', 'esdCoherenceThreshold', 'snrMisregThreshold',
                   'unwMethod', 'polarization', 'coregistration', 'workflow', 'startDate', 'stopDate', 'useGPU',
                   'ilist', 'ilistonly', 'cleanup', 'layoverMask', 'waterMask', 'virtualFiles', 'forceOverride']

    for old_key, new_key in zip(templateKey, isceKey):
        inps_dict[new_key] = inps_dict.pop(old_key)

    return


##################################################################################################################


class PathFind:
    def __init__(self):
        self.logdir = os.getenv('OPERATIONS') + '/LOGS'
        self.scratchdir = os.getenv('SCRATCHDIR')
        self.required_template_options = ['sentinelStack.subswath', 'sentinelStack.boundingBox']
        self.defaultdir = os.path.expandvars('${RSMAS_INSAR}/rinsar/defaults')
        self.orbitdir = os.path.expandvars('$SENTINEL_ORBITS')
        self.auxdir = os.path.expandvars('$SENTINEL_AUX')
        self.geomasterdir = 'merged/geom_master'
        self.squeesardir = 'SqueeSAR'
        self.rundir = 'run_files'
        self.configdir = 'configs'
        self.mergedslcdir = 'merged/SLC'
        self.mergedintdir = 'merged/interferograms'
        self.wrappercommand = 'SentinelWrapper.py -c '
        return

    def set_isce_defaults(self, inps):

        inps_dict = vars(inps)

        if 'sentinelStack.slcDir' not in inps.custom_template:
            inps_dict['custom_template']['sentinelStack.slcDir'] = inps.work_dir + '/SLC'

        if 'sentinelStack.demDir' not in inps.custom_template:
            inps_dict['custom_template']['sentinelStack.demDir'] = inps.work_dir + '/DEM'

        if 'cleanopt' not in inps.custom_template:
            inps_dict['custom_template']['cleanopt'] = '0'

        inps_dict['custom_template']['sentinelStack.workingDir'] = inps.work_dir

        return

    def isce_clean_list(self):
        cleanlist = []
        cleanlist.append([''])
        cleanlist.append(['stack', 'coreg_slaves', 'misreg', 'orbits',
                          'coarse_interferograms', 'ESD', 'interferograms',
                          'slaves', 'geom_master'])
        cleanlist.append(['merged', 'master', 'baselines', 'configs'])
        cleanlist.append(['SLC'])
        cleanlist.append(['PYSAR', 'run_files'])
        cleanlist.append(['stack', 'coreg_slaves', 'misreg', 'orbits',
                          'coarse_interferograms', 'ESD', 'interferograms',
                          'slaves', 'geom_master', 'DEM'])
        return cleanlist

    def get_email_file_list(self):

        fileList = ['velocity.png', 'avgSpatialCoherence.png', 'temporalCoherence.png', 'maskTempCoh.png', 'mask.png',
                     'demRadar_error.png', 'velocityStd.png', 'geo_velocity.png', 'coherence*.png', 'unwrapPhase*.png',
                     'rms_timeseriesResidual_quadratic.pdf', 'CoherenceHistory.pdf', 'CoherenceMatrix.pdf',
                     'bl_list.txt','Network.pdf', 'geo_velocity_masked.kmz', 'timeseries*.png', 'geo_timeseries*.png']
        return fileList




