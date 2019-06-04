#! /usr/bin/env python3
"""This script reads an ifgramStack file and generates sequential interferograms and coherence maps
   Author: Falk Amelung
   Created: 4/2019
"""
###############################################################################

import os
import sys
import argparse
import glob
import matplotlib.pyplot as plt
from osgeo import gdal, osr, ogr
import mintpy
import mintpy.workflow  #dynamic import for modules used by smallbaselineApp workflow
from mintpy.utils import readfile, writefile
from mintpy.objects import ifgramStack
import minsar.utils.process_utilities as putils
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import PathFind

pathObj = PathFind()
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
        file = glob.glob(work_dir + '/mintpy/inputs/ifgramStack.h5')[0]
    except:
        raise Exception('ERROR in ' + os.path.basename(__file__) + ': file ifgramStack.h5 not found') 

    # modify network so that only one connection left
    arg_string = file + ' --max-conn-num 1'
    print('modify_network.py', arg_string)
    mintpy.modify_network.main(arg_string.split())

    if not os.path.isdir(work_dir + '/mintpy/geo'):
        os.makedirs(work_dir + '/mintpy/geo')

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
    #dummy_data, atr = readfile.read(geo_file)

    for i in range(len(date12_list)):
        date_str = date12_list[i]
        print('Working on ... ' + date_str)
        data_coh = readfile.read(file, datasetName='coherence-' + date_str)[0]
        data_unw = readfile.read(file, datasetName='unwrapPhase-' + date_str)[0]

        fname_coh = out_dir + '/coherence_' + date_str + '.tif'
        fname_unw = out_dir + '/interferogram_' + date_str + '.tif'

        create_geotiff(obj, data=data_coh, outfile=fname_coh, type='coherence', work_dir=work_dir)
        create_geotiff(obj, data=data_unw, outfile=fname_unw, type='interferogram', work_dir=work_dir)
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
