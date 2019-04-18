#! /usr/bin/env python3
############################################################
# Copyright(c) 2017, Sara Mirzaee                          #
############################################################
import numpy as np
import os
import gdal, osr
import argparse
from dataset_template import Template

########################################

EXAMPLE = """example:
  create_amplitude_tif.py LombokSenAT156VV.template 
"""


def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 0.1')
    parser.add_argument('custom_template_file', nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('-f', '--file', dest='inputfile', type=str, required=True, help='Input SLC')
    parser.add_argument('-b', '--bbox', dest='bbox', type=str, default='',
                        help="Bounding box (SNWE) ex: '20 21 110 111'")

    return parser


def command_line_parse(iargs=None):
    """ Parses command line agurments into inps variable. """

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    return inps


def array2raster(newRasterfn,gtransform,array):

    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    dst_options = ['COMPRESS=LZW']
    dst_nbands = 1
    outRaster = driver.Create(newRasterfn, cols, rows, dst_nbands, gdal.GDT_Float32, dst_options)
    outRaster.SetGeoTransform(gtransform)
    outband = outRaster.GetRasterBand(1)
    outband.SetMetadata({'SAT': 'S1'})                         # Could be:{ERS, ENV, S1, RS1, RS2, CSK, TSX, JERS, ALOS, ALOS2, NISAR}
    outband.SetMetadata({'Mode': 'Desc'})                      # Could be:{Asc, Desc}
    outband.SetMetadata({'Image Type': 'Ortho_BackScatter'})   # Could be:{Ortho_BackScatter, Geo_BackScatter, Ortho_Coherence, Ortho_Interferogram, ...}
    outband.SetMetadata({'Date': slc})                         # Date (YYYYMMDD format)    
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(4326)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def main(iargs=None):
    """
    Crops SLC images from Isce merged/SLC directory, multilooks and saves the amplitudes
    both in geo coordinates and radar coordinated.
    """

    inps = command_line_parse(iargs)

    inps.template = Template(inps.custom_template_file).get_options()

    project_name = os.path.basename(inps.custom_template_file).partition('.')[0]
    project_dir = os.getenv('SCRATCHDIR') + '/' + project_name
    slave_dir = project_dir + '/merged/SLC'
    geo_master_dir = project_dir + '/merged/geom_master'
    pic_dir =  project_dir + '/amplitude_pic'

    os.chdir(slave_dir)
    try:
        os.system('rm '+inps.inputfile + '/geo*')
    except:
        print('geocoding ...')


    if not os.path.exists(pic_dir):
        os.mkdir(pic_dir)

    print(inps.bbox)
    inps.bbox = [val for val in inps.bbox.split()]
    if len(inps.bbox) != 4:
        raise Exception('Bbox should contain 4 floating point values')

    lon_west = np.float(inps.bbox[2])
    lon_east = np.float(inps.bbox[3])
    lat_south = np.float(inps.bbox[0])
    lat_north = np.float(inps.bbox[1])




    slc = inps.inputfile

    os.chdir(os.path.join(slave_dir, slc))


    command_geocode = "geocodeGdal.py -l {a} -L {b} -f {c} --bbox '{l1} {l2} {L1} {L2}' -x {X} -y {Y}".format(
        a = geo_master_dir+'/lat.rdr.full',
        b = geo_master_dir+'/lon.rdr.full',
        c = slc + '.slc.full',
        l1 = lat_south,
        l2 = lat_north,
        L1 = lon_west,
        L2 = lon_east,
        X = 0.0001,
        Y = 0.0001)


    print(command_geocode)

    os.system(command_geocode)

    gfile = 'geo_' + slc + '.slc.full'
    ds = gdal.Open(gfile + '.vrt', gdal.GA_ReadOnly)
    array = np.abs(ds.GetRasterBand(1).ReadAsArray())
    del ds

    ##
    array = np.where(array > 0, 10.0 * np.log10(pow(array,2)) - 83.0, array)

    dst_file = 'Ortho_' + slc + '_backscatter.tif'

    data = gdal.Open(gfile, gdal.GA_ReadOnly)
    transform = data.GetGeoTransform()

    ## add metadata:

    ds.SetMetadata({'SAT': 'S1'})                         # Could be:{ERS, ENV, S1, RS1, RS2, CSK, TSX, JERS, ALOS, ALOS2, NISAR}
    ds.SetMetadata({'Mode': 'Desc'})                      # Could be:{Asc, Desc}
    ds.SetMetadata({'Image Type': 'Ortho_BackScatter'})   # Could be:{Ortho_BackScatter, Geo_BackScatter, Ortho_Coherence, Ortho_Interferogram, ...}
    ds.SetMetadata({'Date': slc})                         # Date (YYYYMMDD format)

    ##

    array2raster(dst_file, transform, array)

    print('Find the output in {}'.format(pic_dir))

    os.system('mv *.tif '+ pic_dir)
    #os.system('rm geo*')



if __name__ == '__main__':
    '''
    Crop SLCs.
    '''
    main()
