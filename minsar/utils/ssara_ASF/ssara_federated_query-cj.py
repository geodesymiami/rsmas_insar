#!/usr/bin/env python
###############################################################################
# ssara_federated_query.py
#
#  Project:  Seamless SAR Archive
#  Purpose:  Command line federated query client
#  Author:   Scott Baker
#  Created:  June 2013
#
###############################################################################
#  Copyright (c) 2013, Scott Baker 
# 
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation
#  the rights to use, copy, modify, merge, publish, distribute, sublicense,
#  and/or sell copies of the Software, and to permit persons to whom the
#  Software is furnished to do so, subject to the following conditions:
# 
#  The above copyright notice and this permission notice shall be included
#  in all copies or substantial portions of the Software.
# 
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#  OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#  THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.
###############################################################################
from __future__ import print_function
import os
import sys
import json
import datetime
import time
import csv
from xml.dom import minidom
import itertools
import operator
import re
import optparse
import threading
import subprocess as sub
import shutil
try:
    # For Python 3.0 and later
    from urllib.request import urlopen,HTTPCookieProcessor,HTTPPasswordMgrWithDefaultRealm,HTTPBasicAuthHandler,HTTPDigestAuthHandler,build_opener,install_opener
    from urllib.parse import urlencode
    from urllib.error import HTTPError
    from queue import Queue
    #import requests
except ImportError:
    # Fall back to Python2
    from urllib2 import urlopen,HTTPCookieProcessor,HTTPPasswordMgrWithDefaultRealm,HTTPBasicAuthHandler,HTTPDigestAuthHandler,build_opener,install_opener,HTTPError,HTTPRedirectHandler,HTTPSHandler
    from urllib import urlencode
    from Queue import Queue
    #import requests
import ssl

import password_config

#SAA - 2 July 18
# Updated to add required imports for CookieJar stuff
import base64
try:
   # Python 2.x Libs
   from urllib2 import build_opener, install_opener, Request, urlopen, HTTPError
   from urllib2 import URLError, HTTPSHandler,  HTTPHandler, HTTPCookieProcessor

   from cookielib import MozillaCookieJar
   from StringIO import StringIO

except ImportError as e:

   # Python 3.x Libs
   from urllib.request import build_opener, install_opener, Request, urlopen
   from urllib.request import HTTPHandler, HTTPSHandler, HTTPCookieProcessor
   from urllib.error import HTTPError, URLError

   from http.cookiejar import MozillaCookieJar
   from io import StringIO

# End of 2 July 18 add

class MyParser(optparse.OptionParser):
    def format_epilog(self, formatter):
        return self.epilog
    def format_description(self, formatter):
        return self.description
    
