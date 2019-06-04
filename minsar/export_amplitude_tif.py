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
import geocodeGdal as gg

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

    slc = inps.prodlist

    if inps.imtype == 'ortho':
        inps.geo_master_dir = os.path.join(project_dir, pathObj.geomasterdir)
    else:
        inps.geo_master_dir = os.path.join(project_dir, pathObj.geomlatlondir)


    try:
        os.system('rm '+inps.prodlist + '/geo*')
    except:
        print('geocoding ...')

    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    os.chdir(os.path.join(slave_dir, inps.prodlist))

    geocode_file(inps)

    gfile = 'geo_' + slc + '.slc.ml'
    ds = gdal.Open(gfile + '.vrt', gdal.GA_ReadOnly)
    array = np.abs(ds.GetRasterBand(1).ReadAsArray())
    del ds

    ##
    array = np.where(array > 0, 10.0 * np.log10(pow(array, 2)) - 83.0, array)

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
    parser.add_argument('-f', '--file', dest='prodlist', type=str, required=True, help='Input SLC')
    parser.add_argument('-l', '--lat', dest='latFile', type=str,
                        default='lat.rdr.ml', help='latitude file in radar coordinate')
    parser.add_argument('-L', '--lon', dest='lonFile', type=str,
                        default='lon.rdr.ml', help='longitude file in radar coordinate')
    parser.add_argument('-y', '--lat-step', dest='latStep', type=float,
                        help='output pixel size in degree in latitude.')
    parser.add_argument('-x', '--lon-step', dest='lonStep', type=float,
                        help='output pixel size in degree in longitude.')
    parser.add_argument('-o', '--xoff', dest='xOff', type=int, default=0,
                        help='Offset from the begining of geometry files in x direction. Default 0.0')
    parser.add_argument('-p', '--yoff', dest='yOff', type=int, default=0,
                        help='Offset from the begining of geometry files in y direction. Default 0.0')
    parser.add_argument('-r', '--resampling_method', dest='resamplingMethod', type=str, default='near',
                        help='Resampling method (gdalwarp resamplin methods)')
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


def geocode_file(inps):
    """
    Geocodes the input file
    :param inps: input name space
    """

    inps.cropbox = [val for val in inps.cropbox.split()]
    if len(inps.cropbox) != 4:
        raise Exception('Bbox should contain 4 floating point values')

    inps.latFile = os.path.abspath(os.path.join(inps.geo_master_dir, inps.latFile))
    inps.lonFile = os.path.abspath(os.path.join(inps.geo_master_dir, inps.lonFile))
    inps.prodlist = [inps.prodlist + '.slc.ml']

    WSEN = str(inps.cropbox[2]) + ' ' + str(inps.cropbox[0]) + ' ' + str(inps.cropbox[3]) + ' ' + str(inps.cropbox[1])
    latFile, lonFile = gg.prepare_lat_lon(inps)

    gg.getBound(latFile, float(inps.cropbox[0]), float(inps.cropbox[1]), 'lat')
    gg.getBound(lonFile, float(inps.cropbox[2]), float(inps.cropbox[3]), 'lon')

    for infile in inps.prodlist:
        infile = os.path.abspath(infile)
        print('geocoding ' + infile)
        outFile = os.path.join(os.path.dirname(infile), "geo_" + os.path.basename(infile))
        gg.writeVRT(infile, latFile, lonFile)

        cmd = 'gdalwarp -of ENVI -geoloc  -te ' + WSEN + ' -tr ' + str(inps.latStep) + ' ' + \
              str(inps.lonStep) + ' -srcnodata 0 -dstnodata 0 ' + ' -r ' + inps.resamplingMethod + \
              ' -co INTERLEAVE=BIL ' + infile + '.vrt ' + outFile
        print(cmd)
        os.system(cmd)

        # write_xml(outFile)
        cmd = "gdal2isce_xml.py -i " + outFile
        os.system(cmd)

    return


if __name__ == '__main__':
    '''
    Crop SLCs.
    '''
    main()
