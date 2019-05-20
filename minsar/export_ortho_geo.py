#!/usr/bin/env python3

import argparse
import os
import isceobj
import sys
import s1a_isce_utils as ut
import glob
from isceobj.Planet.Planet import Planet
from zerodop.topozero import createTopozero
from isceobj.Util.ImageUtil import ImageLib as IML
from minsar.objects.auto_defaults import PathFind
from minsar.utils.process_utilities import create_or_update_template, get_config_defaults, walltime_adjust
import minsar.job_submission as js
import mergeBursts as mb

pathObj = PathFind()
#################################################################################


def createParser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser( description='Generates lat/lon for each pixel')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('--submit', dest='submit_flag', action='store_true', help='submits job')
    parser.add_argument('--walltime', dest='wall_time', type=str, default='2:00',
                        help='walltime, e.g. 2:00 (default: 2:00)')
    return parser


def cmdLineParse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = createParser()
    inps = parser.parse_args(args=iargs)

    inps = create_or_update_template(inps)
    inps.geom_masterDir = os.path.join(inps.work_dir, pathObj.geomlatlondir)
    inps.master = os.path.join(inps.work_dir, pathObj.masterdir)
    pathObj.rundir = os.path.join(inps.work_dir, pathObj.rundir)
    pathObj.project = os.getenv('SCRATCHDIR').split('/')[-2]
    print('Project: {}'.format(pathObj.project))

    try:
        inps.dem = glob.glob('{}/DEM/*.wgs84'.format(inps.work_dir))[0]
    except:
        print('DEM not exists!')
        sys.exit(1)

    pathObj.correct_for_isce_naming_convention(inps)

    inps.rangeLooks = inps.template['rangeLooks']
    inps.azimuthLooks = inps.template['azimuthLooks']

    if not os.path.exists(inps.geom_masterDir):
        os.mkdir(inps.geom_masterDir)

    return inps


def create_dem_zero(dem, outdir):
    """ create DEM with zero elevation """

    demImage = isceobj.createDemImage()
    demImage.load(dem + '.xml')

    zerodem_name = os.path.expandvars(outdir + '/demzero.wgs84')

    immap = IML.memmap(zerodem_name, mode='write', nchannels=demImage.bands,
                       nxx=demImage.coord1.coordSize, nyy=demImage.coord2.coordSize,
                       scheme=demImage.scheme, dataType=demImage.toNumpyDataType())

    IML.renderISCEXML(zerodem_name, demImage.bands, demImage.coord2.coordSize, demImage.coord1.coordSize,
                      demImage.toNumpyDataType(), demImage.scheme, bbox=demImage.getsnwe())

    dem_zero = isceobj.createDemImage()
    dem_zero.load(zerodem_name + '.xml')
    return dem_zero



def create_georectified_lat_lon(swath_list, masterdir, outdir, dem_zero, range_looks, azimuth_looks):
    """ export geo rectified latitude and longitude """

    for swath in swath_list:
        master = ut.loadProduct(os.path.join(masterdir, 'IW{0}.xml'.format(swath)))

        ###Check if geometry directory already exists.
        dirname = os.path.expandvars(os.path.join(outdir, 'IW{0}'.format(swath)))

        if os.path.isdir(dirname):
            print('Geometry directory {0} already exists.'.format(dirname))
        else:
            os.makedirs(dirname)

        ###For each burst
        for ind in range(master.numberOfBursts):

            burst = master.bursts[ind]

            latname = os.path.join(dirname, 'lat_%02d.rdr' % (ind + 1))
            lonname = os.path.join(dirname, 'lon_%02d.rdr' % (ind + 1))
            hgtname = os.path.join(dirname, 'hgt_%02d.rdr' % (ind + 1))
            losname = os.path.join(dirname, 'los_%02d.rdr' % (ind + 1))
            maskname = os.path.join(dirname, 'shadowMask_%02d.rdr' % (ind + 1))
            incname = os.path.join(dirname, 'incLocal_%02d.rdr' % (ind + 1))

            outnames= (latname, lonname, hgtname, losname, maskname, incname)

            if not (os.path.exists(latname+'.vrt') or os.path.exists(lonname+'.vrt')):
                create_georectified_burst_lat_lon(burst, outnames, dem_zero)

    return


def create_georectified_burst_lat_lon(burst, outnames, dem_zero):

    (latname, lonname, hgtname, losname, maskname, incname) = outnames

    planet = Planet(pname='Earth')
    topo = createTopozero()
    topo.slantRangePixelSpacing = burst.rangePixelSize
    topo.prf = 1.0 / burst.azimuthTimeInterval
    topo.radarWavelength = burst.radarWavelength
    topo.orbit = burst.orbit
    topo.width = burst.numberOfSamples
    topo.length = burst.numberOfLines
    topo.wireInputPort(name='dem', object=dem_zero)
    topo.wireInputPort(name='planet', object=planet)
    topo.numberRangeLooks = 1
    topo.numberAzimuthLooks = 1
    topo.lookSide = -1
    topo.sensingStart = burst.sensingStart
    topo.rangeFirstSample = burst.startingRange
    topo.demInterpolationMethod = 'BIQUINTIC'
    topo.latFilename = latname
    topo.lonFilename = lonname
    topo.heightFilename = hgtname
    topo.losFilename = losname
    topo.maskFilename = maskname
    topo.incFilename = incname
    topo.topo()

    return