def main(argv):
    ### READ IN PARAMETERS FROM THE COMMAND LINE ###
    desc = """Command line client for searching with the SSARA Federated API, 
creating KMLs, and downloading data.  See the options and 
descriptions below for details and usage examples.

For questions or comments, contact Scott Baker: baker@unavco.org
    """
    epi = """
Usage Examples:
  These will do the search and create a KML:
    ssara_federated_query.py --platform=ENVISAT -r 170 -f 2925 --kml
    ssara_federated_query.py --platform=ENVISAT -r 170,392 -f 2925,657-693 -s 2003-01-01 -e 2008-01-01 --kml
    ssara_federated_query.py --platform=ENVISAT,ERS-1,ERS-2 -r 170 -f 2925 --collectionName="WInSAR ESA,EarthScope ESA" --kml
    ssara_federated_query.py --platform=ENVISAT --intersectsWith='POLYGON((-118.3 33.7, -118.3 33.8, -118.0 33.8, -118.0 33.7, -118.3 33.7))' --kml
    
  To download data, add the --download option and add your user credentials to the password_config.py file
    ssara_federated_query.py --platform=ENVISAT -r 170 -f 2925 --download 
    ssara_federated_query.py --platform=ENVISAT -r 170,392 -f 2925,657-693 -s 2003-01-01 -e 2008-01-01 --download 
    ssara_federated_query.py --platform=ENVISAT,ERS-1,ERS-2 -r 170 -f 2925 --collection="WInSAR ESA,EarthScope ESA" --download 

  UAVSAR flight line is mapped to relative orbit in the API. Also the default for the command line client is L0/L1.0 so you will
  need to use the "processingLevel" option, either set it to blank for everything or to something specific.  
    ssara_federated_query.py --platform=UAVSAR --relativeOrbit=05901 --processingLevel='' --intersectsWith='POINT(-155.3 19.4)'
    ssara_federated_query.py --platform=UAVSAR --relativeOrbit=05901 --processingLevel='INTERFEROMETRY' --intersectsWith='POINT(-155.3 19.4)'
"""
    parser = MyParser(description=desc, epilog=epi, version='1.0')
    querygroup = optparse.OptionGroup(parser, "Query Parameters", "These options are used for the API query.  "  
                                      "Use options to limit what is returned by the search. These options act as a way "
                                      "to filter the results and narrow down the search results.")
    
    querygroup.add_option('-p','--platform', action="store", dest="platform", metavar='<ARG>', default='', help='List of platforms (ie ALOS, ENVISAT, ERS-2...')
    querygroup.add_option('-a','--absoluteOrbit', action="store", dest="absoluteOrbit", metavar='<ARG>', default='',help='Absolute orbit (single orbit or list)')                      
    querygroup.add_option('-r', '--relativeOrbit', action="store", dest="relativeOrbit", metavar='<ARG>', default='',help='Relative Orbit (ie track or path)')  
    querygroup.add_option('-i','--intersectsWith', action="store", dest="intersectsWith", metavar='<ARG>', default='',help='WKT format POINT,LINE, or POLYGON')
    querygroup.add_option('-f', '--frame', action="store", dest="frame", metavar='<ARG>', default='',help='frame(s) (single frame or as a list or range)')  
    querygroup.add_option('-s', '--start', action="store", dest="start", metavar='<ARG>', default='',help='start date for acquisitions')
    querygroup.add_option('-e', '--end', action="store", dest="end", metavar='<ARG>', default='',help='end date for acquisitions')
    querygroup.add_option('--beamMode', action="store", dest="beamMode", metavar='<ARG>', default='',help='list of beam modes')  
    querygroup.add_option('--beamSwath', action="store", dest="beamSwath", metavar='<ARG>', default='',help='list of swaths: S1, S2, F1, F4...')
    querygroup.add_option('--flightDirection', action="store", dest="flightDirection", metavar='<ARG>', default='',help='Flight Direction (A or D, default is both)')
    querygroup.add_option('--lookDirection', action="store", dest="lookDirection", metavar='<ARG>', default='',help='Look Direction (L or R, default is both)')
    querygroup.add_option('--polarization', action="store", dest="polarization", metavar='<ARG>', default='',help='single or as a list')
    querygroup.add_option('--collectionName', action="store", dest="collectionName", metavar='<ARG>', default='',help='single collection or list of collections')  
    querygroup.add_option('--processingLevel', action="store", dest="processingLevel", default='L0,L1.0,SLC', help='Processing Level of data: L0, L1, L1.0, SLC... ' )
    querygroup.add_option('--maxResults', action="store", dest="maxResults", type="int", metavar='<ARG>', help='maximum number of results to return (from each archive)')
    querygroup.add_option('--minBaselinePerp', action="store", dest="minBaselinePerp", metavar='<ARG>', help='min perpendicular baseline of granule')
    querygroup.add_option('--maxBaselinePerp', action="store", dest="maxBaselinePerp", metavar='<ARG>', help='max perpendicular baseline of granule')
    querygroup.add_option('--minFaradayRotation', action="store", dest="minFaradayRotation", metavar='<ARG>', help='min faraday rotation of granule')
    querygroup.add_option('--maxFaradayRotation', action="store", dest="maxFaradayRotation", metavar='<ARG>', help='max faraday rotation of granule')
    querygroup.add_option('--minDoppler', action="store", dest="minDoppler", metavar='<ARG>', help='min doppler of granule')
    querygroup.add_option('--maxDoppler', action="store", dest="maxDoppler", metavar='<ARG>', help='max doppler of granule')
    querygroup.add_option('--minInsarStackSize', action="store", dest="minInsarStackSize", metavar='<ARG>', help='min stack size')
    querygroup.add_option('--maxInsarStackSize', action="store", dest="maxInsarStackSize", metavar='<ARG>', help='max stack size')
    parser.add_option_group(querygroup)

    resultsgroup = optparse.OptionGroup(parser, "Result Options", "These options handle the results returned by the API query")
    resultsgroup.add_option('--kml', action="store_true", default=False, help='create a KML of query') 
    resultsgroup.add_option('--kmlName', action="store", dest="kml_filename", type="str", metavar='<ARG>', help='Filename for KML output')
    resultsgroup.add_option('--csv', action="store_true", default=False, help='create a CSV of query')
    resultsgroup.add_option('--print', action="store_true", default=False, help='print results to screen')
    resultsgroup.add_option('--download', action="store_true", default=False, help='download the data')
    resultsgroup.add_option('--parallel', action="store", dest="parallel", type="int", default=1, metavar='<ARG>', help='number of scenes to download in parallel (default=%default)')
