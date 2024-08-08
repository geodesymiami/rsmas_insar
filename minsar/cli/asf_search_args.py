#!/usr/bin/env python3

import asf_search as asf
import datetime
import argparse
import os

workDir = 'SCRATCHDIR'

# Define the description and epilog of the script
EXAMPLE = """Command line client for searching with the ASF Federated API, 
downloading data, and more.  See the options and 
descriptions below for details and usage examples.
"""

epi = """
Usage Examples:
    These will do the search and download data:
        asf_search_args.py --Product=SLC --start-date=2014-10-04 --end-date=2015-10-05 --intersectsWith='POLYGON((-77.9853 0.7881,-77.9185 0.7881,-77.9185 0.8507,-77.9853 0.8507,-77.9853 0.7881))' --relativeOrbit 142 --download
        asf_search_args.py --Product=SLC --start=2014-10-04 --end=2015-10-05 --platform SENTINEL1 --print --download
        asf_search_args.py --Product=CSLC --start=20141004 --end=20151005 --polygon='POLYGON((-77.9853 0.7881,-77.9185 0.7881,-77.9185 0.8507,-77.9853 0.8507,-77.9853 0.7881))' --download --dir=PATH
        asf_search_args.py --Product=CSLC --start=2014-10-04 --end=2015-10-05 --polygon='POLYGON((-77.9853 0.7881,-77.9185 0.7881,-77.9185 0.8507,-77.9853 0.8507,-77.9853 0.7881))' --download --dir=PATH

    To use parallel downloads:
        asf_search_args.py --Product=SLC --start=2014-10-04 --end=2015-10-05 --relativeOrbit=170 --download --dir=PATH --parallel=4

    To search for a specific date range:
        asf_search_args.py --Product=SLC --start=2014-10-04 --end=2015-10-05 --download --dir=PATH

    To search for a specific polygon area:
        asf_search_args.py --Product=SLC --polygon='POLYGON((-77.9853 0.7881,-77.9185 0.7881,-77.9185 0.8507,-77.9853 0.8507,-77.9853 0.7881))'
"""

parser = argparse.ArgumentParser(description=EXAMPLE,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog=epi)

parser.add_argument('--intersectsWith', metavar='POLYGON', help='Poligon of the wanted area of interest to intersect with the search')
parser.add_argument('--start', metavar='YYYY-MM-DD or YYYYMMDD', help='Start date of the search')
parser.add_argument('--end', metavar='YYYY-MM-DD or YYYYMMDD', help='End date of the search')
parser.add_argument('--start-date', metavar='YYYY-MM-DD or YYYYMMDD', help='Start date of the search')
parser.add_argument('--end-date', metavar='YYYY-MM-DD or YYYYMMDD', help='End date of the search')
parser.add_argument('--node', metavar='NODE', help='Flight direction of the satellite (ASCENDING or DESCENDING)')
parser.add_argument('--relativeOrbit', type=int, metavar='ORBIT', help='Relative Orbit Path')
parser.add_argument('--Product', metavar='FILE', dest='product', choices=['SLC', 'CSLC', 'BURST'], help='Choose the product type to download')
parser.add_argument('--platform', nargs='?',metavar='SENTINEL1, SENTINEL-1A, SENTINEL-1B', help='Choose the platform to search')
parser.add_argument('--burst-id', nargs='*', type=str, metavar='BURST', help='Burst ID')
parser.add_argument('--download', action='store_true', help='Download the data')
parser.add_argument('--parallel', type=int, default=1, nargs=1, help='Download the data in parallel, specify the number of processes to use')
parser.add_argument('--print', action='store_true', help='Print the search results')
parser.add_argument('--dir', metavar='FOLDER', help='Specify path to download the data, if not specified, the data will be downloaded either in SCRATCHDIR or HOME directory')

inps = parser.parse_args()

sdate = None
edate = None
node = None
orbit = None
burst_id = None
product = []

if 'SLC' in inps.product:
    product.append(asf.PRODUCT_TYPE.SLC)

if 'BURST' in inps.product:
    product.append(asf.PRODUCT_TYPE.BURST)

    if inps.burst_id:
        burst_id = inps.burst_id

if 'CSLC' in inps.product or inps.product is None: 
    product.append(asf.PRODUCT_TYPE.CSLC)

if inps.start or inps.start_date:
    try:
        sdate = datetime.datetime.strptime(inps.start if inps.start else inps.start_date, '%Y-%m-%d').date()
    except:
        sdate = datetime.datetime.strptime(inps.start if inps.start else inps.start_date, '%Y%m%d').date()

if inps.end or inps.end_date:
    try:
        edate = datetime.datetime.strptime(inps.end if inps.end else inps.end_date, '%Y-%m-%d').date()
    except:
        edate = datetime.datetime.strptime(inps.end if inps.end else inps.end_date, '%Y%m%d').date()

if inps.platform in ['SENTINEL1', 'SENTINEL-1', 'S1', 'S-1']:
    platform = asf.PLATFORM.SENTINEL1

elif inps.platform in ['SENTINEL-1A', 'SENTINEL1A', 'S-1A', 'S1A']:
    platform = asf.PLATFORM.SENTINEL1A

elif inps.platform in ['SENTINEL-1B', 'SENTINEL1B', 'S-1B', 'S1B']:
    platform = asf.PLATFORM.SENTINEL1B

else:
    platform = asf.PLATFORM.SENTINEL1

if inps.node:
    if inps.node in ['ASCENDING', 'ASC', 'A']:
        node = asf.FLIGHT_DIRECTION.ASCENDING

    elif inps.node in ['DESCENDING', 'DESC', 'D']:
        node = asf.FLIGHT_DIRECTION.DESCENDING

if inps.download is not None:
    
    if inps.dir:
        path = inps.dir

    else:
        path = os.getenv('SCRATCHDIR') if os.getenv('SCRATCHDIR') else os.getenv('HOME')

else:
    path = None


print("Searching for Sentinel-1 data...")
results = asf.search(
    platform=platform,
    processingLevel=product,
    start=sdate,
    end=edate,
    intersectsWith=inps.intersectsWith,
    flightDirection=node,
    relativeOrbit=inps.relativeOrbit,
    absoluteBurstID = burst_id
)

if workDir in os.environ:
    work_dir = os.getenv(workDir)

else:
    work_dir = os.getenv('HOME')

if path == '':
    path = work_dir

print(f"Found {len(results)} results.")
for r in results:
    print('--------------------------------------------------------------------------------------------------------------------------')
    print(f"Start date: {r.properties['startTime']}")
    print(f"End date: {(r.properties['stopTime'])}")
    print(f"{r.geometry['type']}: {r.geometry['coordinates']}")
    print(f"Path of satellite: {r.properties['pathNumber']}")
    print(f"Granule:  {r.properties['granuleType']}")
    if burst_id:
        print(f"Absolute Burst ID: {r.properties['burst']['absoluteBurstID']}")

    if inps.print:
        print('')
        print(r)

if inps.download == True:
    print(f"Downloading {len(results)} results")
    results.download(
         path = path,
         session = asf.ASFSession(),
         processes = inps.parallel
    )