#!/usr/bin/env python3

import numpy as np
import argparse
import os
import isce
import isceobj
import datetime
import sys
import shutil
import s1a_isce_utils as ut
import glob
from isceobj.Planet.Planet import Planet
from zerodop.topozero import createTopozero
from isceobj.Util.ImageUtil import ImageLib as IML
from rinsar.objects.auto_defaults import PathFind
from rinsar.utils.process_utilities import create_or_update_template, get_config_defaults, walltime_adjust
import rinsar.job_submission as js
from mergeBursts import multilook

try:
    from dask.distributed import Client, as_completed
    # dask_jobqueue is needed for HPC.
    # PBSCluster (similar to LSFCluster) should also work out of the box
    from dask_jobqueue import LSFCluster
except ImportError:
    raise ImportError('Cannot import dask.distributed or dask_jobqueue!')


pathObj = PathFind()
#################################################################################


def main(iargs=None):
    """ create orth and geo rectifying run jobs and submit them. """

    inps = cmdLineParse(iargs)
    os.environ['DASK_CONFIG'] = os.path.join(inps.work_dir, 'dask')

    demZero = create_demZero(inps.dem, inps.geom_masterDir)

    swathList = ut.getSwathList(inps.master)

    create_georectified_lat_lon(swathList, inps.master, inps.geom_masterDir, demZero)

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
    return


def createParser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser( description='Generates lat/lon for each pixel')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    return parser


def cmdLineParse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = createParser()
    inps = parser.parse_args(args=iargs)

    inps = create_or_update_template(inps)
    inps.geom_masterDir = os.path.join(inps.work_dir, pathObj.geomlatlondir)
    inps.master = os.path.join(inps.work_dir, pathObj.masterdir)

    try:
        inps.dem = glob.glob('{}/DEM/*.wgs84'.format(inps.work_dir))[0]
    except:
        print('DEM not exists!')
        sys.exit(1)

    correct_for_isce_naming_convention(inps)

    inps.rangeLooks = inps.template['rangeLooks']
    inps.azimuthLooks = inps.template['azimuthLooks']

    if os.path.exists(inps.geom_masterDir):
        os.system('rm -rf {}'.format(inps.geom_masterDir))

    os.mkdir(inps.geom_masterDir)

    return inps


def create_demZero(dem, outdir):
    """ create DEM with zero elevation """

    demImage = isceobj.createDemImage()
    demImage.load(dem + '.xml')

    zerodem_name = outdir + '/demzero.wgs84'

    immap = IML.memmap(zerodem_name, mode='write', nchannels=demImage.bands,
                       nxx=demImage.coord1.coordSize, nyy=demImage.coord2.coordSize,
                       scheme=demImage.scheme, dataType=demImage.toNumpyDataType())

    IML.renderISCEXML(zerodem_name, demImage.bands, demImage.coord2.coordSize, demImage.coord1.coordSize,
                      demImage.toNumpyDataType(), demImage.scheme, bbox=demImage.getsnwe())

    demZero = isceobj.createDemImage()
    demZero.load(zerodem_name + '.xml')

    return demZero


def create_georectified_lat_lon(swathList, masterdir, outdir, demZero):
    """ export geo rectified latitude and longitude """

    python_executable_location = sys.executable
    cluster = LSFCluster(python=python_executable_location)
    NUM_WORKERS = 10
    cluster.scale(NUM_WORKERS)
    print("JOB FILE:", cluster.job_script())

    # This line needs to be in a function or in a `if __name__ == "__main__":` block. If it is in no function
    # or "main" block, each worker will try to create its own client (which is bad) when loading the module
    client = Client(cluster)

    futures = []
    start_time = time.time()

    for swath in swathList:
        master = ut.loadProduct(os.path.join(masterdir, 'IW{0}.xml'.format(swath)))

        ###Check if geometry directory already exists.
        dirname = os.path.join(outdir, 'IW{0}'.format(swath))

        if os.path.isdir(dirname):
            print('Geometry directory {0} already exists.'.format(dirname))
        else:
            os.makedirs(dirname)

        ###For each burst
        for ind in range(master.numberOfBursts):

            burst = master.bursts[ind]

            latname = os.path.join(dirname, 'lat_%02d.rdr' % (ind + 1))
            lonname = os.path.join(dirname, 'lon_%02d.rdr' % (ind + 1))

            data = (dirname, burst, latname, lonname, demZero, inps.rangeLooks, inps.azimuthLooks)

            future = client.submit(create_georectified_burst_lat_lon, data, retries=3)
            futures.append(future)

    i_future = 0
    for future, result in as_completed(futures, with_results=True):
        i_future += 1
        print("FUTURE #" + str(i_future), "complete in", time.time() - start_time,
              "output multilooked file:", result, "Time:", time.time())

    cluster.close()
    client.close()

    return


