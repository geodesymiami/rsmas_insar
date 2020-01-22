#! /usr/bin/env python3
"""This script reads an ifgramStack file and generates sequential interferograms and coherence maps
   Author: Falk Amelung
   Created: 4/2019
"""
###############################################################################

import os
import sys
import glob
import time
from osgeo import gdal, osr, ogr
import mintpy
import mintpy.workflow  # dynamic import for modules used by smallbaselineApp workflow
from mintpy.utils import readfile, writefile
from mintpy.objects import ifgramStack
import minsar.utils.process_utilities as putils
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind
import minsar.job_submission as js

pathObj = PathFind()

###############################################################################


def main(iargs=None):
    """ generates interferograms and coherence images in GeoTiff format """

    inps = putils.cmd_line_parse(iargs)

    time.sleep(putils.pause_seconds(inps.wait_time))

    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'ifgramStack_to_ifgram_and_coherence'
        job_file_name = job_name
        js.submit_script(job_name, job_file_name, sys.argv[:], inps.work_dir)
        sys.exit(0)

    if not iargs is None:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(iargs[:]))
    else:
        message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    out_dir = inps.work_dir + '/' + pathObj.tiffdir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    try:
        file = glob.glob(inps.work_dir + '/mintpy/inputs/ifgramStack.h5')[0]
    except:
        raise Exception('ERROR in ' + os.path.basename(__file__) + ': file ifgramStack.h5 not found') 

    # modify network so that only one connection left
    arg_string = file + ' --max-conn-num 1'
    print('modify_network.py', arg_string)
    mintpy.modify_network.main(arg_string.split())

    if not os.path.isdir(inps.work_dir + '/mintpy/geo'):
        os.makedirs(inps.work_dir + '/mintpy/geo')

    # geocode ifgramStack
    geo_file = os.path.dirname(os.path.dirname(file)) + '/geo/geo_' + os.path.basename(file)
    lookup_file = os.path.dirname(os.path.dirname(file)) + '/inputs/geometryRadar.h5'
    template_file = os.path.dirname(os.path.dirname(file)) + '/smallbaselineApp_template.txt'
    arg_string = file + ' -t ' + template_file + ' -l ' + lookup_file + ' -o ' + geo_file
    print('geocode.py', arg_string)
    mintpy.geocode.main(arg_string.split())

    # loop over all interferograms
    obj = ifgramStack(geo_file)
    obj.open()
    date12_list = obj.get_date12_list()
    # dummy_data, atr = readfile.read(geo_file)

    for i in range(len(date12_list)):
        date_str = date12_list[i]
        print('Working on ... ' + date_str)
        data_coh = readfile.read(file, datasetName='coherence-' + date_str)[0]
        data_unw = readfile.read(file, datasetName='unwrapPhase-' + date_str)[0]

        fname_coh = out_dir + '/coherence_' + date_str + '.tif'
        fname_unw = out_dir + '/interferogram_' + date_str + '.tif'

        create_geotiff(obj, data=data_coh, outfile=fname_coh, type='coherence', work_dir=inps.work_dir)
        create_geotiff(obj, data=data_unw, outfile=fname_unw, type='interferogram', work_dir=inps.work_dir)
    return


def create_geotiff (obj, data, outfile, type, work_dir):
    ''' creates a geo_tiff '''

    originX = float(obj.get_metadata()['X_FIRST'])
    pixelWidth = float(obj.get_metadata()['X_STEP'])
    originY = float(obj.get_metadata()['Y_FIRST'])
    pixelHeight = float(obj.get_metadata()['Y_STEP'])
    gt = [originX, pixelWidth, 0, originY, 0, pixelHeight]
    driver = gdal.GetDriverByName('GTiff')
    ds = driver.Create(outfile, data.shape[1], data.shape[0], 1, gdal.GDT_Float32, )

    # this assumes the projection is Geographic lat/lon WGS 84
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    ds.SetGeoTransform(gt)

    # metadata consistent with Backscatter products:
    xmlfile = glob.glob(os.path.join(work_dir, pathObj.masterdir, '*.xml'))[0]
    attributes = putils.xmlread(xmlfile)
    Metadata = {'SAT': attributes['missionname'], 'Mode': attributes['passdirection'],
                'Image_Type': 'ortho_{}'.format(type),
                'Date': obj.get_metadata()['START_DATE'] + '-' + obj.get_metadata()['END_DATE']}
    ds.SetMetadata(Metadata)

    outband = ds.GetRasterBand(1)
    outband.WriteArray(data)
    outband.FlushCache()

    ds = None
    return 
###########################################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
