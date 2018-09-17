#! /usr/bin/env python3
###############################################################################
#
# Project: dem_ssara_kawan.py
# Author: Kawan & Falk Amelung
# Created:9/2018
#
###############################################################################


import os
import sys
import glob
import argparse
import shutil
import subprocess
from . import messageRsmas
import re
from pysar.utils import readfile


EXAMPLE = '''
  example:
  dem_rsmas.py  $SAMPLES/GalapagosT128SenVVD.template

      uses sentinelStack.boundingBox to generate a dem in DEM folder as dem.py requires integer degrees

      options:
           sentinelStack.demMethod = ssara [default: bbox]

      subtracts/adds ` 0.5 degree and then rounds to full integer

      '-1 0.15 -91.3 -90.9' -- >'-2 1 -92 -90

     work for islands where zip files may be missing

'''

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

##########################################################################


def dem_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
                                     description='Options for SSARA, ISCE, and more? Default set to ISCE.',
                                     epilog=EXAMPLE)
    parser.add_argument('custom_template_file',
                        nargs='?',
                        help='custom template with option settings.\n')
    parser.add_argument('--ssara',
                        dest='ssara',
                        action='store_true',
                        help='run ssara_federated_query w/ grd output file')
    parser.add_argument('--isce',
                        dest='isce',
                        action='store_true',
                        help='run isce, set as default')

    inps = parser.parse_args()

    # set default to ISCE
    if inps.ssara:
        inps.isce = False
    else:
        inps.isce = True
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
    tempfile = 'dem.temp'
    outfilexml = 'dem.dem.wgs84.xml'
    outfilevrt = 'dem.dem.wgs84.vrt'
    command = '/nethome/famelung/test/test/rsmas_insar/3rdparty/python/anaconda2/bin/gdalinfo {file} >> {tempfile}'.format(file=filename, tempfile=tempfile)
    subprocess.Popen(command, shell=True).wait()

    with(open(tempfile, 'r')) as temp:
        fulldict = dict()
        tempstr = temp.read()

        fulldict['c1delta'] = re.findall(r'Pixel Size = \((.+),.+\)', tempstr)[0] 
        fulldict['c1ev'] = round(float(re.findall(r'Upper Right\s+\( (.\d+.\d+),', tempstr)[0]), 1)
        fulldict['c1size'] = int(re.findall(r'Size is (\d+),\s+\d+', tempstr)[0])  
        fulldict['c1sv'] = round(float(re.findall(r'Lower Left\s+\( (.\d+.\d+),', tempstr)[0]), 1)

        fulldict['c2delta'] = re.findall(r'Pixel Size = \(.+,(.+)\)', tempstr)[0]
        fulldict['c2ev'] = round(float(re.findall(r'Lower Left\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)
        fulldict['c2size'] = int(re.findall(r'Size is \d+,\s+(\d+)', tempstr)[0])
        fulldict['c2sv'] = round(float(re.findall(r'Upper Right\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]), 1)

        fulldict['numbands'] = re.findall(r'Band (\d+) \w', tempstr)[0]
        fulldict['ref'] = re.findall(r'GEOGCS\["(.+)",', tempstr)[0].replace(' ', '')
        fulldict['length'] = fulldict['c2size']
        fulldict['width'] = fulldict['c1size']
        fulldict['xmax'] = fulldict['c1ev']
        fulldict['xmin'] = fulldict['c1sv']
        fulldict['filename'] = cwd + '/' + outfilexml
        fulldict['extrafilename'] = cwd + '/' + outfilevrt

    #    fulldict['srs']= ':'.join (thing for thing in re.findall(r'UNIT.+\s.+\s.+AUTHORITY\["(\w+)","(\d+)"]]',tempstr)[0])
    #    fulldict['geotransform'] = '{c1sv}, {c1delta}, 0, {c2sv}, {c2delta}, 0' #north up images? for [2] and [4] see "affine geotransform" https://www.gdal.org/gdal_datamodel.html
    #    fulldict['datatype'] = re.findall(r'Type=([A-Za-z0-9]+)', tempstr)[0]
    #    fulldict['sfilename'] = outfilevrt
    #    fulldict['lineoffset'] = int(fulldict['c1size']) * 2 #how is lineoffset calculated

    os.remove(tempfile)

    # with(open(outfilevrt, 'w')) as out:
    #     out.write(vrttext.format(**fulldict))

    with(open(outfilexml, 'w')) as out:
        out.write(xmltext.format(**fulldict))
    return


def grd_to_envi_vrt():
    command = 'gdal_translate -ot Int16 -of ENVI dem.grd dem.dem.wgs84;gdal_translate -of vrt dem.grd dem.dem.wgs84.xml.vrt' 
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()
    return


def call_ssara_dem(custom_template, inps, cwd):
    print('You have started SSARA!')
    out_file = 'ssara_dem.log'
    command = 'ssara_federated_query.py {ssaraopt} --dem >& {outfile}'.format(ssaraopt=custom_template['ssaraopt'], outfile=out_file)
    print('command currently executing: ' + command)
    subprocess.Popen(command, shell=True).wait()
    print('dem.grd downloaded')
    grd_to_envi_vrt()
    grd_to_xml(cwd)
    return


def main(argv):

    messageRsmas.log(' '.join(argv))
    inps = dem_parser()
    custom_template = readfile.read_template(inps.custom_template_file)
    cwd = make_dem_dir()
    # can sentinelStack.demMethod be removed? I think parser is the replacement
    if 'sentinelStack.demMethod' not in list(custom_template.keys()):
        custom_template['sentinelStack.demMethod'] = '?'

    if custom_template['sentinelStack.demMethod'] == 'bbox' or custom_template['sentinelStack.demMethod'] == 'isce' or inps.isce:
        print('You hace started isce')
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
        messageRsmas.log(cmd)

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        except subprocess.CalledProcessError as exc:
            print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
            sys.exit('Error produced by dem.py')
        else:
            # print("Success.        StdOut \n{}\n".format(output))
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

    elif custom_template['sentinelStack.demMethod'] == 'ssara' or inps.ssara:
        call_ssara_dem(custom_template, inps, cwd)
        print('You have finished SSARA!')
    else:
        sys.ext('Error unspported demMethod option: ' + custom_template['sentinelStack.demMethod'])

    print('\n###############################################')
    print('End of dem_rsmas.py')
    print('################################################\n')

###########################################################################################
if __name__ == '__main__':
    main(sys.argv[:])