#    resultsgroup.add_option('--unavuser', action="store", dest="unavuser", type="str", metavar='<ARG>', help='UNAVCO SAR Archive username')
#    resultsgroup.add_option('--unavpass', action="store", dest="unavpass", type="str",metavar='<ARG>', help='UNAVCO SAR Archive password')
#    resultsgroup.add_option('--asfuser', action="store", dest="asfuser", type="str", metavar='<ARG>', help='ASF Archive username')
#    resultsgroup.add_option('--asfpass', action="store", dest="asfpass", type="str", metavar='<ARG>', help='ASF Archive password')
#    resultsgroup.add_option('--ssuser', action="store", dest="ssuser", type="str", metavar='<ARG>', help='Supersites username')
#    resultsgroup.add_option('--sspass', action="store", dest="sspass", type="str", metavar='<ARG>', help='Supersites password')
    resultsgroup.add_option('--monthMin', action="store", dest="monMin",type="int", default=1, metavar='<ARG>', help='minimum integer month')
    resultsgroup.add_option('--monthMax', action="store", dest="monMax",type="int", default=12, metavar='<ARG>', help='maximum integer month')
    resultsgroup.add_option('--noswath', action="store_true", default=False, help='Enforce first_frame==final_frame (i.e. not a swath)')
    resultsgroup.add_option('--dem', action="store_true", default=False, help='OT call for DEM')
    #resultsgroup.add_option('--asfResponseTimeout', action="store", dest="asfResponseTimeout", type="int", default=40, metavar='<ARG>', help='Set the timeout length for ASF API response (SSARA server defaults to 15 sec.)')
    resultsgroup.add_option('--asfResponseTimeout', action="store", dest="asfResponseTimeout", type="int", metavar='<ARG>', help='Set the timeout length for ASF API response (SSARA server defaults to 15 sec.)')
    resultsgroup.add_option('--s1orbits', action="store_true", default=False, help="Download S1 orbits from ESA for the result set")
    parser.add_option_group(resultsgroup) 
    opts, remainder = parser.parse_args(argv)
    opt_dict= vars(opts)

    ### BUILD DICTIONARY WITH QUERY FIELDS TO THE API ###
    query_dict = {}
    if opt_dict['platform']: query_dict['platform'] = opt_dict['platform']
    if opt_dict['absoluteOrbit']: query_dict['absoluteOrbit'] = opt_dict['absoluteOrbit']
    if opt_dict['relativeOrbit']: query_dict['relativeOrbit'] = opt_dict['relativeOrbit']
    if opt_dict['frame']: query_dict['frame'] = opt_dict['frame']
    if opt_dict['start']: query_dict['start'] = opt_dict['start']
    if opt_dict['end']: query_dict['end'] = opt_dict['end']
    if opt_dict['beamMode']: query_dict['beamMode'] = opt_dict['beamMode']
    if opt_dict['beamSwath']: query_dict['beamSwath'] = opt_dict['beamSwath']
    if opt_dict['flightDirection']: query_dict['flightDirection'] = opt_dict['flightDirection']
    if opt_dict['lookDirection']: query_dict['lookDirection'] = opt_dict['lookDirection']
    if opt_dict['polarization']: query_dict['polarization'] = opt_dict['polarization']
    if opt_dict['collectionName']: query_dict['collectionName'] = opt_dict['collectionName']
    if opt_dict['processingLevel']: query_dict['processingLevel'] = opt_dict['processingLevel']
    if opt_dict['maxResults']: query_dict['maxResults'] = opt_dict['maxResults']
    if opt_dict['intersectsWith']: query_dict['intersectsWith'] = opt_dict['intersectsWith']
    if opt_dict['minBaselinePerp']: query_dict['minBaselinePerp'] = opt_dict['minBaselinePerp']
    if opt_dict['maxBaselinePerp']: query_dict['maxBaselinePerp'] = opt_dict['maxBaselinePerp']
    if opt_dict['minDoppler']: query_dict['minDoppler'] = opt_dict['minDoppler']
    if opt_dict['maxDoppler']: query_dict['maxDoppler'] = opt_dict['maxDoppler']
    if opt_dict['minFaradayRotation']: query_dict['minFaradayRotation'] = opt_dict['minFaradayRotation']
    if opt_dict['maxFaradayRotation']: query_dict['maxFaradayRotation'] = opt_dict['maxFaradayRotation']
    if opt_dict['minInsarStackSize']: query_dict['minInsarStackSize'] = opt_dict['minInsarStackSize']
    if opt_dict['maxInsarStackSize']: query_dict['maxInsarStackSize'] = opt_dict['maxInsarStackSize']
    if opt_dict['asfResponseTimeout']: query_dict['asfResponseTimeout'] = opt_dict['asfResponseTimeout']


    ### QUERY THE APIs AND GET THE JSON RESULTS ###
    params = urlencode(query_dict)
    ssara_url = "https://web-services.unavco.org/brokered/ssara/api/sar/search?%s" % params
    print(ssara_url)
    print("Running SSARA API Query")
    t = time.time()
    f = urlopen(ssara_url)
    json_data = f.read().decode('utf8')
    data = json.loads(json_data)
    scenes = data['resultList']
    #print(scenes)
    print("SSARA API query: %f seconds" % (time.time()-t))
    if data['message']:
        print("###########################")
        for d in data['message']:
            print(d)
        print("###########################")

    ### ORDER THE SCENES BY STARTTIME, NEWEST FIRST ###
    scenes = sorted(scenes, key=operator.itemgetter('startTime'), reverse=True)
    print("Found %d scenes" % len(scenes))
    try:
        scenes = [r for r in sorted(scenes, key=operator.itemgetter('startTime')) 
                        if datetime.datetime.strptime(r['startTime'],"%Y-%m-%d %H:%M:%S").month >= opt_dict['monMin'] 
                        and datetime.datetime.strptime(r['startTime'],"%Y-%m-%d %H:%M:%S").month <= opt_dict['monMax'] ]
    except:
        scenes = [r for r in sorted(scenes, key=operator.itemgetter('startTime')) 
                        if datetime.datetime.strptime(r['startTime'],"%Y-%m-%dT%H:%M:%S.%f").month >= opt_dict['monMin'] 
                        and datetime.datetime.strptime(r['startTime'],"%Y-%m-%dT%H:%M:%S.%f").month <= opt_dict['monMax'] ]

    print("Scenes after filtering for monthMin %d and monthMax %d: %d" % (opt_dict['monMin'],opt_dict['monMax'],len(scenes)))
    if opt_dict['noswath']:
        scenes = [ r for r in sorted(scenes) if r['firstFrame']==r['finalFrame'] ]
        print("Scenes after filtering out swaths: %d" % len(scenes))

    if opt_dict['dem']:
        lats = []
        lons = []
        for scene in scenes:
            fp = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", scene['stringFootprint'])
            for t in map(lambda i: float(fp[i]), filter(lambda i: i % 2 == 1, range(len(fp)))):
                lats.append(t)
            for t in map(lambda i: float(fp[i]), filter(lambda i: i % 2 == 0, range(len(fp)))):
                lons.append(t)
        north = max(lats)+0.15
        south = min(lats)-0.15
        east = max(lons)+0.15
        west = min(lons)-0.15
        print('wget -O dem.tif "http://ot-data1.sdsc.edu:9090/otr/getdem?north=%f&south=%f&east=%f&west=%f&demtype=SRTMGL1"' % (north,south,east,west))
        print('gdal_translate -of GMT -projwin %f %f %f %f /vsicurl/https://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/SRTM_GL1_Ellip/SRTM_GL1_Ellip_srtm.vrt dem.grd' % (west,north,east,south))

    if not opt_dict['kml'] and not opt_dict['download'] and not opt_dict['print']:
        print("You did not specify the --kml, --print, or --download option, so there really is nothing else I can do for you now")
    if opt_dict['print']:
        for r in sorted(scenes, key=operator.itemgetter('startTime')):
            print(",".join(str(x) for x in [r['collectionName'], r['platform'], r['absoluteOrbit'], r['startTime'], r['stopTime'], r['relativeOrbit'], r['firstFrame'], r['finalFrame'], r['beamMode'], r['beamSwath'], r['flightDirection'], r['lookDirection'],r['polarization'], r['downloadUrl']]))
    ### MAKE THE CSV FILE ###
    if opt_dict['csv']:
        with open('ssara_federated_search_'+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+".csv",'w') as CSV:
            writer = csv.writer(CSV)
            writer.writerow(['Collection','Platform','absOrbit','relOrbit','First Frame','Final Frame','Start Time','Stop Time','Beam Mode','Swath','Flight Dir','Look Dir','Polarization','Process Level','URL','WKT'])
            for scene in sorted(scenes, key=operator.itemgetter('startTime')):
                writer.writerow([scene['collectionName'],scene['platform'],scene['absoluteOrbit'],scene['relativeOrbit'],
                                 scene['firstFrame'],scene['finalFrame'],scene['startTime'],scene['stopTime'],scene['beamMode'],
                                 scene['beamSwath'],scene['flightDirection'],scene['lookDirection'],scene['polarization'],
                                 scene['processingLevel'],scene['downloadUrl'],scene['stringFootprint']])
