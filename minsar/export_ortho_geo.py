#!/usr/bin/env python3

import numpy as np
import os
import isce
import isceobj
import sys
import glob
import gdal
import time
from minsar.objects import message_rsmas
from isceobj.Planet.Planet import Planet
from zerodop.topozero import createTopozero
from isceobj.Util.ImageUtil import ImageLib as IML
from minsar.objects.auto_defaults import PathFind
import minsar.utils.process_utilities as putils
from minsar.job_submission import JOB_SUBMIT

# FA 9/19: commented out as `import boto3 hangs`
#from upload_image_products import upload_to_s3

pathObj = PathFind()
#################################################################################


def main(iargs=None):
    """ create orth and geo rectifying run jobs and submit them. """

    inps = putils.cmd_line_parse(iargs)

    if 'stripmap' in inps.prefix:
        sys.path.append(os.path.join(os.getenv('ISCE_STACK'), 'stripmapStack'))
    else:
        sys.path.append(os.path.join(os.getenv('ISCE_STACK'), 'topsStack'))

    from s1a_isce_utils import loadProduct, getSwathList
    import mergeBursts
    
    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))

    inps.geom_referenceDir = os.path.join(inps.work_dir, pathObj.geomlatlondir)
    inps.reference = os.path.join(inps.work_dir, pathObj.referencedir)

    try:
        inps.dem = glob.glob('{}/DEM/*.wgs84'.format(inps.work_dir))[0]
    except:
        print('DEM not exists!')
        sys.exit(1)

    if not os.path.exists(inps.geom_referenceDir):
        os.mkdir(inps.geom_referenceDir)

    time.sleep(putils.pause_seconds(inps.wait_time))

    inps.out_dir = os.path.join(inps.work_dir, 'run_files')
    job_obj = JOB_SUBMIT(inps)

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'export_ortho_geo'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)

    pic_dir = os.path.join(inps.work_dir, pathObj.tiffdir)

    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    demZero = create_demZero(inps.dem, inps.geom_referenceDir)

    swathList = getSwathList(inps.reference)

    create_georectified_lat_lon(swathList, inps.reference, inps.geom_referenceDir, demZero, loadProduct)

    merge_burst_lat_lon(inps, mergeBursts)

    multilook_images(inps, mergeBursts)

    run_file_list = make_run_list(inps)

    for item in run_file_list:

        putils.remove_last_job_running_products(run_file=item)

        job_obj.write_batch_jobs(batch_file=item)
        job_status = job_obj.submit_batch_jobs(batch_file=item)

        if job_status:
            putils.remove_zero_size_or_length_error_files(run_file=item)
            putils.rerun_job_if_exit_code_140(run_file=item, inps_dict=inps)
            putils.raise_exception_if_job_exited(run_file=item)
            putils.concatenate_error_files(run_file=item, work_dir=inps.work_dir)
            putils.move_out_job_files_to_stdout(run_file=item)

    return


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


def create_georectified_lat_lon(swathList, reference, outdir, demZero, load_function):
    """ export geo rectified latitude and longitude """

    for swath in swathList:
        reference = load_function(os.path.join(reference, 'IW{0}.xml'.format(swath)))

        ###Check if geometry directory already exists.
        dirname = os.path.join(outdir, 'IW{0}'.format(swath))

        if os.path.isdir(dirname):
            print('Geometry directory {0} already exists.'.format(dirname))
        else:
            os.makedirs(dirname)

        ###For each burst
        for ind in range(reference.numberOfBursts):
            burst = reference.bursts[ind]

            latname = os.path.join(dirname, 'lat_%02d.rdr' % (ind + 1))
            lonname = os.path.join(dirname, 'lon_%02d.rdr' % (ind + 1))
            hgtname = os.path.join(dirname, 'hgt_%02d.rdr' % (ind + 1))
            losname = os.path.join(dirname, 'los_%02d.rdr' % (ind + 1))

            if not (os.path.exists(latname + '.xml') or os.path.exists(lonname + '.xml')):

                #####Run Topo
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

                topo.topo()
    return