def create_georectified_burst_lat_lon(data):

    (dirname, burst, latname, lonname, demZero, rangeLooks, azimuthLooks) = data

    planet = Planet(pname='Earth')
    topo = createTopozero()
    topo.slantRangePixelSpacing = burst.rangePixelSize
    topo.prf = 1.0 / burst.azimuthTimeInterval
    topo.radarWavelength = burst.radarWavelength
    topo.orbit = burst.orbit
    topo.width = burst.numberOfSamples
    topo.length = burst.numberOfLines
    topo.wireInputPort(name='dem', object=demZero)
    topo.wireInputPort(name='planet', object=planet)
    topo.numberRangeLooks = rangeLooks
    topo.numberAzimuthLooks = azimuthLooks
    topo.lookSide = -1
    topo.sensingStart = burst.sensingStart
    topo.rangeFirstSample = burst.startingRange
    topo.demInterpolationMethod = 'BIQUINTIC'
    topo.latFilename = latname
    topo.lonFilename = lonname
    topo.topo()

    return None


def merge_burst_lat_lon(inps):
    """ merge lat and lon bursts """

    merglatCmd = 'mergeBursts.py --stack {a} --inp_master {b} --dirname {c} --name_pattern {d} ' \
                 '--outfile {e} --method {f} --range_looks {g} --azimuth_looks {h} --no_data_value {i} ' \
                 '--multilook' \
        .format(a=os.path.join(inps.work_dir, pathObj.stackdir), b=inps.master, c=inps.geom_masterDir,
                d='lat*rdr', e=os.path.join(inps.geom_masterDir, 'lat.rdr'), f='top', g=inps.rangeLooks,
                h=inps.azimuthLooks, i=0)

    merglonCmd = 'mergeBursts.py --stack {a} --inp_master {b} --dirname {c} --name_pattern {d} ' \
                 '--outfile {e} --method {f} --range_looks {g} --azimuth_looks {h} --no_data_value {i} ' \
                 '--multilook' \
        .format(a=os.path.join(inps.work_dir, pathObj.stackdir), b=inps.master, c=inps.geom_masterDir,
                d='lon*rdr', e=os.path.join(inps.geom_masterDir, 'lon.rdr'), f='top', g=inps.rangeLooks,
                h=inps.azimuthLooks, i=0)

    print(merglatCmd)
    os.system(merglatCmd)

    print(merglonCmd)
    os.system(merglonCmd)

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

    python_executable_location = sys.executable
    cluster = LSFCluster(python=python_executable_location)
    if len(full_slc_list) >= 40:
        NUM_WORKERS = 40
    else:
        NUM_WORKERS = len(full_slc_list)

    cluster.scale(NUM_WORKERS)
    print("JOB FILE:", cluster.job_script())

    # This line needs to be in a function or in a `if __name__ == "__main__":` block. If it is in no function
    # or "main" block, each worker will try to create its own client (which is bad) when loading the module
    client = Client(cluster)

    futures = []
    start_time = time.time()

    for slc_full, slc_ml in zip(full_slc_list, multilooked_slc):
        data = (slc_full, slc_ml, inps.azimuthLooks, inps.rangeLooks)

        future = client.submit(multilook_single_image, data, retries=3)
        futures.append(future)

    i_future = 0
    for future, result in as_completed(futures, with_results=True):
        i_future += 1
        print("FUTURE #" + str(i_future), "complete in", time.time() - start_time,
              "output multilooked file:", result, "Time:", time.time())

    cluster.close()
    client.close()
    return


def multilook_single_image(data):
    (slc_full, slc_ml, inps.azimuthLooks, inps.rangeLooks) = data
    out_name = multilook(slc_full, slc_ml, inps.azimuthLooks, inps.rangeLooks)
    return out_name


if __name__ == '__main__':
    main()
