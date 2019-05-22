#! /usr/bin/env python3
############################################################
# Copyright(c) 2017, Sara Mirzaee                          #
############################################################
import numpy as np
import os
import sys
import gdal
import osr
import argparse
import glob
from minsar.objects.dataset_template import Template
from minsar.objects.auto_defaults import PathFind
from minsar.utils.process_utilities import xmlread, create_or_update_template
from minsar.objects import message_rsmas

pathObj = PathFind()
########################################

EXAMPLE = """example:
  create_amplitude_tif.py LombokSenAT156VV.template 
"""


def main(iargs=None):
    """
    Crops SLC images from Isce merged/SLC directory and creates georectified and orthorectified products.
    """

    message_rsmas.log(os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1::]))

    inps = command_line_parse(iargs)
    project_name = os.path.basename(inps.customTemplateFile).partition('.')[0]
    project_dir = os.getenv('SCRATCHDIR') + '/' + project_name
    slave_dir = os.path.join(project_dir, pathObj.mergedslcdir)
    pic_dir = os.path.join(project_dir, pathObj.tiffdir)
    inps = create_or_update_template(inps)

    os.chdir(slave_dir)

    slc = inps.inputfile

    if inps.imtype == 'ortho':
        geo_master_dir = os.path.join(project_dir, pathObj.geomasterdir)
    else:
        geo_master_dir = os.path.join(project_dir, pathObj.geomlatlondir)


    try:
        os.system('rm '+inps.inputfile + '/geo*')
    except:
        print('geocoding ...')

    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    os.chdir(os.path.join(slave_dir, inps.inputfile))

    geocode_file(inps.inputfile, inps.cropbox, geo_master_dir, inps.latStep, inps.lonStep)

    gfile = 'geo_' + slc + '.slc.ml'
    ds = gdal.Open(gfile + '.vrt', gdal.GA_ReadOnly)
    array = np.abs(ds.GetRasterBand(1).ReadAsArray())
    del ds

    ##
    array = np.where(array > 0, 10.0 * np.log10(pow(array,2)) - 83.0, array)

    if inps.imtype == 'ortho':
        dst_file = 'orthorectified_' + slc + '_backscatter.tif'
    else:
        dst_file = 'georectified_' + slc + '_backscatter.tif'

    data = gdal.Open(gfile, gdal.GA_ReadOnly)
    transform = data.GetGeoTransform()

    ##
    xmlfile = glob.glob(os.path.join(project_dir, pathObj.masterdir, '*.xml'))[0]
    attributes = xmlread(xmlfile)
    Metadata = {'SAT': attributes['missionname'], 'Mode': attributes['passdirection'],
                'Image_Type': '{}_BackScatter'.format(inps.imtype), 'Date': slc}

    raster2geotiff(dst_file, transform, array, Metadata)

    print('Find the output in {}'.format(pic_dir))

    os.system('mv *.tif {}'.format(pic_dir))
    os.system('rm geo*')

    return


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('customTemplateFile', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('-f', '--file', dest='inputfile', type=str, required=True, help='Input SLC')
    parser.add_argument('-y', '--lat-step', dest='latStep', type=float,
                        help='output pixel size in degree in latitude.')
    parser.add_argument('-x', '--lon-step', dest='lonStep', type=float,
                        help='output pixel size in degree in longitude.')
    parser.add_argument('-t', '--type', dest='imtype', type=str, default='ortho',
                        help="ortho, geo")

    return parser


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps


def raster2geotiff(newRasterfn, gtransform, array, metadata):
    """
    Exports the raster data to a geotiff format.
    :param newRasterfn: the name of output geotiff file
    :param gtransform: geo transform object for gdal
    :param array: raster to be written to the file
    :param metadata: all other metadata to be attached to the file
    """

    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    dst_options = ['COMPRESS=LZW']
    dst_nbands = 1
    outRaster = driver.Create(newRasterfn, cols, rows, dst_nbands, gdal.GDT_Float32, dst_options)
    outRaster.SetGeoTransform(gtransform)
    outband = outRaster.GetRasterBand(1)
    outband.SetMetadata(metadata)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

    return


def geocode_file(slc, bbox, geo_master_dir, latStep, lonStep):
    """
    Geocodes the input file
    :param slc: input file
    :param bbox: bounding box to crop the output file
    :param geo_master_dir: where the geometry files are located
    """

    command_geocode = "geocodeGdal.py -l {a} -L {b} -f {c} --bbox '{box}' -x {X} -y {Y}".format(
        a=geo_master_dir + '/lat.rdr',
        b=geo_master_dir + '/lon.rdr',
        c=slc + '.slc.ml',
        box=bbox,
        X=latStep,
        Y=lonStep)

    print(command_geocode)
    os.system(command_geocode)
    return


if __name__ == '__main__':
    '''
    Crop SLCs.
    '''
    main()