#                CSV.write(",".join(str(x) for x in [r['collectionName'], r['platform'], r['absoluteOrbit'], r['startTime'], r['stopTime'], r['relativeOrbit'], r['firstFrame'], r['finalFrame'], r['beamMode'], r['beamSwath'], r['flightDirection'], r['lookDirection'],r['polarization'], r['downloadUrl']])+"\n")
    ### GET A KML FILE, THE FEDERATED API HAS THIS OPTION ALREADY, SO MAKE THE SAME CALL AGAIN WITH output=kml OPTION ###
    if opt_dict['kml']:
        ssara_url = "https://web-services.unavco.org/brokered/ssara/api/sar/search?output=kml&%s" % params
        print("Getting KML")
        t = time.time()
        r = urlopen(ssara_url)
        localName = r.info()['Content-Disposition'].split('filename=')[1].replace('"','')
        if opt_dict['kml_filename']:
            localName = opt_dict['kml_filename']
        print("Saving KML: %s" % localName)
        f = open(localName, 'wb')
        f.write(r.read())
        f.close() 
    ### DOWNLOAD THE DATA FROM THE QUERY RESULTS ### 
    if opt_dict['download']:
        allGood = True
        for collection in list(set([d['collectionName'] for d in scenes])):
            if ('WInSAR' in collection or 'EarthScope' in collection) and not (password_config.unavuser and password_config.unavpass ):
                print("Can't download collection: %s" % collection)
                print("You need to specify your UNAVCO username and password in password_config.py")
                print("If you don't have a UNAVCO username/password, limit the query with the --collection option\n")
                allGood = False
            if 'Supersites VA4' in collection and not (password_config.eossouser and password_config.eossopass ):
                print("Can't download collection: %s" % collection)
                print("You need to specify your EO Single Sign On username and password in password_config.py")
                print("\n****************************************************************")
                print("For the Supersites VA4 data, you need an EO Single Sign On username/password:")
                print("Sign up for one here: https://eo-sso-idp.eo.esa.int/idp/AuthnEngine")
                print("****************************************************************\n")
                allGood = False
            if 'ASF' in collection and not (password_config.asfuser and password_config.asfpass ):
                print("Can't download collection: %s" % collection)
                print("You need to specify your ASF username and password in password_config.py")
                print("If you don't have a ASF username/password, limit the query with the --collection option\n")
                allGood = False
        if not allGood:
            print("Exiting now since some username/password are needed for data download to continue")
            exit()
        print("Downloading data now, %d at a time." % opt_dict['parallel'])
        #create a queue for parallel downloading
        queue = Queue()
        #spawn a pool of threads, and pass them queue instance 
        for i in range(opt_dict['parallel']):
            t = ThreadDownload(queue)
            t.setDaemon(True)
            t.start()
            #time.sleep(1)
        #populate queue with data   
        for d in sorted(scenes, key=operator.itemgetter('collectionName')):
            queue.put([d, opt_dict])
        #wait on the queue until everything has been processed     
        queue.join()
    ### Sentinel-1 Orbit Data Download ###
    if opt_dict['s1orbits']:
        print("Downloading S1 orbit data, %d at a time" % opt_dict['parallel'])
        #create a queue for parallel downloading
        queue = Queue()
        #spawn a pool of threads, and pass them queue instance
        for i in range(opt_dict['parallel']):
            t = s1OrbitDownload(queue)
            t.setDaemon(True)
            t.start()
        #populate queue with data
        for scene in scenes:
            queue.put([scene, opt_dict])
        #wait on the queue until everything has been processed
        queue.join()

