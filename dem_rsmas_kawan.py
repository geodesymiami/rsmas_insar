#! /usr/bin/env python2
###############################################################################
# 
# Project: dem_ssara.py
# Author: Falk Amelung
# Created: 3/2018
#
###############################################################################


import os
import sys
import glob
import time
import argparse
import warnings
import shutil
import subprocess
import messageRsmas
from pysar.utils import readfile


import json
import fnmatch

EXAMPLE='''example:
  dem_rsmas.py  $SAMPLES/GalapagosT128SenVVD.template

      uses sentinelStack.boundingBox to generate a dem in DEM folder as dem.py requires integer degrees

      options:
           sentinelStack.demMethod = ssara [default: bbox]

      subtracts/adds ` 0.5 degree and then rounds to full integer

      '-1 0.15 -91.3 -90.9' -- >'-2 1 -92 -90

     work for islands where zip files may be missing

'''

XML='''<imageFile>
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
                        help='run ssara_federated_query w/ tiff output file')
    parser.add_argument('--isce',
                        dest='isce',
                        action='store_true',
                        help='run isce, set as default')
    
    inps = parser.parse_args()
    
    # set default to ISCE
    if inps.ssara:
        inps.isce = False
        print('inps.ssara')
    else:
        inps.isce = True
        print('inps.isce')
    return inps


def make_dem_dir():
    if os.path.isdir('DEM'):
       shutil.rmtree('DEM')
    os.mkdir('DEM')
    os.chdir('DEM')
    return os.getcwd()


def make_slc_dir():
    work_dir_slc = os.path.abspath(os.getcwd()) + '/SLC'

    if not os.path.isdir(work_dir_slc):
        os.mkdir(work_dir_slc)
    os.chdir(work_dir_slc)
    return work_dir_slc


def tiff_to_xml():
    print('you have started tiff_to_xml')

    command = 'unzip \'*.zip\''
    subprocess.Popen(command, shell=True).wait()
    
    # search for .tiff files
    for root, dirnames,filenames in os.walk('.'):
        for filename in fnmatch.filter(filenames, '*.tiff'): 
            tempfile = filename.replace('tiff','temp')
            outfile = filename.replace('tiff','xml')
            command = '/nethome/famelung/test/testqqqq/rsmas_insar/3rdparty/gdal/gdal-210_work/bin/gdalinfo {work_dir}/{file} >> {temp_file}'.format(work_dir= root,file= filename,temp_file=tempfile)
            subprocess.Popen(command, shell=True).wait()
            os.chdir(root)

            with(open(tempfile,'r')) as temp:
                xmldict= dict()
                tempstr= temp.read()
                print('TEST :', re.findall(r'GEOGCS\["(.+)",', tempstr)[0].replace(' ','')) 

                xmldict['c1delta']= re.findall(r'Pixel Size = \((.+),.+\)', tempstr)[0] 
                xmldict['c1ev']= round(float(re.findall(r'Upper Right\s+\( (.\d+.\d+),', tempstr)[0]),1)
                xmldict['c1size']= int(re.findall(r'Size is (\d+),\s+\d+',tempstr)[0])  
                xmldict['c1sv']= round(float(re.findall(r'Lower Left\s+\( (.\d+.\d+),', tempstr)[0]),1)

                xmldict['c2delta']= re.findall(r'Pixel Size = \(.+,(.+)\)', tempstr)[0]
                xmldict['c2ev']= round(float(re.findall(r'Lower Left\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]),1)
                xmldict['c2size']= int(re.findall(r'Size is \d+,\s+(\d+)',tempstr)[0])
                xmldict['c2sv']= round(float(re.findall(r'Upper Right\s+\( .\d+.\d+,\s+(.\d+.\d+)\)', tempstr)[0]),1)

                xmldict['numband']= re.findall(r'Band (\d+) \w', tempstr)[0]
                xmldict['ref']= re.findall(r'GEOGCS\["(.+)",', tempstr)[0].replace(' ','')
                xmldict['length']= xmldict['c2size']
                xmldict['width']= xmldict['c1size']
                xmldict['xmax']= xmldict['c1ev']
                xmldict['xmin']= xmldict['c1sv']

                #xml file name
                xmldict['filename'] = 'Unknown'
                xmldict['extrafilename'] = 'Unknown'
            os.remove(tempfile)
            
            with(open(outfile,'w')) as out:
                out.write(xmltext.format(**xmldict))
               
    print('you have exited tiff to xml')


def call_ssara_dem(custom_template, inps):
    print('You have started ssara!')
    
    slc_dir = make_slc_dir()
    parent_dir = os.getenv('PARENTDIR')    
    out_file = 'ssara_output_1.log'
    ssara_command = 'ssara_federated_query.py {ssaraopt} --dem --asfResponseTimeout=360 --parallel=20 --download >& {outfile}'.format(ssaraopt=custom_template['ssaraopt'],outfile=out_file)
    command = 'ssh pegasus.ccs.miami.edu "s.cgood; cd {slcdir};  {parentdir}/3rdparty/SSARA/{ssaracommand}"'.format(slcdir=slc_dir,parentdir=parent_dir,ssaracommand=ssara_command)

    print('command currently executing: ' + command)
    status = subprocess.Popen(command, shell=True).wait()
    print('Files Downloaded')
    tiff_to_xml()

    return


def main(argv):

    messageRsmas.log(' '.join(argv))
    inps = dem_parser()
    custom_template = readfile.read_template(inps.custom_template_file)
    cwd = make_dem_dir()

    # can sentinelStack.demMethod be removed? I think parser is the replacement
    if 'sentinelStack.demMethod' not in custom_template.keys():
       custom_template['sentinelStack.demMethod']='bbox'

    if custom_template['sentinelStack.demMethod']=='bbox':
       bbox=custom_template['sentinelStack.boundingBox']
       south=bbox.split(' ')[0].split('\'')[1]   # assumes quotes '-1 0.15 -91.3 -91.0'
       north=bbox.split(' ')[1]
       west =bbox.split(' ')[2]
       east =bbox.split(' ')[3].split('\'')[0]
    elif custom_template['sentinelStack.demMethod']=='ssara':
       call_ssara_dem(custom_template, inps)
       cmd = 'ssara_federated_query.py '+custom_template['ssaraopt']+' --dem'
       output = subprocess.check_output(cmd, shell=True)
       output=output.split("\n")
       for line in output:
         if line.startswith("wget"):
           coordList = line.split("?")[1].split("&")[0:4]
           for item in coordList:
              if "north" in item:
                 north=item.split("=")[1]
              if "south" in item:
                 south=item.split("=")[1]
              if "east" in item:
                 east=item.split("=")[1]
              if "west" in item:
                 west=item.split("=")[1]
    else:
       sys.ext('Error unspported demMethod option: '+custom_template['sentinelStack.demMethod'])
 
    if inps.ssara:
        call_ssara_dem(custom_template, inps)
        print('####### CONTINUED')
    else: 
        print('not ssara')
    south=round(float(south)-0.5)
    north=round(float(north)+0.5)
    west =round(float(west)-0.5)
    east =round(float(east)+0.5)
  
    demBbox=str(int(south))+' '+str(int(north))+' '+str(int(west))+' '+str(int(east))
    cmd ='dem.py -a stitch -b '+demBbox+' -c -u https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/'
    messageRsmas.log(cmd)

    try:
       output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as exc:
       print("Command failed. Exit code, StdErr:", exc.returncode,exc.output)
       sys.exit('Error produced by dem.py')
    else:
       #print("Success.        StdOut \n{}\n".format(output))
       if 'Could not create a stitched DEM. Some tiles are missing' in output:
          os.chdir('..')
          shutil.rmtree('DEM')
          sys.exit('Error in dem.py: Tiles are missing. Ocean???')

    xmlFile = glob.glob('demLat_*.wgs84.xml')[0]
    fin = open(xmlFile,'r')
    fout = open("tmp.txt", "wt")
    for line in fin:
        fout.write( line.replace('demLat', cwd+'/demLat') )
    fin.close()
    fout.close()
    os.rename('tmp.txt',xmlFile)

    print '\n###############################################'
    print 'End of dem_rsmas.py'
    print '################################################\n'

###########################################################################################
if __name__ == '__main__':
    main(sys.argv[:])