def merge_burst_lat_lon(inps, mergeBursts_function):
    """ merge lat and lon bursts """

    range_looks = inps.template['topsStack.rangeLooks']
    azimuth_looks = inps.template['topsStack.azimuthLooks']

    merglatCmd = ['mergeBursts.py', ['--stack', os.path.join(inps.work_dir, pathObj.stackdir),
                                     '--inp_reference', inps.reference, '--dirname', inps.geom_referenceDir,
                                     '--name_pattern', 'lat*rdr', '--outfile',
                                     os.path.join(inps.geom_referenceDir, 'lat.rdr'),
                                     '--method', 'top', '--use_virtual_files', '--multilook',
                                     '--range_looks', str(int(range_looks)),
                                     '--azimuth_looks', str(int(azimuth_looks)),
                                     '--no_data_value', '0', '--multilook_tool', 'gdal']]

    merglonCmd = ['mergeBursts.py', ['--stack', os.path.join(inps.work_dir, pathObj.stackdir),
                                     '--inp_reference', inps.reference, '--dirname', inps.geom_referenceDir,
                                     '--name_pattern', 'lon*rdr', '--outfile',
                                     os.path.join(inps.geom_referenceDir, 'lon.rdr'),
                                     '--method', 'top', '--use_virtual_files', '--multilook',
                                     '--range_looks', str(int(range_looks)),
                                     '--azimuth_looks', str(int(azimuth_looks)),
                                     '--no_data_value', '0', '--multilook_tool', 'gdal']]

    if not os.path.exists(os.path.join(inps.geom_referenceDir, 'lat.rdr')):
        print(merglatCmd)
        mergeBursts_function.main(merglatCmd[1])

    if not os.path.exists(os.path.join(inps.geom_referenceDir, 'lon.rdr')):
        print(merglonCmd)
        mergeBursts_function.main(merglonCmd[1])

    return


def make_run_list(inps):
    """ create batch job file for creating ortho and geo rectified backscatter images """

    run_orthorectify = os.path.join(inps.work_dir, pathObj.rundir, 'run_imageProducts_orthorectify')
    run_georectify = os.path.join(inps.work_dir, pathObj.rundir, 'run_imageProducts_georectify')
    slc_list = os.listdir(os.path.join(inps.work_dir, pathObj.mergedslcdir))

    lat_ds = gdal.Open(inps.geom_referenceDir + '/lat.rdr.ml', gdal.GA_ReadOnly)
    latstep = abs(
        (np.nanmin(lat_ds.GetVirtualMemArray()) - np.nanmax(lat_ds.GetVirtualMemArray())) / (lat_ds.RasterYSize - 1))

    lon_ds = gdal.Open(inps.geom_referenceDir + '/lon.rdr.ml', gdal.GA_ReadOnly)
    lonstep = abs(
        (np.nanmin(lon_ds.GetVirtualMemArray()) - np.nanmax(lon_ds.GetVirtualMemArray())) / (lon_ds.RasterXSize - 1))

    ifgram_cmd = 'ifgramStack_to_ifgram_and_coherence.py {}'.format(inps.custom_template_file)

    with open(run_orthorectify, 'w') as f:
        for item in slc_list:
            cmd = 'export_amplitude_tif.py {a0} -f {a1} -y {a2} -x {a3}  -t ortho \n'.format(
                a0=inps.custom_template_file, a1=item, a2=latstep, a3=lonstep)
            f.write(cmd)
        f.write(ifgram_cmd)

    with open(run_georectify, 'w') as f:
        for item in slc_list:
            cmd = 'export_amplitude_tif.py {a0} -f {a1} -y {a2} -x {a3} -t geo \n'.format(
                a0=inps.custom_template_file, a1=item, a2=latstep, a3=lonstep)
            f.write(cmd)

    run_file_list = [run_orthorectify, run_georectify]

    return run_file_list


def multilook_images(inps, mergeBursts_module):

    full_slc_list = [os.path.join(inps.work_dir, pathObj.mergedslcdir, x, x+'.slc.full')
                for x in os.listdir(os.path.join(inps.work_dir, pathObj.mergedslcdir))]

    multilooked_slc = [x.split('.full')[0] + '.ml' for x in full_slc_list]

    range_looks = inps.template['topsStack.rangeLooks']
    azimuth_looks = inps.template['topsStack.azimuthLooks']

    for slc_full, slc_ml in zip(full_slc_list, multilooked_slc):
        if not os.path.exists(slc_ml):
            mergeBursts_module.multilook(slc_full, slc_ml, azimuth_looks, range_looks, multilook_tool="gdal")

    full_geometry_list = [os.path.join(inps.work_dir, pathObj.geomlatlondir, x)
                          for x in ['lat.rdr.full', 'lon.rdr.full']] \
                         + [os.path.join(inps.work_dir, pathObj.georeferencedir, x)
                            for x in ['lat.rdr.full', 'lon.rdr.full']]

    multilooked_geometry = [x.split('.full')[0] + '.ml' for x in full_geometry_list]

    for geo_full, geo_ml in zip(full_geometry_list, multilooked_geometry):
        if not os.path.exists(geo_ml):
            mergeBursts_module.multilook(geo_full, geo_ml, azimuth_looks, range_looks, multilook_tool="gdal")

    return


if __name__ == '__main__':
    main()
