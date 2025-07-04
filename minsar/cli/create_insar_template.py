import os
import re
import sys
import math
import argparse
import datetime
import requests
from datetime import datetime as dt
from datetime import timedelta as td
from urllib.parse import urlparse, parse_qs
import pandas as pd

scratch = os.getenv('SCRATCHDIR')


EXAMPLE = f"""
DEFAULT FULLPATH FOR EXCEL IS ${os.getenv('SCRATCHDIR')}

create_insar_template.py --excel Central_America.xlsx --save
create_insar_template.py --swath '1 2' --url https://search.asf.alaska.edu/#/?zoom=9.065&center=130.657,31.033&polygon=POLYGON((130.5892%2031.2764,131.0501%2031.2764,131.0501%2031.5882,130.5892%2031.5882,130.5892%2031.2764))&productTypes=SLC&flightDirs=Ascending&resultsLoaded=true&granule=S1B_IW_SLC__1SDV_20190627T092113_20190627T092140_016880_01FC2F_0C69-SLC
create_insar_template.py  --polygon 'POLYGON((130.5892 31.2764,131.0501 31.2764,131.0501 31.5882,130.5892 31.5882,130.5892 31.2764))' --path 54 --swath '1 2' --satellite 'Sen' --start-date '20160601' --end-date '20230926'
"""
SCRATCHDIR = os.getenv('SCRATCHDIR')


