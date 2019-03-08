#! /usr/bin/env python3
###############################################################################
# 
# Project: dem_ssara.py
# Author: Falk Amelung
# Created: 3/2018
# Last Updated: 10/2018
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

EXAMPLE='''example:
  dem_rsmas.py  $SAMPLES/GalapagosT128SenVVD.template

      uses sentinelStack.boundingBox to generate a dem in DEM folder as dem.py requires integer degrees

      options:
           sentinelStack.demMethod = ssara [default: bbox]

      subtracts/adds ` 0.5 degree and then rounds to full integer

      '-1 0.15 -91.3 -90.9' -- >'-2 1 -92 -90

     work for islands where zip files may be missing
'''

##########################################################################
def run_dem_rsmas(argv):

    messageRsmas.log(' '.join(argv))
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,\
                                     epilog=EXAMPLE)
    parser.add_argument('custom_template_file', nargs='?',\
                        help='custom template with option settings.\n')
    inps = parser.parse_args()

    custom_template = readfile.read_template(inps.custom_template_file)
 
    if os.path.isdir('DEM'):
       shutil.rmtree('DEM')
    os.mkdir('DEM')
    os.chdir('DEM')

    cwd = os.getcwd()

    if 'sentinelStack.demMethod' not in custom_template.keys():
       custom_template['sentinelStack.demMethod']='bbox'

    if custom_template['sentinelStack.demMethod']=='bbox' or custom_template['sentinelStack.demMethod']=='auto':
       bbox=custom_template['sentinelStack.boundingBox']
       south=bbox.split(' ')[0].split('\'')[1]   # assumes quotes '-1 0.15 -91.3 -91.0'
       north=bbox.split(' ')[1]
       west =bbox.split(' ')[2]
       east =bbox.split(' ')[3].split('\'')[0]
    elif custom_template['sentinelStack.demMethod']=='ssara':
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
       sys.exit('Error unspported demMethod option: '+custom_template['sentinelStack.demMethod'])
 
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
          #shutil.rmtree('DEM')
          sys.exit('Error in dem.py: Tiles are missing. Ocean???')

    xmlFile = glob.glob('demLat_*.wgs84.xml')[0]
    fin = open(xmlFile,'r')
    fout = open("tmp.txt", "wt")
    for line in fin:
        fout.write( line.replace('demLat', cwd+'/demLat') )
    fin.close()
    fout.close()
    os.rename('tmp.txt',xmlFile)

    print('\n###############################################')
    print('End of dem_rsmas.py')
    print('################################################\n')

###########################################################################################
if __name__ == '__main__':
    run_dem_rsmas(sys.argv[:])

