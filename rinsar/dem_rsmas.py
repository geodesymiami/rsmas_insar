#! /usr/bin/env python3
###############################################################################
#
# Project: dem_rsmas.py
# Author: Kawan & Falk Amelung
# Created:9/2018
#
# Notes for refactoring:
#   - use sentinelStack defaults (scurrently 'ssara' is given but ignored
#   - use datast_template
#   - for bounddingBox create a call_isce_dem function
#   - in ssara part, use GDAL class instead of  parsing the gdalinfo output

###############################################################################

import os
import sys
import glob
import argparse
import shutil
import re
import subprocess
from rinsar.objects import message_rsmas, dataset_template
from pysar.utils import readfile
from rinsar.utils.download_ssara_rsmas import add_polygon_to_ssaraopt

EXAMPLE = '''
  example:
  dem_rsmas.py  $SAMPLES/GalapagosT128SenVVD.template
      uses sentinelStack.boundingBox to generate a dem in DEM folder as dem.py requires integer degrees
      options:
           sentinelStack.demMethod = boundingBox [default: ssara]

      subtracts/adds ` 0.5 degree and then rounds to full integer
      '-1 0.15 -91.3 -90.9' -- >'-2 1 -92 -90
     work for islands where zip files may be missing
'''

def main(args):
    command = os.path.basename(__file__) + ' ' + ' '.join(args[1:])
    message_rsmas.log(command)

    # set defaults: ssara=True is set in dem_parser, use custom_pemp[late field if given
    inps = dem_parser()
    custom_template = readfile.read_template(inps.custom_template_file)

    if 'sentinelStack.demMethod' in list(custom_template.keys()):
        if custom_template['sentinelStack.demMethod'] == 'ssara':
           inps.flag_ssara = True
           inps.flag_boundingBox = False
        if custom_template['sentinelStack.demMethod'] == 'boundingBox':
           inps.flag_ssara = False
           inps.flag_boundingBox = True

    # print( 'flag_ssara: ' +str(inps.flag_ssara))
    # print( 'flag_boundingBox : ' + str(inps.flag_boundingBox))

    cwd = make_dem_dir()

    if inps.flag_ssara:

        call_ssara_dem(custom_template, inps, cwd)

        print('You have finished SSARA!')
    elif inps.flag_boundingBox:
        print('DEM generation using ISCE')
        bbox = custom_template['sentinelStack.boundingBox']
        south = bbox.split(' ')[0].split('\'')[1]   # assumes quotes '-1 0.15 -91.3 -91.0'
        north = bbox.split(' ')[1]
        west = bbox.split(' ')[2]
        east = bbox.split(' ')[3].split('\'')[0]

        south = round(float(south) - 0.5)
        north = round(float(north) + 0.5)
        west = round(float(west) - 0.5)
        east = round(float(east) + 0.5)

        demBbox = str(int(south)) + ' ' + str(int(north)) + ' ' + str(int(west)) + ' ' + str(int(east))
        cmd = 'dem.py -a stitch -b ' + demBbox + ' -c -u https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/'
        message_rsmas.log(cmd)

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        except subprocess.CalledProcessError as exc:
            print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
            sys.exit('Error produced by dem.py')
        else:
            if 'Could not create a stitched DEM. Some tiles are missing' in output:
                os.chdir('..')
                shutil.rmtree('DEM')
                sys.exit('Error in dem.py: Tiles are missing. Ocean???')

        xmlFile = glob.glob('demLat_*.wgs84.xml')[0]
        fin = open(xmlFile, 'r')
        fout = open("tmp.txt", "wt")
        for line in fin:
            fout.write(line.replace('demLat', cwd + '/demLat'))
        fin.close()
        fout.close()
        os.rename('tmp.txt', xmlFile)

    else:
        sys.ext('Error unspported demMethod option: ' + custom_template['sentinelStack.demMethod'])

    print('\n###############################################')
    print('End of dem_rsmas.py')
    print('################################################\n')