def create_parser():
    synopsis = 'Create Template for insar processing'
    epilog = EXAMPLE
    parser = argparse.ArgumentParser(description=synopsis, epilog=epilog, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--excel', type=str, help="Path to the Excel file with volcano data.")
    parser.add_argument('--url', type=str, help="URL to the ASF data.")
    parser.add_argument('--polygon', type=str, help="Polygon coordinates in WKT format.")
    parser.add_argument('--path', type=int, help="Path number.")
    parser.add_argument('--direction', type=str, choices=['A', 'D'], default='A', help="Flight direction (default: %(default)s).")
    parser.add_argument('--swath', type=str, default='1 2 3', help="Swath numbers as a string (default: %(default)s).")
    parser.add_argument('--troposphere', type=str, default='auto', help="Tropospheric correction mode.")
    parser.add_argument('--thresh', type=float, default=0.7, help="Threshold value for temporal coherence.")
    parser.add_argument('--lat-step', type=float, default=0.0002, help="Latitude step size (default: %(default)s).")
    parser.add_argument('--satellite', type=str, choices=['Sen'], default='Sen', help="Specify satellite (default: %(default)s).")
    parser.add_argument('--save-name', type=str, default=None, help=f"Save the template with specified Volcano name ({os.getenv('TEMPLATES')}/Volcano.template).")
    parser.add_argument('--save', action="store_true")
    parser.add_argument('--start-date', nargs='*', metavar='YYYYMMDD', type=str, help='Start date of the search')
    parser.add_argument('--end-date', nargs='*', metavar='YYYYMMDD', type=str, help='End date of the search')
    parser.add_argument('--period', nargs='*', metavar='YYYYMMDD:YYYYMMDD, YYYYMMDD,YYYYMMDD', type=str, help='Period of the search')
    parser.add_argument("--jeststream", action="store_true", help="Upload on jetstream")
    parser.add_argument("--insarmaps", action="store_true", help="Upload on insarmaps")

    inps = parser.parse_args()

    if inps.period:
        for p in inps.period:
            delimiters = '[,:\-\s]'
            dates = re.split(delimiters, p)

            if len(dates[0]) and len(dates[1]) != 8:
                msg = 'Date format not valid, it must be in the format YYYYMMDD'
                raise ValueError(msg)

            inps.start_date.append(dates[0])
            inps.end_date.append(dates[1])
    else:
        if not inps.start_date:
            inps.start_date = "20160601"
        if not inps.end_date:
            inps.end_date = datetime.datetime.now().strftime("%Y%m%d")

    return inps


def miaplpy_check_longitude(lon1, lon2):
    """
    Adjusts longitude values based on the Miaplpy criteria.
    """
    if abs(lon1 - lon2) > 0.2:
        val = (abs(lon1 - lon2) - 0.2) / 2
        miaLon1 = round(lon1 - val, 2) if lon1 > 0 else round(lon1 + val, 2)
        miaLon2 = round(lon2 + val, 2) if lon2 > 0 else round(lon2 - val, 2)
    else:
        miaLon1 = lon1
        miaLon2 = lon2
    return miaLon1, miaLon2


def topstack_check_longitude(lon1, lon2):
    """
    Adjusts longitude values based on the TopStack criteria.
    """
    if abs(lon1 - lon2) < 5:
        val = (5 - abs(lon1 - lon2)) / 2
        topLon1 = round(lon1 + val, 2) if lon1 > 0 else round(lon1 - val, 2)
        topLon2 = round(lon2 - val, 2) if lon2 > 0 else round(lon2 + val, 2)
    else:
        topLon1 = min(lon1, lon2)
        topLon2 = max(lon1, lon2)
    return topLon1, topLon2


def main(file_name):
    path = os.path.join(scratch, file_name)

    if not os.path.exists(path):
        raise FileNotFoundError(f"File {file_name} does not exist in {scratch}")

    df = pd.read_excel(path)

    return df


if __name__ == '__main__':
    main()


def create_insar_template(inps, path, swath, troposphere, lat_step, start_date, end_date, satellite, lat1, lat2, lon1, lon2, miaLon1, miaLon2, topLon1, topLon2):
    """
    Creates an InSAR template configuration.

    Args:
        inps: Input parameters object containing various attributes.
        satellite: Satellite name or identifier.
        lat1, lat2: Latitude range.
        lon1, lon2: Longitude range.
        miaLon1, miaLon2: Miaplpy longitude range.
        topLon1, topLon2: Topstack longitude range.

    Returns:
        The generated template configuration.
    """
    lon_step = round(lat_step / math.cos(math.radians(float(lat1))), 5)

    print(f"Latitude range: {lat1}, {lat2}\n")
    print(f"Longitude range: {lon1}, {lon2}\n")
    print(f"Miaplpy longitude range: {miaLon1}, {miaLon2}\n")
    print(f"Topstack longitude range: {topLon1}, {topLon2}\n")

    template = generate_config(
        path=path,
        satellite=satellite,
        lat1=lat1,
        lat2=lat2,
        lon1=lon1,
        lon2=lon2,
        topLon1=topLon1,
        topLon2=topLon2,
        swath=swath,
        tropo=troposphere,
        miaLon1=miaLon1,
        miaLon2=miaLon2,
        lat_step=lat_step,
        lon_step=lon_step,
        start_date=start_date,
        end_date= end_date,
        thresh=inps.thresh,
        jetstream=inps.jeststream,
        insarmaps=inps.insarmaps
    )

    return template


def extract_coordinates(polygon_str):
    # Remove "POLYGON((" and "))" to isolate the coordinates
    coordinates = polygon_str.replace("POLYGON((", "").replace("))", "")

    # Split the coordinates into a list of (lon, lat) pairs
    points = [tuple(map(float, coord.split())) for coord in coordinates.split(",")]

    # Extract all longitudes and latitudes
    longitudes = [point[0] for point in points]
    latitudes = [point[1] for point in points]

    # Compute the bounding box
    min_lon = min(longitudes)
    max_lon = max(longitudes)
    min_lat = min(latitudes)
    max_lat = max(latitudes)

    return min_lon, max_lon, min_lat, max_lat


def asf_extractor(url):
    # Parse the URL
    parsed_url = urlparse(url)

    # Extract the fragment (part after #)
    fragment = parsed_url.fragment

    # Parse the query parameters from the fragment
    query_params = parse_qs(fragment.split('?')[1])

    min_lon, max_lon, min_lat, max_lat = extract_coordinates(query_params['polygon'][0])

    satellite = 'SENTINEL-1' if 'S1' in query_params['granule'][0] else None

    # Format the result
    bounding_box = f"{min_lon},{min_lat},{max_lon},{max_lat}"

    api = f"https://api-prod-private.asf.alaska.edu/services/search/param?bbox={bounding_box}&dataset={satellite}&processinglevel={query_params['productTypes'][0]}&flightDirection={query_params['flightDirs'][0]}&maxResults=250&output=jsonlite2"

    request = requests.get(api)
    if request.status_code == 200:
        print("Request was successful\n")
        data = request.json()

    for result in data.get("results", []):
        if result["gn"] not in query_params['granule'][0]:
            continue

        print(result['gn'])
        result_min_lon, result_max_lon, result_min_lat, result_max_lat = extract_coordinates(result["w"])

        # Check if the result polygon's bounding box contains the input polygon's bounding box
        if not (result_min_lon <= min_lon and result_max_lon >= max_lon and
            result_min_lat <= min_lat and result_max_lat >= max_lat):
            msg = f"Result {result['gn']} does not contain the input polygon"
            continue

        path = result["p"]
        msg = None

    if msg:
        raise ValueError(msg)

    return str(path), satellite, query_params['flightDirs'][0][0], min_lat, max_lat, min_lon, max_lon


def parse_polygon(polygon):
        polygon = polygon.replace("POLYGON((", "").replace("))", "")

        latitude = []
        longitude = []

        for word in polygon.split(','):
            if (float(word.split(' ')[1])) not in latitude:
                latitude.append(float(word.split(' ')[1]))
            if (float(word.split(' ')[0])) not in longitude:
                longitude.append(float(word.split(' ')[0]))

        lon1, lon2 = round(min(longitude),2), round(max(longitude),2)
        lat1, lat2 = round(min(latitude),2), round(max(latitude),2)

        return lat1, lat2, lon1, lon2


def get_satellite_name(satellite):
    if satellite == 'Sen':
        return 'SENTINEL-1A,SENTINEL-1B'
    elif satellite == 'Radarsat':
        return 'RADARSAT2'
    elif satellite == 'TerraSAR':
        return 'TerraSAR-X'
    else:
        raise ValueError("Invalid satellite name. Choose from ['Sen', 'Radarsat', 'TerraSAR']")


def generate_config(path, satellite, lat1, lat2, lon1, lon2, topLon1, topLon2, swath, tropo, miaLon1, miaLon2, lat_step, lon_step, start_date, end_date, thresh, jetstream, insarmaps):
    config = f"""\
######################################################
cleanopt                          = 0   # [ 0 / 1 / 2 / 3 / 4]   0,1: none 2: keep merged,geom_master,SLC 3: keep MINTPY 4: everything
processor                         = isce
ssaraopt.platform                 = {satellite}  # [Sentinel-1 / ALOS2 / RADARSAT2 / TerraSAR-X / COSMO-Skymed]
ssaraopt.relativeOrbit            = {path}
ssaraopt.startDate                = {start_date}  # YYYYMMDD
ssaraopt.endDate                  = {end_date}    # YYYYMMDD
hazard_products_flag              = False
#insarmaps_flag                     = True
######################################################
#topsStack.boundingBox             = {lat1} {lat2} {topLon1} {topLon2}    # -1 0.15 -91.6 -90.9
#topsStack.excludeDates            =  20240926
topsStack.subswath                = {swath} # '1 2'
topsStack.numConnections          = 4    # comment
topsStack.azimuthLooks            = 3    # comment
topsStack.rangeLooks              = 15   # comment
topsStack.filtStrength            = 0.2  # comment
topsStack.unwMethod               = snaphu  # comment
topsStack.coregistration          = auto  # [NESD geometry], auto for NESD
#topsStack.referenceDate           = 20151220

######################################################
mintpy.load.autoPath              = yes
mintpy.subset.lalo                = {lat1}:{lat2},{lon1}:{lon2}
mintpy.compute.cluster            = local #[local / slurm / pbs / lsf / none], auto for none, cluster type
mintpy.compute.numWorker          = 30 #[int > 1 / all], auto for 4 (local) or 40 (non-local), num of workers
#mintpy.reference.lalo             = {lat1},{lon1}     # S of SN

mintpy.networkInversion.parallel  = yes  #[yes / no], auto for no, parallel processing using dask
mintpy.network.tempBaseMax        = auto  #[1-inf, no], auto for no, max temporal baseline in days
mintpy.network.perpBaseMax        = auto  #[1-inf, no], auto for no, max perpendicular spatial baseline in meter
mintpy.network.connNumMax         = auto  #[1-inf, no], auto for no, max number of neighbors for each acquisition
mintpy.network.coherenceBased     = auto  #[yes / no], auto for no, exclude interferograms with coherence < minCoherence
mintpy.network.aoiLALO            = auto  #[S:N,W:E / no], auto for no - use the whole area
mintpy.networkInversion.minTempCoh  = 0.6 #[0.0-1.0], auto for 0.7, min temporal coherence for mask

mintpy.troposphericDelay.method   = {tropo}   # pyaps  #[pyaps / height_correlation / base_trop_cor / no], auto for pyaps
mintpy.save.hdfEos5               = yes   #[yes / update / no], auto for no, save timeseries to UNAVCO InSAR Archive format
mintpy.save.hdfEos5.update        = yes   #[yes / no], auto for no, put XXXXXXXX as endDate in output filename
mintpy.save.hdfEos5.subset        = yes   #[yes / no], auto for no, put subset range info in output filename
mintpy.save.kmz                   = yes   #[yes / no], auto for yes, save geocoded velocity to Google Earth KMZ file
####################
minsar.miaplpyDir.addition         = date  #[name / lalo / no] auto for no (miaply_$name_startDate_endDate))
miaplpy.subset.lalo                = {lat1}:{lat2},{miaLon1}:{miaLon2}  #[S:N,W:E / no], auto for no
miaplpy.load.startDate             = auto # 20200101
miaplpy.load.endDate               = auto
mintpy.geocode.laloStep            = {lat_step},{lon_step}
mintpy.reference.minCoherence      = 0.5      #[0.0-1.0], auto for 0.85, minimum coherence for auto method
miaplpy.interferograms.delaunayBaselineRatio = 4
miaplpy.interferograms.delaunayTempThresh    = 120     # [days] temporal threshold for delaunay triangles, auto for 120
miaplpy.interferograms.delaunayPerpThresh    = 200     # [meters] Perp baseline threshold for delaunay triangles, auto for 200
miaplpy.interferograms.networkType           = single_reference # network
miaplpy.interferograms.networkType           = delaunay # network
#############################################
miaplpy.load.processor            = isce
miaplpy.multiprocessing.numProcessor = 40
miaplpy.inversion.rangeWindow     = 24   # range window size for searching SHPs, auto for 15
miaplpy.inversion.azimuthWindow   = 7    # azimuth window size for searching SHPs, auto for 15
miaplpy.timeseries.tempCohType    = full     # [full, average], auto for full.
miaplpy.timeseries.minTempCoh     = 0.50     # auto for 0.5
mintpy.networkInversion.minTempCoh = {thresh}
#############################################
minsar.upload_flag                = {jetstream}    # [True / False ], upload to jetstream (Default: False)
minsar.insarmaps_flag             = {insarmaps}
minsar.insarmaps_dataset          = filt*DS
#############################################
"""
    return config


def main(iargs=None):
    inps = create_parser() if not isinstance(iargs, argparse.Namespace) else iargs
    data_collection = []

    if inps.excel:
        from src.maketemplate.read_excel import main
        df = main(inps.excel)

        for index, row in df.iterrows():
            lat1, lat2, lon1, lon2 = parse_polygon(row.polygon)

            # Perform checks
            miaLon1, miaLon2 = miaplpy_check_longitude(lon1, lon2)
            topLon1, topLon2 = topstack_check_longitude(lon1, lon2)
            yesterday = dt.now() - td(days=1)

            satellite = get_satellite_name(row.get('satellite'))

            # Create processed values dictionary
            processed_values = {
                'latitude1': lat1,
                'latitude2': lat2,
                'longitude1': lon1,
                'longitude2': lon2,
                'miaplpy.longitude1': miaLon1,
                'miaplpy.longitude2': miaLon2,
                'topsStack.longitude1': topLon1,
                'topsStack.longitude2': topLon2,
                'path': row.get('ssaraopt.relativeOrbit', ''),
                'start_date': row.get('ssaraopt.startDate', ''),
                'end_date': yesterday.strftime('%Y%m%d') if 'auto' in row.get('ssaraopt.endDate', '') else row.get('ssaraopt.endDate', ''),
                'troposphere': row.get('mintpy.troposphericDelay', 'auto'),
                'swath': row.get('topsStack.subswath', ''),
                'satellite': satellite

            }

            # Update row dictionary and append to collection
            row_dict = row.to_dict()
            row_dict.update(processed_values)
            data_collection.append(row_dict)
    else:
        # Handle URL or polygon input
        if inps.url:
            path, satellite, direction, lat1, lat2, lon1, lon2 = asf_extractor.main(inps.url)
        else:
            lat1, lat2, lon1, lon2 = parse_polygon(inps.polygon)
            satellite = get_satellite_name(inps.satellite)
            direction = inps.direction
            path = inps.path

        # Perform checks
        miaLon1, miaLon2 = miaplpy_check_longitude(lon1, lon2)
        topLon1, topLon2 = topstack_check_longitude(lon1, lon2)

        # Create processed values dictionary
        processed_values = {
            'name': inps.name if hasattr(inps, 'name') else 'Unknown',
            'direction': direction,
            'ssaraopt.startDate': inps.startDate if hasattr(inps, 'startDate') else 'auto',
            'ssaraopt.endDate': inps.endDate if hasattr(inps, 'endDate') else 'auto',
            'ssaraopt.relativeOrbit': inps.relativeOrbit if hasattr(inps, 'relativeOrbit') else None,
            'topsStack.subswath': inps.swath if hasattr(inps, 'swath') else None,
            'mintpy.troposphericDelay': inps.troposphericDelay if hasattr(inps, 'troposphericDelay') else 'auto',
            'polygon': inps.polygon if hasattr(inps, 'polygon') else None,
            'satellite': satellite,
            'latitude1': lat1,
            'latitude2': lat2,
            'longitude1': lon1,
            'longitude2': lon2,
            'miaplpy.longitude1': miaLon1,
            'miaplpy.longitude2': miaLon2,
            'topsStack.longitude1': topLon1,
            'topsStack.longitude2': topLon2,
            'path': path
        }

        # Append processed values to collection
        data_collection.append(processed_values)

    for data in data_collection:
        template = create_insar_template(
            inps=inps,
            path = data.get('path',''),
            swath = data.get('swath', ''),
            troposphere = data.get('troposphere', 'auto'),
            lat_step = inps.lat_step,
            start_date = data.get('start_date', ''),
            end_date = data.get('end_date', ''),
            satellite=data.get('satellite'),
            lat1=data.get('latitude1'),
            lat2=data.get('latitude2'),
            lon1=data.get('longitude1'),
            lon2=data.get('longitude2'),
            miaLon1=data.get('miaplpy.longitude1'),
            miaLon2=data.get('miaplpy.longitude2'),
            topLon1=data.get('topsStack.longitude1'),
            topLon2=data.get('topsStack.longitude2')
        )

        if inps.save_name or inps.save:
            name = inps.save_name if inps.save_name else data.get('name', '')
            sat = "Sen" if "SEN" in data.get('satellite', '').upper()[:4] else ""
            template_name = os.path.join(
                os.getenv('TEMPLATES'),
                f"{name}{sat}{data.get('direction')}{data.get('path')}.template"
            )
            with open(template_name, 'w') as f:
                f.write(template)
                print(f"Template saved in {template_name}")

if __name__ == '__main__':
    main(iargs=sys.argv)
