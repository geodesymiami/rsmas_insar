#! /usr/bin/env python3
###############################################################################
#
# Project: dem_rsmas.py
# Author: Kawan & Falk Amelung
# Created:9/2018
#
# Notes for refactoring:
#   - use topsStack defaults (scurrently 'ssara' is given but ignored
#   - use datast_template
#   - for boundingBox create a call_isce_dem function
#   - in ssara part, use GDAL class instead of  parsing the gdalinfo output

###############################################################################

import os
import sys
import glob
import shutil
import re
import subprocess
import math
from minsar.objects import message_rsmas
from minsar.old_generate_download_command import add_polygon_to_ssaraopt
from minsar.utils.process_utilities import cmd_line_parse
from minsar.utils import get_boundingBox_from_kml
from minsar.job_submission import JOB_SUBMIT

#from minsar.download_rsmas import ssh_with_commands

EXAMPLE = '''
  example:
  dem_rsmas.py  $SAMPLES/GalapagosT128SenVVD.template
      uses topsStack.boundingBox or stripmapStack.boundingBox to generate a dem in DEM folder as dem.py requires integer degrees
      options:
           topsStack.demMethod = boundingBox [default: ssara]
      subtracts/adds ` 0.5 degree and then rounds to full integer
      '-1 0.15 -91.3 -90.9' -- >'-2 1 -92 -90
     work for islands where zip files may be missing
'''