def call_ssara_dem(custom_template, inps, cwd):
    print('DEM generation using SSARA')
    out_file = 'ssara_dem.log'

    # need to refactor so that Josh's dataset_template will be used throughout
    dset_template = dataset_template.Template(inps.custom_template_file)
    ssaraopt_string = dset_template.generate_ssaraopt_string()
    ssaraopt_list = ssaraopt_string.split(' ')
    ssaraopt_list = add_polygon_to_ssaraopt(dset_template, ssaraopt_list.copy(), delta_lat=0)
    ssaraopt_string = ' '.join(ssaraopt_list)
    custom_template['ssaraopt'] = ssaraopt_string

    command = 'ssara_federated_query.py {ssaraopt} --dem >& {outfile}'.format(ssaraopt=custom_template['ssaraopt'], outfile=out_file)
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()
    print('downloaded dem.grd')
    grd_to_envi_and_vrt()
    grd_to_xml(cwd)

def dem_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Options dem geneation method: SSARA or BBOX (ISCE).',
                                     epilog=EXAMPLE)
    parser.add_argument('custom_template_file',
                        nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('--ssara',
                        dest='flag_ssara',
                        action='store_true',
                        default=True,
                        help='run ssara_federated_query w/ grd output file, set as default')
    parser.add_argument('--boundingBox',
                        dest='flag_boundingBox',
                        action='store_true',
                        default=False,
                        help='run dem.py from isce using boundingBox as lat/long bounding box')

    inps = parser.parse_args()

    # switch off ssara (default) if boundingBox is selected
    if inps.flag_boundingBox and inps.flag_ssara:
       inps.flag_ssara = False

    return inps

def make_dem_dir():
    if os.path.isdir('DEM'):
        shutil.rmtree('DEM')
    os.mkdir('DEM')
    os.chdir('DEM')
    return os.getcwd()

def grd_to_xml(cwd):
    print('you have started grd_to_xml')

    filename = 'dem.grd'
    outfilexml = 'dem.dem.wgs84.xml'
    outfilevrt = 'dem.dem.wgs84.vrt'
    gdalinfopath = 'gdalinfo'
    command = '{gdalinfopath} {file}'.format(gdalinfopath = gdalinfopath, file=filename)
    print(command)

    tempstr = subprocess.getoutput(command)

    # FA: it should be possible to retrieve the attributess from the objext but I did not find which fields
    #from osgeo import gdal
    #from gdalconst import GA_ReadOnly
    #dataset = gdal.Open(filename,gdal.GA_ReadOnly)
    #dataset.GetGeoTransform()
    #ul = dataset.GetGeoTransform()
    #dataset.RasterXSize

    xmlparamters = dict()

    xmlparamters['c1delta'] = re.findall(r'Pixel Size = \((.+),.+\)', tempstr)[0]
    xmlparamters['c1ev'] = round(float(re.findall(r'Upper Right\s+\( (.\d+.\d+),', tempstr)[0]), 1)
    xmlparamters['c1size'] = int(re.findall(r'Size is (\d+),\s+\d+', tempstr)[0])
    xmlparamters['c1sv'] = round(float(re.findall(r'Lower Left\s+\( (.\d+.\d+),', tempstr)[0]), 1)

    xmlparamters['c2delta'] = re.findall(r'Pixel Size = \(.+,(.+)\)', tempstr)[0]
    xmlparamters['c2ev'] = round(float(re.findall(r'Lower Left\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)
    xmlparamters['c2size'] = int(re.findall(r'Size is \d+,\s+(\d+)', tempstr)[0])
    xmlparamters['c2sv'] = round(float(re.findall(r'Upper Right\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)

    xmlparamters['numbands'] = re.findall(r'Band (\d+) \w', tempstr)[0]
    xmlparamters['ref'] = re.findall(r'GEOGCS\["(.+)",', tempstr)[0].replace(' ', '')
    xmlparamters['length'] = xmlparamters['c2size']
    xmlparamters['width'] = xmlparamters['c1size']
    xmlparamters['xmax'] = xmlparamters['c1ev']
    xmlparamters['xmin'] = xmlparamters['c1sv']
    xmlparamters['filename'] = cwd + '/' + outfilexml
    xmlparamters['extrafilename'] = cwd + '/' + outfilevrt

    with(open(outfilexml, 'w')) as out:
        out.write(xmltext.format(**xmlparamters))

def grd_to_envi_and_vrt():
    # Commands to create ENVI .hdr Labelled Raster and vrt xml file
    command = '''gdal_translate -ot Int16 -of ENVI dem.grd dem.dem.wgs84;
                 gdal_translate -of vrt dem.grd dem.dem.wgs84.xml.vrt'''
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()

#####################################################################################
xmltext = '''
<imageFile>
    <property name="ISCE_VERSION">
        <value>Release: 2.0.0_20170403, svn-2256, 20170403. Current: svn-exported.</value>
    </property>
    <property name="access_mode">
        <value>read</value>
        <doc>Image access mode.</doc>
    </property>
    <property name="byte_order">
        <value>l</value>
        <doc>Endianness of the image.</doc>
    </property>
    <component name="coordinate1">
        <factorymodule>isceobj.Image</factorymodule>
        <factoryname>createCoordinate</factoryname>
        <doc>First coordinate of a 2D image (width).</doc>
        <property name="delta">
            <value>{c1delta}</value>
            <doc>Coordinate quantization.</doc>
        </property>
        <property name="endingvalue">
            <value>{c1ev}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
        <property name="family">
            <value>imagecoordinate</value>
            <doc>Instance family name</doc>
        </property>
        <property name="name">
            <value>imagecoordinate_name</value>
            <doc>Instance name</doc>
        </property>
        <property name="size">
            <value>{c1size}</value>
            <doc>Coordinate size.</doc>
        </property>
        <property name="startingvalue">
            <value>{c1sv}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
    </component>
    <component name="coordinate2">
        <factorymodule>isceobj.Image</factorymodule>
        <factoryname>createCoordinate</factoryname>
        <doc>Second coordinate of a 2D image (length).</doc>
        <property name="delta">
            <value>{c2delta}</value>
            <doc>Coordinate quantization.</doc>
        </property>
        <property name="endingvalue">
            <value>{c2ev}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
        <property name="family">
            <value>imagecoordinate</value>
            <doc>Instance family name</doc>
        </property>
        <property name="name">
            <value>imagecoordinate_name</value>
            <doc>Instance name</doc>
        </property>
        <property name="size">
            <value>{c2size}</value>
            <doc>Coordinate size.</doc>
        </property>
        <property name="startingvalue">
            <value>{c2sv}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
    </component>
    <property name="data_type">
        <value>short</value>
        <doc>Image data type.</doc>
    </property>
    <property name="extra_file_name">
        <value>{extrafilename}</value>
        <doc>For example name of vrt metadata.</doc>
    </property>
    <property name="family">
        <value>demimage</value>
        <doc>Instance family name</doc>
    </property>
    <property name="file_name">
        <value>{filename}</value>
        <doc>Name of the image file.</doc>
    </property>
    <property name="image_type">
        <value>dem</value>
        <doc>Image type used for displaying.</doc>
    </property>
    <property name="length">
        <value>{length}</value>
        <doc>Image length</doc>
    </property>
    <property name="name">
        <value>demimage_name</value>
        <doc>Instance name</doc>
    </property>
    <property name="number_bands">
        <value>{numbands}</value>
        <doc>Number of image bands.</doc>
    </property>
    <property name="reference">
        <value>{ref}</value>
        <doc>Geodetic datum</doc>
    </property>
    <property name="scheme">
        <value>BIP</value>
        <doc>Interleaving scheme of the image.</doc>
    </property>
    <property name="width">
        <value>{width}</value>
        <doc>Image width</doc>
    </property>
    <property name="xmax">
        <value>{xmax}</value>
        <doc>Maximum range value</doc>
    </property>
    <property name="xmin">
        <value>{xmin}</value>
        <doc>Minimum range value</doc>
    </property>
</imageFile>'''

vrttext = '''
<VRTDataset rasterXSize="{c1size}" rasterYSize="{c2size}">
    <SRS>{srs}</SRS>
    <GeoTransform>{geotransform}</GeoTransform>
    <VRTRasterBand band="{numbands}" dataType="{datatype}" subClass="VRTRawRasterBand">
        <SourceFilename relativeToVRT="1">{sfilename}</SourceFilename>
        <ByteOrder>LSB</ByteOrder>
        <ImageOffset>0</ImageOffset>
        <PixelOffset>2</PixelOffset>
        <LineOffset>{lineoffset}</LineOffset>
    </VRTRasterBand>
</VRTDataset>'''


def call_ssara_dem(inps, cwd):
    print('DEM generation using SSARA')
    out_file = 'ssara_dem.log'

    command = 'ssara_federated_query.py {ssaraopt} --dem >& {outfile}'.format(ssaraopt=inps.ssaraopt,
                                                                              outfile=out_file)
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()
    print('downloaded dem.grd')
    grd_to_envi_and_vrt()
    grd_to_xml(cwd)   ## need re package


def dem_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Options dem geneation method: SSARA or BBOX (ISCE).',
                                     epilog=EXAMPLE)
    parser.add_argument('customTemplateFile',
                        nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('--ssara',
                        dest='flag_ssara',
                        action='store_true',
                        default=True,
                        help='run ssara_federated_query w/ grd output file, set as default')
    parser.add_argument('--boundingBox',
                        dest='flag_boundingBox',
                        action='store_true',
                        default=False,
                        help='run dem.py from isce using boundingBox as lat/long bounding box')

    inps = parser.parse_args()

    # switch off ssara (default) if boundingBox is selected
    if inps.flag_boundingBox and inps.flag_ssara:
        inps.flag_ssara = False

    return inps


def make_dem_dir(dem_dir):
    if os.path.isdir(dem_dir):
        shutil.rmtree(dem_dir)
    os.mkdir(dem_dir)
    os.chdir(dem_dir)
    return os.getcwd()


def grd_to_xml(cwd):
    print('you have started grd_to_xml')

    filename = 'dem.grd'
    outfilexml = 'dem.dem.wgs84.xml'
    outfilevrt = 'dem.dem.wgs84.vrt'
    gdalinfopath = 'gdalinfo'
    command = '{gdalinfopath} {file}'.format(gdalinfopath=gdalinfopath, file=filename)
    print(command)

    tempstr = subprocess.getoutput(command)

    # FA: it should be possible to retrieve the attributess from the objext but I did not find which fields
    # from osgeo import gdal
    # from gdalconst import GA_ReadOnly
    # dataset = gdal.Open(filename,gdal.GA_ReadOnly)
    # dataset.GetGeoTransform()
    # ul = dataset.GetGeoTransform()
    # dataset.RasterXSize

    xmlparamters = dict()

    xmlparamters['c1delta'] = re.findall(r'Pixel Size = \((.+),.+\)', tempstr)[0]
    xmlparamters['c1ev'] = round(float(re.findall(r'Upper Right\s+\( (.\d+.\d+),', tempstr)[0]), 1)
    xmlparamters['c1size'] = int(re.findall(r'Size is (\d+),\s+\d+', tempstr)[0])
    xmlparamters['c1sv'] = round(float(re.findall(r'Lower Left\s+\( (.\d+.\d+),', tempstr)[0]), 1)

    xmlparamters['c2delta'] = re.findall(r'Pixel Size = \(.+,(.+)\)', tempstr)[0]
    xmlparamters['c2ev'] = round(float(re.findall(r'Lower Left\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)
    xmlparamters['c2size'] = int(re.findall(r'Size is \d+,\s+(\d+)', tempstr)[0])
    xmlparamters['c2sv'] = round(float(re.findall(r'Upper Right\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)

    xmlparamters['numbands'] = re.findall(r'Band (\d+) \w', tempstr)[0]
    xmlparamters['ref'] = re.findall(r'GEOGCS\["(.+)",', tempstr)[0].replace(' ', '')
    xmlparamters['length'] = xmlparamters['c2size']
    xmlparamters['width'] = xmlparamters['c1size']
    xmlparamters['xmax'] = xmlparamters['c1ev']
    xmlparamters['xmin'] = xmlparamters['c1sv']
    xmlparamters['filename'] = cwd + '/' + outfilexml
    xmlparamters['extrafilename'] = cwd + '/' + outfilevrt

    with(open(outfilexml, 'w')) as out:
        out.write(xmltext.format(**xmlparamters))


def grd_to_envi_and_vrt():
    # Commands to create ENVI .hdr Labelled Raster and vrt xml file
    command = '''gdal_translate -ot Int16 -of ENVI dem.grd dem.dem.wgs84;
                 gdal_translate -of vrt dem.grd dem.dem.wgs84.xml.vrt'''
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()


#####################################################################################
xmltext = '''
<imageFile>
    <property name="ISCE_VERSION">
        <value>Release: 2.0.0_20170403, svn-2256, 20170403. Current: svn-exported.</value>
    </property>
    <property name="access_mode">
        <value>read</value>
        <doc>Image access mode.</doc>
    </property>
    <property name="byte_order">
        <value>l</value>
        <doc>Endianness of the image.</doc>
    </property>
    <component name="coordinate1">
        <factorymodule>isceobj.Image</factorymodule>
        <factoryname>createCoordinate</factoryname>
        <doc>First coordinate of a 2D image (width).</doc>
        <property name="delta">
            <value>{c1delta}</value>
            <doc>Coordinate quantization.</doc>
        </property>
        <property name="endingvalue">
            <value>{c1ev}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
        <property name="family">
            <value>imagecoordinate</value>
            <doc>Instance family name</doc>
        </property>
        <property name="name">
            <value>imagecoordinate_name</value>
            <doc>Instance name</doc>
        </property>
        <property name="size">
            <value>{c1size}</value>
            <doc>Coordinate size.</doc>
        </property>
        <property name="startingvalue">
            <value>{c1sv}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
    </component>
    <component name="coordinate2">
        <factorymodule>isceobj.Image</factorymodule>
        <factoryname>createCoordinate</factoryname>
        <doc>Second coordinate of a 2D image (length).</doc>
        <property name="delta">
            <value>{c2delta}</value>
            <doc>Coordinate quantization.</doc>
        </property>
        <property name="endingvalue">
            <value>{c2ev}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
        <property name="family">
            <value>imagecoordinate</value>
            <doc>Instance family name</doc>
        </property>
        <property name="name">
            <value>imagecoordinate_name</value>
            <doc>Instance name</doc>
        </property>
        <property name="size">
            <value>{c2size}</value>
            <doc>Coordinate size.</doc>
        </property>
        <property name="startingvalue">
            <value>{c2sv}</value>
            <doc>Starting value of the coordinate.</doc>
        </property>
    </component>
    <property name="data_type">
        <value>short</value>
        <doc>Image data type.</doc>
    </property>
    <property name="extra_file_name">
        <value>{extrafilename}</value>
        <doc>For example name of vrt metadata.</doc>
    </property>
    <property name="family">
        <value>demimage</value>
        <doc>Instance family name</doc>
    </property>
    <property name="file_name">
        <value>{filename}</value>
        <doc>Name of the image file.</doc>
    </property>
    <property name="image_type">
        <value>dem</value>
        <doc>Image type used for displaying.</doc>
    </property>
    <property name="length">
        <value>{length}</value>
        <doc>Image length</doc>
    </property>
    <property name="name">
        <value>demimage_name</value>
        <doc>Instance name</doc>
    </property>
    <property name="number_bands">
        <value>{numbands}</value>
        <doc>Number of image bands.</doc>
    </property>
    <property name="reference">
        <value>{ref}</value>
        <doc>Geodetic datum</doc>
    </property>
    <property name="scheme">
        <value>BIP</value>
        <doc>Interleaving scheme of the image.</doc>
    </property>
    <property name="width">
        <value>{width}</value>
        <doc>Image width</doc>
    </property>
    <property name="xmax">
        <value>{xmax}</value>
        <doc>Maximum range value</doc>
    </property>
    <property name="xmin">
        <value>{xmin}</value>
        <doc>Minimum range value</doc>
    </property>
</imageFile>'''

vrttext = '''
<VRTDataset rasterXSize="{c1size}" rasterYSize="{c2size}">
    <SRS>{srs}</SRS>
    <GeoTransform>{geotransform}</GeoTransform>
    <VRTRasterBand band="{numbands}" dataType="{datatype}" subClass="VRTRawRasterBand">
        <SourceFilename relativeToVRT="1">{sfilename}</SourceFilename>
        <ByteOrder>LSB</ByteOrder>
        <ImageOffset>0</ImageOffset>
        <PixelOffset>2</PixelOffset>
        <LineOffset>{lineoffset}</LineOffset>
    </VRTRasterBand>
</VRTDataset>'''

###########################################################################################
if __name__ == '__main__':
    main(sys.argv[:])
