#! /usr/bin/env python3
"""This script reads an ifgramStack file and generates sequential interferograms and coherence maps
   Author: Falk Amelung
   Created: 4/2019
"""
###############################################################################

import os
import sys
import argparse
import subprocess
import glob
import shutil
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal, osr, ogr
import isce
import isceobj
from isceobj.Util.ImageUtil import ImageLib as IML
import create_batch as cb
import pysar
import pysar.workflow  #dynamic import for modules used by pysarApp workflow
from pysar.utils import readfile, writefile
from pysar.objects import ifgramStack
import rinsar.utils.process_utilities as putils
from rinsar.objects import message_rsmas
from rinsar.objects.dataset_template import Template

###############################################################################
EXAMPLE = '''example:
  download_rsmas.py $SAMPLESDIR/GalapagosSenDT128.template
'''

def command_line_parse(iargs=None):
    """Command line parser."""
    parser = create_parser()
    inps = parser.parse_args(args=iargs)
    return inps

def create_parser():
    """ Creates command line argument parser object. """
    parser = argparse.ArgumentParser(description='Downloads SAR data using a variety of scripts',
                                     formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('template_file', help='template file containing ssaraopt field')
    parser.add_argument('--outdir', dest='out_dir', default='hazard_products', help='output directory.')

    return parser

###############################################################################

def main(iargs=None):
    """ generates interferograms and coherence images in GeoTiff format """

    message_rsmas.log(os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    inps = command_line_parse(iargs)
    project_name = putils.get_project_name(custom_template_file=inps.template_file)
    work_dir = putils.get_work_directory(None, project_name)
    out_dir = work_dir + '/' + inps.out_dir
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    try:
        file = glob.glob(work_dir + '/PYSAR/INPUTS/ifgramStack.h5')[0]
    except:
        raise Exception('ERROR in ' + os.path.basename(__file__) + ': file ifgramStack.h5 not found') 

    # modify network so that only one connection left
    arg_string = file + ' --max-conn-num 1'
    print('modify_network.py', arg_string)
    pysar.modify_network.main(arg_string.split())

    if not os.path.isdir('GEOCODE'):
        os.makedirs('GEOCODE')

    # geocode ifgramStack
    geo_file = os.path.dirname( os.path.dirname(file)) + '/GEOCODE/geo_' + os.path.basename(file)
    lookup_file =  os.path.dirname( os.path.dirname(file)) + '/INPUTS/geometryRadar.h5'
    template_file = os.path.dirname(os.path.dirname(file)) + '/pysarApp_template.txt'
    arg_string = file + ' -t ' + template_file + ' -l ' + lookup_file + ' -o ' + geo_file
    print('geocode.py', arg_string)
    pysar.geocode.main(arg_string.split())

    # loop over all interferograms
    obj = ifgramStack(geo_file)
    obj.open()
    date12_list = obj.get_date12_list()
    dummy_data, atr = readfile.read(geo_file)

    #for i in  range(2):
    for i in  range(len(date12_list)):
        date_str = date12_list[i]
        print('Working on ... ' + date_str)
        data_coh = readfile.read(geo_file, datasetName='coherence-' + date_str)[0]
        data_unw = readfile.read(geo_file, datasetName='unwrapPhase-' + date_str)[0]

        fname_coh = out_dir + '/coherence_' + date_str + '.tif'
        fname_unw = out_dir + '/interferogram_' + date_str + '.tif'

        create_geotiff( obj, data = data_coh, outfile = fname_coh, type = 'coherence' )
        create_geotiff( obj, data = data_unw, outfile = fname_unw, type = 'interferogram' )
    return

def create_geotiff (obj, data, outfile, type):
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
    ds.SetMetadata(obj.metadata)
    ## TODO: Need to add metadata data_content: 'coherence' (use variable type)
    ## NEED HELP: I could not figure it out

    if type == 'coherence':
        outband = ds.GetRasterBand(1)
    if type == 'interferogram':
        outband = ds.GetRasterBand(1)

    plt.imshow(data)
    plt.savefig( outfile )
    #outband.SetStatistics(np.min(data), np.max(data), np.average(data), np.std(data))
    outband.WriteArray(data)
    ds = None
    return 
###########################################################################################

if __name__ == '__main__':
    main(sys.argv[1:])