def main(iargs=None):
    # set defaults: ssara=True is set in dem_parser, use custom_pemp[late field if given
    inps = cmd_line_parse(iargs, script='dem_rsmas')

    if not iargs is None:
        input_arguments = iargs
    else:
        input_arguments = sys.argv[1::]

    message_rsmas.log(inps.work_dir, os.path.basename(__file__) + ' ' + ' '.join(input_arguments))
    
    inps.out_dir = inps.work_dir
    inps.num_data = 1

    job_obj = JOB_SUBMIT(inps)
    #########################################
    # Submit job
    #########################################

    if inps.submit_flag:
        job_name = 'dem_rsmas'
        job_file_name = job_name
        if '--submit' in input_arguments:
            input_arguments.remove('--submit')
        command = [os.path.abspath(__file__)] + input_arguments
        job_obj.submit_script(job_name, job_file_name, command)
        sys.exit(0)


    if not inps.flag_boundingBox and not inps.flag_ssara:
        if 'demMethod' in list(inps.template.keys()):
            if inps.template['demMethod'] == 'ssara':
                inps.flag_ssara = True
                inps.flag_boundingBox = False
            if inps.template['demMethod'] == 'boundingBox':
                inps.flag_ssara = False
                inps.flag_boundingBox = True
    elif inps.flag_boundingBox:
        inps.flag_ssara = False
    else:
        inps.flag_ssara = True

    dem_dir = os.path.join(inps.work_dir, 'DEM')
    if not exist_valid_dem_dir(dem_dir):
        os.mkdir(dem_dir)

    try:
       inps.slc_dir = inps.template['topsStack.slcDir']
    except:
       inps.slc_dir = os.path.join(inps.work_dir, 'SLC')

    # 10/21: inps.template['topsStack.slcDir'] may contain ./SLC  (it would be better to change where topsStack.slcDir is assigned)
    if '.' in inps.slc_dir:
       inps.slc_dir = inps.slc_dir.replace(".",os.getcwd())

    if 'COSMO-SKYMED' in inps.ssaraopt:
       inps.slc_dir = inps.slc_dir.replace('SLC','RAW_data')
    if 'TSX' in inps.ssaraopt:
       inps.slc_dir = inps.slc_dir.replace('SLC','SLC_ORIG')
      
    # FA 10/2021: We probably should check here whether a DEM/*wgs84 file exist and exit if it does.
    # That could save time. On the other hand, most steps allow to be run even if data exist
    os.chdir(dem_dir)

    if inps.flag_ssara:

        call_ssara_dem(inps, dem_dir)

        print('You have finished SSARA!')
        cmd = 'fixImageXml.py -f -i {}'.format(glob.glob(dem_dir + '/dem*.wgs84')[0])
        os.system(cmd)

    elif inps.flag_boundingBox or inps.flag_ssara_kml:
        print('DEM generation using ISCE based on *kml file')
        if inps.flag_boundingBox:
           bbox = inps.template[inps.prefix + 'Stack.boundingBox'].strip("'")

        if inps.flag_ssara_kml:

           try:
              ssara_kml_file=sorted( glob.glob(inps.slc_dir + '/ssara_search_*.kml') )[-1]
              #ssara_kml_file=sorted( glob.glob(inps.work_dir + '/SLC/ssara_search_*.kml') )[-1]
           except:
              # FA 8/2023: If there is no kml file or bbox emty it should rerun ssara to get a kml file
              raise FileExistsError('No SLC/ssara_search_*.kml found')

           print('using kml file:',ssara_kml_file)

           try:
              bbox = get_boundingBox_from_kml.main( [ssara_kml_file, '--delta_lon' , '0'] )
           except:
              raise Exception('Problem with *kml file: does not contain bbox information')
           bbox = bbox.split('SNWE:')[1]

        print('bbox:',bbox)
        bbox = [val for val in bbox.split()]

        south = bbox[0]
        north = bbox[1]
        west = bbox[2]
        east = bbox[3].split('\'')[0]

        south = math.floor(float(south) - 0.5)
        north = math.ceil(float(north) + 0.5)
        west = math.floor(float(west) - 0.5)
        east = math.ceil(float(east) + 0.5)

        demBbox = str(int(south)) + ' ' + str(int(north)) + ' ' + str(int(west)) + ' ' + str(int(east))
        command = 'dem.py -a stitch --filling --filling_value 0 -b ' + demBbox + ' -c -u https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/'

        message_rsmas.log(os.getcwd(), command)

        if os.getenv('DOWNLOADHOST') == 'local':
            try:
                #FA 8/2023: instead of calling dem.py here should import dem.py and call dem.main( (or similar))
                proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                        universal_newlines=True)
                output, error = proc.communicate()
                print(error)
                if proc.returncode is not 0:
                    #raise Exception(
                    #    'ERROR starting dem.py subprocess')  # FA 8/19: I don't think this happens, errors are is output
                    print('FA 8/23: dem.py returns error. SKIPPING because it may happen because of poor dem.py call')
                print(output)
                print(error, file=sys.stderr)
            except subprocess.CalledProcessError as exc:
                print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
                sys.exit('Error produced by dem.py')
            else:
                if 'Could not create a stitched DEM. Some tiles are missing' in output:
                    os.chdir('..')
                    shutil.rmtree('DEM')
                    sys.exit('Error in dem.py: Tiles are missing. Ocean???')
        else:
            dem_dir = os.getcwd()
            ssh_command_list = ['s.bgood', 'cd {0}'.format(dem_dir), command]
            host = os.getenv('DOWNLOADHOST')
            try:
                status = ssh_with_commands(host, ssh_command_list)
            except subprocess.CalledProcessError as exc:
                print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
                sys.exit('Error produced by dem.py using ' + host)

        #cmd = 'fixImageXml.py -f -i {}'.format(glob.glob(dem_dir + '/demLat_*.wgs84')[0])
        #os.system(cmd)

        # print('Exit status from dem.py: {0}'.format(status))

        # xmlFile = glob.glob('demLat_*.wgs84.xml')[0]

        # fin = open(xmlFile, 'r')
        # fout = open("tmp.txt", "wt")
        # for line in fin:
        #    fout.write(line.replace('demLat', dem_dir + '/demLat'))
        # fin.close()
        # fout.close()
        # os.rename('tmp.txt', xmlFile)

    else:
        sys.exit('Error unspported demMethod option: ' + inps.template['demMethod'])

    print('\n###############################################')
    print('End of dem_rsmas.py')
    print('################################################\n')

    return None


