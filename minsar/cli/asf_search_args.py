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
        asf_search_args.py --product=SLC --start-date=20030101 --end-date=20080101 --path=170 --download=$SCRATCHDIR/asf_product
        asf_search_args.py --product=CSLC --start-date=20030101 --end-date=20080101 --path=170 --download=$SCRATCHDIR/asf_product
        asf_search_args.py --product=SLC --start-date=20030101 --end-date=20080101 --polygon="POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))" --download=$SCRATCHDIR/asf_product
        asf_search_args.py --product=CSLC --start-date=20030101 --end-date=20080101 --polygon="POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))" --download=$SCRATCHDIR/asf_product

    To use parallel downloads:
        asf_search_args.py --product=SLC --start-date=20030101 --end-date=20080101 --path=170 --download=$SCRATCHDIR/asf_product --parallel=4

    To search for a specific date range:
        asf_search_args.py --product=SLC --start-date=20030101 --end-date=20080101 --download=$SCRATCHDIR/asf_product

    To search for a specific polygon area:
        asf_search_args.py --product=SLC --start-date=20030101 --end-date=20080101 --polygon="POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))" --download=$SCRATCHDIR/asf_product
"""

# Create an ArgumentParser object
parser = argparse.ArgumentParser(description=EXAMPLE,
                formatter_class=argparse.RawTextHelpFormatter,
                epilog=epi)

# Define your optional arguments
parser.add_argument('--polygon', metavar='POLYGON', help='Poligon of the wanted area to intersect with the search')
parser.add_argument('--start-date', metavar='DATE', help='Start date of the search')
parser.add_argument('--end-date', metavar='DATE', help='End date of the search')
parser.add_argument('--path', metavar='ORBIT', help='Relative Orbit Path')
parser.add_argument('--download', metavar='FOLDER', nargs='?', const='', default=None, help='Specify path to download the data, if not specified, the data will be downloaded either in SCRATCHDIR or HOME directory')
parser.add_argument('--product', metavar='FILE', help='Choose the product type to download')
parser.add_argument('--parallel', nargs=1, help='Download the data in parallel, specify the number of processes to use')

inps = parser.parse_args()

sdate = None
edate = None
polygon = None
orbit = None
path = None
product = []

if 'SLC' in inps.product:
    product.append(asf.PRODUCT_TYPE.SLC)

if 'BURST' in inps.product:
    product.append(asf.PRODUCT_TYPE.BURST)

if 'CSLC' in inps.product or inps.product is None: 
    product.append(asf.PRODUCT_TYPE.CSLC)

if inps.start_date:
    sdate = datetime.datetime.strptime(inps.start_date, '%Y%m%d').date()

if inps.end_date:
    edate = datetime.datetime.strptime(inps.end_date, '%Y%m%d').date()

if inps.polygon :
    polygon = inps.polygon

if inps.path:
    orbit = inps.path

if inps.download:
    path = inps.download

if inps.parallel:
    par = int(inps.parallel[0])
else:
    par = 1

print("Searching for Sentinel-1 data...")
results = asf.search(
    platform=asf.PLATFORM.SENTINEL1,
    processingLevel=product,
    start=sdate,
    end=edate,
    intersectsWith=polygon,
    relativeOrbit=orbit
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

if path != '' and path is not None:
    results.download(
         path = path,
         session = asf.ASFSession(),
         processes = par
    )