def merge_burst_lat_lon(inps):
    """ merge lat and lon bursts """

    merglatCmd = ['mergeBursts.py', ['--stack', os.path.join(inps.work_dir, pathObj.stackdir),
                                     '--inp_master', inps.master, '--dirname', inps.geom_masterDir,
                                     '--name_pattern', 'lat*rdr', '--outfile', os.path.join(inps.geom_masterDir, 'lat.rdr'),
                                     '--method', 'top', '--use_virtual_files', '--multilook',
                                     '--range_looks', str(int(inps.rangeLooks)),
                                     '--azimuth_looks', str(int(inps.azimuthLooks)),
                                     '--multilook_tool', 'gdal', '--no_data_value', '0']]

    merglonCmd = ['mergeBursts.py', ['--stack', os.path.join(inps.work_dir, pathObj.stackdir),
                                     '--inp_master', inps.master, '--dirname', inps.geom_masterDir,
                                     '--name_pattern', 'lon*rdr', '--outfile', os.path.join(inps.geom_masterDir, 'lon.rdr'),
                                     '--method', 'top', '--use_virtual_files', '--multilook',
                                     '--range_looks', str(int(inps.rangeLooks)),
                                     '--azimuth_looks', str(int(inps.azimuthLooks)),
                                     '--multilook_tool', 'gdal', '--no_data_value', '0']]

    if not os.path.exists(os.path.join(inps.geom_masterDir, 'lat.rdr')):
        print(merglatCmd)
        mb.main(merglatCmd[1])

    if not os.path.exists(os.path.join(inps.geom_masterDir, 'lon.rdr')):
        print(merglonCmd)
        mb.main(merglonCmd[1])

    sys.exit(0)

    return


def make_run_list_amplitude(inps):
    """ create batch job file for creating ortho and geo rectified backscatter images """

    run_amplitude_ortho = os.path.join(inps.work_dir, pathObj.rundir, 'run_amplitude_ortho')
    run_amplitude_geo = os.path.join(inps.work_dir, pathObj.rundir, 'run_amplitude_geo')
    slc_list = os.listdir(os.path.join(inps.work_dir, pathObj.mergedslcdir))

    with open(run_amplitude_ortho, 'w') as f:
        for item in slc_list:
            cmd = 'export_amplitude_tif.py {a0} -f {a1} -b "{a2}" -t ortho \n'.format(
                a0=inps.customTemplateFile, a1=item, a2=inps.cropbox)
            f.write(cmd)

    with open(run_amplitude_geo, 'w') as f:
        for item in slc_list:
            cmd = 'export_amplitude_tif.py {a0} -f {a1} -b "{a2}" -t geo \n'.format(
                a0=inps.customTemplateFile, a1=item, a2=inps.cropbox)
            f.write(cmd)

    run_file_list = [run_amplitude_ortho, run_amplitude_geo]

    return run_file_list


def multilook_images(inps):

    full_slc_list = [os.path.join(inps.work_dir, pathObj.mergedslcdir, x, x+'.slc.full')
                for x in os.listdir(os.path.join(inps.work_dir, pathObj.mergedslcdir))]

    multilooked_slc = [x.split('.full')[0]+'.ml' for x in full_slc_list]

    for slc_full, slc_ml in zip(full_slc_list, multilooked_slc):
        if not os.path.exists(slc_ml):
            mb.multilook(slc_full, slc_ml, inps.azimuthLooks, inps.rangeLooks)
    return


def main(iargs=None):
    """ create ortho and geo rectifying run jobs and submit them. """

    inps = cmdLineParse()

    if inps.submit_flag:
        job_file_name = 'export_ortho_geo'
        work_dir = os.getcwd()
        job_name = inps.customTemplateFile.split(os.sep)[-1].split('.')[0]
        js.submit_script(job_name, job_file_name, sys.argv[:], work_dir, inps.wall_time)
        sys.exit(0)

    if not os.path.exists(os.path.join(inps.geom_masterDir, 'lon.rdr')):

        dem_zero = create_dem_zero(inps.dem, inps.geom_masterDir)

        swath_list = ut.getSwathList(inps.master)

        create_georectified_lat_lon(swath_list, inps.master, inps.geom_masterDir, dem_zero, inps.rangeLooks,
                                    inps.azimuthLooks)
        merge_burst_lat_lon(inps)

    multilook_images(inps)

    run_file_list = make_run_list_amplitude(inps)

    config = get_config_defaults(config_file='job_defaults.cfg')

    for item in run_file_list:
        step_name = 'amplitude_ortho_geo'
        try:
            memorymax = config[step_name]['memory']
        except:
            memorymax = config['DEFAULT']['memory']

        try:
            if config[step_name]['adjust'] == 'True':
                walltimelimit = walltime_adjust(config[step_name]['walltime'])
            else:
                walltimelimit = config[step_name]['walltime']
        except:
            walltimelimit = config['DEFAULT']['walltime']

        queuename = os.getenv('QUEUENAME')

        jobs = js.submit_batch_jobs(batch_file=item,
                                    out_dir=os.path.join(inps.work_dir, 'run_files'),
                                    memory=memorymax, walltime=walltimelimit, queue=queuename)


if __name__ == '__main__':
    main()