def call_ssara_dem(inps, cwd):
    print('DEM generation using SSARA');
    sys.stdout.flush()
    out_file = 'ssara_dem.log'

    # need to refactor so that Josh's dataset_template will be used throughout
    ssaraopt_string = inps.ssaraopt
    ssaraopt_list = ssaraopt_string.split(' ')
    ssaraopt_list = add_polygon_to_ssaraopt(dataset_template=inps.template, ssaraopt=ssaraopt_list.copy(), delta_lat=0)
    ssaraopt_string = ' '.join(ssaraopt_list)

    out_file = 'out_ssara_dem'
    command = 'ssara_federated_query.py {ssaraopt} --dem '.format(ssaraopt=ssaraopt_string)
    message_rsmas.log(os.getcwd(), command)
    command = '('+command+' | tee '+out_file+'.o) 3>&1 1>&2 2>&3 | tee '+out_file+'.e'
    print('command currently executing: ' + command); sys.stdout.flush()
    if os.getenv('DOWNLOADHOST') == 'local':
        print('Command: ' + command);
        sys.stdout.flush()
        try:
            proc = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True,
                                    universal_newlines=True)
            error, output = proc.communicate()  # FA 8/19 error, output works better here than output, error. Could be that stderr and stdout are switched .
            if proc.returncode is not 0:
                raise Exception(
                    'ERROR starting dem.py subprocess')  # FA 8/19: I don't think this happens, errors are is output
        except subprocess.CalledProcessError as exc:
            print("Command failed. Exit code, StdErr:", exc.returncode, exc.output)
            sys.exit('Error produced by ssara_federated_query.py')
        else:
            if not 'Downloading DEM' in output:
                os.chdir('..')
                shutil.rmtree('DEM')
                sys.exit('Error in dem.py: Tiles are missing. Ocean???')
    else:
        dem_dir = os.getcwd()
        ssh_command_list = ['s.bgood', 'cd {0}'.format(cwd), command]
        host = os.getenv('DOWNLOADHOST')
        status = ssh_with_commands(host, ssh_command_list)
        # print('status from ssh_with_commands:' + str(status)); sys.stdout.flush()

    print('Done downloading dem.grd');
    sys.stdout.flush()
    grd_to_envi_and_vrt()
    grd_to_xml(cwd)


def exist_valid_dem_dir(dem_dir):
    """ Returns True of a valid dem dir exist. Otherwise remove die and return False """
    if os.path.isdir(dem_dir):
        products = glob.glob(os.path.join(dem_dir, '*dem.wgs84*'))
        if len(products) >= 3:
            print('DEM products already exist. if not satisfying, remove the folder and run again')
            return True
        else:
            shutil.rmtree(dem_dir)
            return False
    else:
        return False


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
    xmlparamters['c1ev'] = float(re.findall(r'Upper Right\s+\(\s*(.\d+.\d+),', tempstr)[0])
    xmlparamters['c1size'] = int(re.findall(r'Size is (\d+),\s+\d+', tempstr)[0])
    xmlparamters['c1sv'] = float(re.findall(r'Lower Left\s+\(\s*(.\d+.\d+),', tempstr)[0])

    xmlparamters['c2delta'] = re.findall(r'Pixel Size = \(.+,(.+)\)', tempstr)[0]
    xmlparamters['c2ev'] = float(re.findall(r'Lower Left\s+\(\s*.\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0])
    xmlparamters['c2size'] = int(re.findall(r'Size is \d+,\s+(\d+)', tempstr)[0])
    xmlparamters['c2sv'] = float(re.findall(r'Upper Right\s+\(\s*.\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0])

    xmlparamters['numbands'] = re.findall(r'Band (\d+) \w', tempstr)[0]
    xmlparamters['ref'] = 'WGS84'  # FA 3/20: hardwired in
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
    main()
