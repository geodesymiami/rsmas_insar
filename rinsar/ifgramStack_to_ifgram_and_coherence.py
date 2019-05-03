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

import messageRsmas
import _process_utilities as putils
from dataset_template import Template
import create_batch as cb
import pysar
import numpy as np
import pysar.workflow  #dynamic import for modules used by pysarApp workflow
from pysar.utils import readfile, writefile
from pysar.objects import ifgramStack
import matplotlib.pyplot as plt
import isce
import isceobj
from isceobj.Util.ImageUtil import ImageLib as IML

from osgeo import gdal, osr, ogr
import numpy as np

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
    parser.add_argument( '--submit', dest='submit_flag', action='store_true', help='submits job')

    # parser.add_argument('template_file', help='template file containing ssaraopt field', nargs='?')
    return parser

###############################################################################

def main(iargs=None):
    """ generates interferograms and coherence images in GeoTiff format """



    #plt.imshow(data, interpolation='nearest')
    #plt.show()

    messageRsmas.log(os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    inps = command_line_parse(iargs)
    project_name = putils.get_project_name(custom_template_file=inps.template_file)
    work_dir = putils.get_work_directory(None, project_name)
    try:
        file = glob.glob(work_dir + '/PYSAR/INPUTS/ifgramStack.h5')[0]
    except:
        raise Exception('ERROR in ' + os.path.basename(__file__) + ': file ifgramStack.h5 not found') 

    arg_string = file + ' --max-conn-num 1'
    print('modify_network.py', arg_string)
    pysar.modify_network.main(arg_string.split())

    if not os.path.isdir('GEOCODE'):
        os.makedirs('GEOCODE')

    geo_file = os.path.dirname( os.path.dirname(file)) + '/GEOCODE/geo_' + os.path.basename(file)
    arg_string = file + ' -t pysarApp_template.txt -o ' + geo_file
    print('geocode.py', arg_string)
    pysar.geocode.main(arg_string.split())
    data, atr = readfile.read(geo_file)

    obj = ifgramStack(geo_file)
    obj.open()
    dir(obj)
   
    i = 5
    obj.get_date_list()
    date12_list = obj.get_date12_list()
    date_str = date12_list[i]

    coh_data = readfile.read(geo_file, datasetName='coherence-' + date_str)[0]
    unw_data = readfile.read(geo_file, datasetName='unwrapPhase-' + date_str)[0]

    coh_out_file = 'coherence_' + date_str + '.h5'

    data = coh_data

    originX = float(obj.get_metadata()['X_FIRST'])
    pixelWidth = float(obj.get_metadata()['X_STEP'])
    originY = float(obj.get_metadata()['Y_FIRST'])
    pixelHeight = float(obj.get_metadata()['Y_STEP'])
    geo_transform = [originX, pixelWidth, 0, originY, 0, pixelHeight]
 
    driver = gdal.GetDriverByName('GTiff')
    #ds = driver.Create('output.tif', data.shape[0], data.shape[1], 1, gdal.GDT_Float64, )
    ds = driver.Create('/nethome/famelung/output.tif', data.shape[1], data.shape[0], 1, gdal.GDT_Float64, )
    # this assumes the projection is Geographic lat/lon WGS 84
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    ds.SetProjection(srs.ExportToWkt())
    gt = [originX, pixelWidth, 0, originY, 0, pixelHeight]
    ds.SetGeoTransform(gt)
    outband=ds.GetRasterBand(1)

    plt.imshow(data)
    plt.savefig('/nethome/famelung/foo.png')
    import pdb; pdb.set_trace()
    #outband.SetStatistics(np.min(data), np.max(data), np.average(data), np.std(data))
    outband.WriteArray(data)
    ds = None

    '''
    dsDict = dict()
    dsDict['coherence'] = coh_data
    import pdb; pdb.set_trace()
    writefile.write(dsDict, out_file=coh_out_file, metadata=atr)

    i = 0
    coh_data = readfile.read(file, datasetName='coherence-' + date_str)[0]
    unw_data = readfile.read(file, datasetName='unwrapPhase-' + date_str)[0]

    coh_out_name = 'coherence-' + date_str  

    width = coh_data.shape[1]
    n_line = coh_data.shape[0]

    #ifg = np.memmap(outputint_name , dtype=np.complex64, mode='w+', shape=(n_line, width))
    Quality = IML.memmap(coh_out_name, mode='write', nchannels=1, nxx=width, nyy=n_line, scheme='BIL', dataType='f')
    Quality.bands[0][:,:] = coh_data
    IML.renderISCEXML(coh_out_name, 1, n_line, width, 'f', 'BIL')

    obj_unw = isceobj.createImage()
    obj_unw.load(coh_out_name + '.xml')
    obj_unw.imageType = 'f'
    obj_unw.renderHdr()

    #obj_unw.setFilename(coh_out_name)
    #obj_unw.setWidth(width)
    #obj_unw.setLength(n_line)
    #obj_unw.setAccessMode('READ')
    #obj_unw.imageType = 'f'
    #obj_unw.renderHdr()
    #obj_unw.renderVRT()

    #Ifs[:,:] = interferogram_rasterfile
    #obj_int = isceobj.createIntImage()
    #obj_int.setFilename(outputint_name)
    #obj_int.setWidth(width)
    #obj_int.setLength(n_line)
    #obj_int.setAccessMode('READ')
    #obj_int.renderHdr()
    #obj_int.renderVRT()

    #This is in complex format but if you want to save in float:

    #out_img = isceobj.createImage()
    #out_img.load(outputint_name + '.xml')
    #out_img.renderHdr()
    cmd = 'gdal_translate -of ENVI -co INTERLEAVE=BIL ' + coh_out_name + '.vrt ' + coh_out_name
    os.system(cmd)
    import pdb; pdb.set_trace()

    #If you want to add metadata to art files:

    ds = gdal.Open(outputint_name, gdal.GA_ReadOnly)
    ds.SetMetadata({'plmethod': inps.plmethod})

    #atr = readfile.read_attribute(file)
    dataset_list= readfile.get_dataset_list(file)
    slice_list= readfile.get_slice_list(file)

    slice_list[0]

    i = 1
    unwrap_phase, atr = readfile.read(file, datasetName=slice_list[i])
    coherence, atr = readfile.read(file, datasetName=slice_list[i+int(len(slice_list)/3)])

    unwrap_phase = data[i,]
    coherence = data[i + data.shape[0],]
    '''
    

###########################################################################################


if __name__ == '__main__':
    main(sys.argv[1:])
