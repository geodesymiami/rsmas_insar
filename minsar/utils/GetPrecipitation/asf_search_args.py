#!/usr/bin/env python3

import asf_search as asf
import datetime
import argparse
import os

EXAMPLE = """example:
  
asf_search_args.py --polygon "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
asf_search_args.py --start-date 2019-01-01 --end-date 2021-09-29

"""

workDir = 'SCRATCHDIR'

# Create an ArgumentParser object
parser = argparse.ArgumentParser()

# Define your optional arguments
parser.add_argument('--polygon', help='Poligon of the wanted area to intersect with the search')
parser.add_argument('--start-date', help='Start date of the search')
parser.add_argument('--end-date', help='End date of the search')
parser.add_argument('--path', help='Relative Orbit Path')
parser.add_argument('--download', nargs='?', const='', default=None, help='Specify path to download the data, if not specified, the data will be downloaded either in SCRATCHDIR or HOME directory')

args = parser.parse_args()

# (asf.constants.PRODUCT_TYPE)
print(asf.constants.PRODUCT_TYPE)
print(args.download)

sdate = None
edate = None
polygon = None
orbit = None
path = None

if args.start_date is not None:
    sdate = datetime.datetime.strptime(args.start_date, '%Y-%m-%d').date()

if args.end_date is not None:
    edate = datetime.datetime.strptime(args.end_date, '%Y-%m-%d').date()

if args.polygon is not None:
    polygon = args.polygon

if args.path is not None:
    orbit = args.path

if args.download is not None:
    path = args.download

results = asf.search(
    platform= asf.PLATFORM.SENTINEL1,
    processingLevel=[asf.PRODUCT_TYPE.CSLC],
    start = sdate,
    end = edate,
    intersectsWith = polygon,
    relativeOrbit = orbit
)

if workDir in os.environ:
    work_dir = os.getenv(workDir)

else:
    work_dir = os.getenv('HOME')

if path == '':
    path = work_dir

# print(results[0].properties['startTime'], (results[0].properties['stopTime']), results[0].geometry)
# print(results[-1].properties['startTime'], (results[-1].properties['stopTime']), results[-1].geometry)
for r in results:
    print(r.properties['startTime'], (r.properties['stopTime']), r.geometry)

if path != '' and path is not None:
    results.download(
         path = path,
         session = asf.ASFSession()
    )