class s1OrbitDownload(threading.Thread):
    """Threaded S1 orbit download"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            scene, opt_dict = self.queue.get()
            scene_center_time = datetime.datetime.strptime(scene['startTime'],"%Y-%m-%d %H:%M:%S")
            sat = os.path.basename(scene['downloadUrl']).split("_")[0]
            validity_start_time = scene_center_time-datetime.timedelta(days=1)
            orb_type = 'aux_poeorb'
            if (datetime.datetime.now()-scene_center_time).days < 21:
                orb_type = 'aux_resorb'
                validity_start_time = scene_center_time-datetime.timedelta(hours=10)
            ##### FIND THE CORRECT ORBIT FILE #####
            BASE_URL = 'https://qc.sentinel1.eo.esa.int/%s/?validity_start_time=%s' % (orb_type, validity_start_time.strftime("%Y-%m-%d"))
            #for i in re.findall('''href=["'](.[^"']+)["']''', urlopen(BASE_URL, context=ssl.SSLContext(ssl.PROTOCOL_TLSv1)).read().decode('utf-8'), re.I):
            for i in re.findall('''href=["'](.[^"']+)["']''', urlopen(BASE_URL).read().decode('utf-8'), re.I):
                if '.EOF' in i and sat in i:
                    orbit_file_url = "%s%s" % (BASE_URL.split("?")[0], i)
                    orbit_file = os.path.basename(orbit_file_url)
                    orb_file_dates = os.path.splitext(orbit_file)[0].split('_V')[1].split("_")
                    orb_start = datetime.datetime.strptime(orb_file_dates[0], "%Y%m%dT%H%M%S")
                    orb_stop = datetime.datetime.strptime(orb_file_dates[1], "%Y%m%dT%H%M%S")
                    if os.path.exists(orbit_file):
                        print("Already downloaded %s" % orbit_file_url)
                    elif not os.path.exists(orbit_file) and (orb_start < scene_center_time) and (orb_stop > scene_center_time):
                        cmd = "wget --no-check-certificate -c %s" % orbit_file_url
                        print(cmd)
                        pipe = sub.Popen(cmd, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT).stdout
                        pipe.read()
                    else:
                        print("No match %s" % orbit_file_url)
            self.queue.task_done()
    
# SAA - 2 July 18
# This is a big block of code designed to do all the cookie jar handling 
# that is required for urllib authentication.  This should be a much more 
# stable authentication method moving forward.

# Get and validate a cookie
def get_cookie(uname,pword,cookie_jar_path):
    print(cookie_jar_path)
    if os.path.isfile(cookie_jar_path):
       cookie_jar = MozillaCookieJar()
       cookie_jar.load(cookie_jar_path)
 
       ## make sure cookie is still valid
       print('*******************  FIRST COOKIE Check  ******************')
       if check_cookie(cookie_jar):
          print(" > Re-using previous cookie jar.")
          print('*******************  END FIRST COOKIE Check  ******************')
          return cookie_jar
       else:
          print(" > Could not validate old cookie Jar")
          cookie_jar = get_new_cookie(uname,pword,cookie_jar_path)
          check_cookie(cookie_jar)
    else:
        print('Could not find existing cookie jar -- Creating a new one')
        cookie_jar = get_new_cookie(uname,pword,cookie_jar_path)

    return cookie_jar
 
def get_new_cookie(new_username,new_password,cookie_jar_path):

   # Build URS4 Cookie request
   auth_cookie_url = asf_urs4['url'] + '?client_id=' + asf_urs4['client'] + '&redirect_uri=' + asf_urs4['redir'] + '&response_type=code&state='

   try:
      #python2
      user_pass = base64.b64encode (bytes(new_username+":"+new_password))
   except TypeError:
      #python3
      user_pass = base64.b64encode (bytes(new_username+":"+new_password, "utf-8"))
      user_pass = user_pass.decode("utf-8")

   # Authenticate against URS, grab all the cookies
   cookie_jar = MozillaCookieJar()
   opener = build_opener(HTTPCookieProcessor(cookie_jar), HTTPHandler(), HTTPSHandler())
   request = Request(auth_cookie_url, headers={"Authorization": "Basic {0}".format(user_pass)})

   # Watch out cookie rejection!
   try:
      response = opener.open(request)
   except HTTPError as e:
      if e.code == 401:
         print (" > Username and Password combo was not successful. Please try again.")
         return False
      else:
         # If an error happens here, the user most likely has not confirmed EULA.
         print ("\nIMPORTANT: There was an error obtaining a download cookie!")
         print ("Your user appears to lack permission to download data from the ASF Datapool.")
         print ("\n\nNew users: you must first log into Vertex and accept the EULA. In addition, your Study Area must be set at Earthdata https://urs.earthdata.nasa.gov")
         exit(-1)
   except URLError as e:
      print ("\nIMPORTANT: There was a problem communicating with URS, unable to obtain cookie. ")
      print ("Try cookie generation later.")
      exit(-1)

   # Did we get a cookie?
   if check_cookie_is_logged_in(cookie_jar):
      #COOKIE SUCCESS!
      print('Saving cookie jar file')
      cookie_jar.save(cookie_jar_path)
      return cookie_jar

   # if we aren't successful generating the cookie, nothing will work. Stop here!
   print ("WARNING: Could not generate new cookie! Cannot proceed. Please try Username and Password again.")
   print ("Response was {0}.".format(response.getcode()))
   print ("\n\nNew users: you must first log into Vertex and accept the EULA. In addition, your Study Area must be set at Earthdata https://urs.earthdata.nasa.gov")
   exit(-1)

# make sure we're logged into URS
def check_cookie_is_logged_in(cj):
   for cookie in cj:
      if cookie.name == 'urs_user_already_logged':
          # Only get this cookie if we logged in successfully!
          return True

   return False

def check_cookie(cookie_jar):

   if cookie_jar is None:
      print (" > Cookiejar is bunk: {0}".format(cookie_jar))
      return False

   # File we know is valid, used to validate cookie
   file_check = 'https://urs.earthdata.nasa.gov/profile'

   # Apply custom Redirect Hanlder
   opener = build_opener(HTTPCookieProcessor(cookie_jar), HTTPHandler(debuglevel=0), HTTPSHandler(debuglevel=0))
   install_opener(opener)

   # Attempt a HEAD request
   request = Request(file_check)
   request.get_method = lambda : 'HEAD'
   try:
      print (" > attempting to download {0}".format(file_check))
      response = urlopen(request)
      resp_code = response.getcode()
      # Make sure we're logged in
      if not check_cookie_is_logged_in(cookie_jar):
         return False

      # Save cookiejar
      cookie_jar.save(cookie_jar_path)

   except HTTPError:
      # If we ge this error, again, it likely means the user has not agreed to current EULA
      print ("\nIMPORTANT: ")
      print ("Your user appears to lack permissions to download data from the ASF Datapool.")
      print ("\n\nNew users: you must first log into Vertex and accept the EULA. In addition, your Study Area must be set at Earthdata https://urs.earthdata.nasa.gov")
      exit(-1)

   # This return codes indicate the USER has not been approved to download the data
   if resp_code in (300, 301, 302, 303):
      try:
         redir_url = response.info().getheader('Location')
      except AttributeError:
         redir_url = response.getheader('Location')

      print ("Redirect ({0}) occured, invalid cookie value!".format(resp_code))
      return False

   # These are successes!
   if resp_code in (200, 307):
      return True

   return False

# End of 2 July 18 add

def asf_dl(d, opt_dict):
    user_name = password_config.asfuser
    user_password = password_config.asfpass
    url = d['downloadUrl']
    filename = os.path.basename(url)
    print("ASF Download:",filename)
    start = time.time()

    # SAA - 2 July 2018
    # Redid the downloader to support new cookie jars

    global cookie_jar_path
    cookie_jar_path = os.path.join( os.getcwd(), ".bulk_download_cookiejar.txt")
    cookie_jar = MozillaCookieJar()

    global asf_urs4
    asf_urs4 = { 'url': 'https://urs.earthdata.nasa.gov/oauth/authorize',
            'client': 'BO_n7nTIlMljdvU6kRRB3g',
            'redir': 'https://auth.asf.alaska.edu/login'}

    # Make sure we can write it our current directory
    if os.access(os.getcwd(), os.W_OK) is False:
        print ("WARNING: Cannot write to current path! Check permissions for {0}".format(os.getcwd()))
        exit(-1)

    cj = get_cookie(user_name,user_password,cookie_jar_path)
    print('**********************  START 2nd COOKIE CHECK ******************')
    if check_cookie(cj):
        pass
    else:
        sys.exit('Did not pass check_cookie')

    print("ASF Download:",filename)
    start = time.time()
    try:
        request = Request(url)
        response = urlopen(request)
    except HTTPError as e:
        print(url)
        print(e)
        return
    dl_file_size = int(response.info()['Content-Length'])
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if dl_file_size == file_size:
            print("%s already downloaded" % filename)
            return
    start = time.time()
    CHUNK = 128*10240
    with open(filename, 'wb') as fp:
        while True:
            chunk = response.read(CHUNK)
            if not chunk: break
            fp.write(chunk)

    # Check to see if you got the file properly or not
    total_time = time.time() - start
    mb_sec = (os.path.getsize(filename) / (1024 * 1024.0)) / total_time
    print("%s download time: %.2f secs (%.2f MB/sec)" % (filename, total_time, mb_sec))
    fp.close()
        
def unavco_dl(d, opt_dict):
    user_name = password_config.unavuser
    user_password = password_config.unavpass
    url = d['downloadUrl']
    passman = HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, 'https://imaging.unavco.org/data/sar/lts', user_name, user_password)
    authhandler = HTTPDigestAuthHandler(passman)
    opener = build_opener(authhandler)    
    filename = os.path.basename(url)
    try:
        f = opener.open(url)
    except HTTPError as e:
        print(e)
        return
    dl_file_size = int(f.info()['Content-Length'])
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if dl_file_size == file_size:
            print("%s already downloaded" % filename)
            f.close()
            return
    start = time.time()
    CHUNK = 256 * 10240
    with open(filename, 'wb') as fp:
        while True:
            chunk = f.read(CHUNK)
            if not chunk: break
            fp.write(chunk)
    total_time = time.time() - start
    mb_sec = (os.path.getsize(filename) / (1024 * 1024.0)) / total_time
    print("%s download time: %.2f secs (%.2f MB/sec)" % (filename, total_time, mb_sec))
    f.close()
    
def va4_dl(d, opt_dict):
    user_name = password_config.eossouser
    user_password = password_config.eossopass
    url = d['downloadUrl']
    filename = os.path.basename(url)
    secp_path = os.path.dirname(sys.argv[0])+"/data_utils/secp"
    cmd = """%s -C %s:%s %s""" % (secp_path,user_name,user_password,d['downloadUrl'])
    print("Downloading:",url)
    start = time.time()
    pipe = sub.Popen(cmd, shell=True, stdout=sub.PIPE, stderr=sub.STDOUT).stdout
    pipe.read()
    total_time = time.time() - start
    mb_sec = (os.path.getsize(filename) / (1024 * 1024.0)) / total_time
    print("%s download time: %.2f secs (%.2f MB/sec)" % (filename, total_time, mb_sec))
    
class ThreadDownload(threading.Thread):
    """Threaded SAR data download"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            d, opt_dict = self.queue.get()
            if 'unavco' in d['downloadUrl']:
                unavco_dl(d, opt_dict)
            elif 'asf' in d['downloadUrl'] :
                asf_dl(d, opt_dict)
                url = d['downloadUrl']
                filename = os.path.basename(url)
                # SAA -- This is a quick check to see if the response from the server 
                # was bad.  If the file size is less than 1600 bytes it is just a server
                # response and the asf_dl function is called again to get the file.
                # should be made more robust to try a few times and then give up. 
                if os.path.getsize(filename) < 1600:
                    print('Retrying file: %s' % filename)
                    os.unlink(filename)
                    asf_dl(d,opt_dict)
            elif d['collectionName'] == 'Supersites VA4':
                va4_dl(d,opt_dict)
            self.queue.task_done()
             
if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.argv.append('-h')
    main(sys.argv[1:])
