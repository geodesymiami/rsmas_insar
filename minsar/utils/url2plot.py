#!/usr/bin/env python3
"""
URL2plot.py

Converts an insarmaps URL string into a viewPS.py command string.

Usage:
    URL2plot.py "<insarmaps URL>"

"""

import sys
import math
import os
import re
import subprocess  # Add this import statement
from urllib.parse import urlparse, parse_qs

def print_help():
    help_text = """
url2plot.py: Convert an insarmaps URL into a viewPS.py command.

Usage:
    url2plot.py "<insarmaps URL>"

The insarmaps URL should have the following format:
    https://insarmaps.miami.edu/start/<centerLat>/<centerLon>/<zoomFactor>?<query_parameters>

Examples:
    cd $SCRATCHDIR/unittestGalapagosSenD128/mintpy
    url2plot.py "https://insarmaps.miami.edu/start/-0.8286/-91.1462/14.1973?flyToDatasetCenter=false&startDataset=S1_IW1_128_0596_0597_20160605_XXXXXXXX_S00887_S00783_W091207_W091106&pointLat=-0.81794&pointLon=-91.13625&minScale=-60&maxScale=60&startDate=20160629&endDate=20160804"

    cd $SCRATCHDIR/unittestGalapagosSenD128/miaplpy_SN_201606_201608/network_single_reference
    url2plot.py "https://insarmaps.miami.edu/start/-0.8286/-91.1462/14.1973?flyToDatasetCenter=false&startDataset=S1_IW1_128_0596_0597_20160605_XXXXXXXX_S00860_S00810_W091190_W091130_SingDS&pointLat=-0.81794&pointLon=-91.13625&minScale=-60&maxScale=60&startDate=20160629&endDate=20160804"


The script computes a  subset using delta = 301.2 * exp(-0.7075 * zoomFactor)
and builds a commands to be run.

Current limitations:
    - viewPS.py reads ths S1*.he5 file but does not use it. It always uses velocity.h5 ?!?
    - "displacement" on URL is not used.
    - viewPS.py ignores --period option

Todo:
    - viewPS.py should use timeseries2velocity
    - needs option to fit time function or use difference between start-date and end-date
    - viewPS.py should call extract_hdf5eos5 and extract as needed
    - ideally tsview.py, view.py have options to use OSM satellite/street as background, and to plot radar-coded data in geo coordinates.
    - should be one command that creates the plot with an easy way to modify plot parameters.

"""
    print(help_text.strip())

def parse_insarmaps_url(url):
    # Parse URL and extract the path segments
    parsed = urlparse(url)
    path_parts = parsed.path.split('/')
    # Expecting a structure like: ['', 'start', centerLat, centerLon, zoomFactor]
    try:
        start_index = path_parts.index('start')
        center_lat = float(path_parts[start_index + 1])
        center_lon = float(path_parts[start_index + 2])
        zoom_factor = float(path_parts[start_index + 3])
    except (ValueError, IndexError):
        raise ValueError("URL path does not have the expected format '/start/<centerLat>/<centerLon>/<zoomFactor>'.")

    # Parse the query string
    qs = parse_qs(parsed.query)
    # Helper: extract first value or None if not present
    def get_val(key, default=None):
        return qs.get(key, [default])[0]

    file = get_val('startDataset')
    point_lat = get_val('pointLat')
    point_lon = get_val('pointLon')
    ref_lat = get_val('refPointLat')
    ref_lon = get_val('refPointLon')
    min_scale = get_val('minScale')
    max_scale = get_val('maxScale')
    start_date = get_val('startDate')
    end_date = get_val('endDate')
    pixel_size = get_val('pixelSize')
    # For colorscale, default to "velocity" if not given.
    unit = get_val('colorscale', 'velocity')

    # Convert numeric values if they exist, else leave as None.
    point_lat = float(point_lat) if point_lat is not None else None
    point_lon = float(point_lon) if point_lon is not None else None
    ref_lat = float(ref_lat) if ref_lat is not None else None
    ref_lon = float(ref_lon) if ref_lon is not None else None
    min_scale = float(min_scale) if min_scale is not None else None
    max_scale = float(max_scale) if max_scale is not None else None

    return {
        'center_lat': center_lat,
        'center_lon': center_lon,
        'zoom_factor': zoom_factor,
        'file': file,
        'point_lat': point_lat,
        'point_lon': point_lon,
        'ref_lat': ref_lat,
        'ref_lon': ref_lon,
        'min_scale': min_scale,
        'max_scale': max_scale,
        'start_date': start_date,
        'end_date': end_date,
        'pixel_size': pixel_size,
        'unit': unit
    }


def build_commands(params):
    """
    Given the parsed parameters, compute the subset extents and return
    the viewPS.py command string.
    """
    # Extract required parameters:
    center_lat = params['center_lat']
    center_lon = params['center_lon']
    zoom_factor = params['zoom_factor']
    file = params['file']
    unit = params['unit']
    start_date = params['start_date']
    end_date = params['end_date']
    ref_lat = params['ref_lat']
    ref_lon = params['ref_lon']
    min_scale = params['min_scale']
    max_scale = params['max_scale']

    if params['pixel_size'] is None:
        pixel_size = 1
    else:
        pixel_size = params['pixel_size']

    mod_pixel_size = round(float(pixel_size) * 5)

    # Compute delta using the given formula:
    delta = 301.2 * math.exp(-0.7075 * zoom_factor)
    # For longitude, we use the same delta.
    delta_lat = delta
    delta_lon = delta*1.5  # arbitrarily selected. Needs to be calculate based on latitude

    # Calculate subset boundaries:
    min_lat = center_lat - delta_lat
    max_lat = center_lat + delta_lat
    min_lon = center_lon - delta_lon
    max_lon = center_lon + delta_lon

    # Format numeric outputs to three decimals.
    fmt = "{:.3f}"
    subset_lat = f"{fmt.format(min_lat)}:{fmt.format(max_lat)}"
    subset_lon = f"{fmt.format(min_lon)}:{fmt.format(max_lon)}"

    #### Build the plot_data.py command string.
    plot_data_cmd_parts = []

    if start_date and end_date:
        plot_data_cmd_parts.extend(["--period", f"{start_date}:{end_date}"])

    plot_data_cmd_parts.extend([
        "--plot-type=timeseries",
        "--ref-lalo", f"{ref_lat:.5f}", f"{ref_lon:.5f}",
        "--resolution", "01s",
        "--isolines", "3",
        "--lalo", f"{params['point_lat']:.5f}", f"{params['point_lon']:.5f}"
    ])

    #### Build the timeseries2velocity.py command string.
    ts2velocity_cmd_parts = [ "timeseries2velocity.py", f"{file}.he5" if file else "None.he5"]
    if start_date and end_date:
        ts2velocity_cmd_parts.append(f"--start-date {start_date} --end-date {end_date}")

    #### Build the extract_hdfeos5 command string.
    extract_cmd_parts = [ "extract_hdfeos5.py", f"{file}.he5"]

    #### Build the viewPS.py and/or view.py command string
    ref_lalo, subset_lalo, point_size,  scale, sub_lat_lon, scatter_size = [], [], [], [], [], []
    if ref_lat is not None and ref_lon is not None:
        ref_lalo.append(f"--ref-lalo {fmt.format(ref_lat)} {fmt.format(ref_lon)}")
    subset_lalo.append(f"--subset-lalo={subset_lat},{subset_lon}")
    scatter_size.append(f"--style scatter --scatter-size {mod_pixel_size}")
    point_size.append(f"--point-size {mod_pixel_size}")  # 3/25: should use different point_size for view.py, viewPS.py (geo, radar-coded)
    if min_scale is not None and max_scale is not None:
        scale.append(f"--vlim {min_scale} {max_scale}")

    sub_lat_lon.append(f"--sub-lat {min_lat:.4f} {max_lat:.4f} --sub-lon {min_lon:.4f} {max_lon:.4f}")

    #### Build the viewPS.py and view.py command strings (second should use velocity.h5 or geo_velocity.h5 depending on geometry but not supported by timeseries2velocity.py).
    #### viewPS.py need to accept scatter_size instead of point_size

    viewsPS1_cmd_parts = [ "viewPS.py", f"{file}.he5"," velocity","--dem geo_geometryRadar.h5 --figsize 8 8" ]
    viewsPS2_cmd_parts = [ "viewPS.py", f"{file}.he5"," velocity","--satellite --figsize 8 8" ]
    viewsPS3_cmd_parts = [ "viewPS.py", f"{file}.he5"," dem_error","--satellite --figsize 8 8" ]
    viewsPS4_cmd_parts = [ "viewPS.py", f"{file}.he5"," elevation","--satellite --figsize 8 8" ]
    view_cmd_parts = [ "view.py velocity.h5 velocity --mask geo_mask.h5 --dem geo_geometryRadar.h5 --alpha 0.8" ] # opacity hardwired

    viewsPS1_cmd_parts.extend( scale + ref_lalo + subset_lalo + point_size )
    viewsPS2_cmd_parts.extend( scale + ref_lalo + subset_lalo + point_size )
    viewsPS3_cmd_parts.extend( ref_lalo + subset_lalo + point_size )
    viewsPS4_cmd_parts.extend( ref_lalo + subset_lalo + point_size )
    view_cmd_parts.extend( ref_lalo + sub_lat_lon + scale + scatter_size )

    viewsPS1_cmd = " ".join(viewsPS1_cmd_parts)
    viewsPS2_cmd = " ".join(viewsPS2_cmd_parts)
    viewsPS3_cmd = " ".join(viewsPS3_cmd_parts)
    viewsPS4_cmd = " ".join(viewsPS4_cmd_parts)
    view_cmd = " ".join(view_cmd_parts)
    ts2velocity_cmd = " ".join(ts2velocity_cmd_parts)
    extract_cmd = " ".join(extract_cmd_parts)

    return plot_data_cmd_parts, ts2velocity_cmd, extract_cmd, view_cmd, viewsPS1_cmd, viewsPS2_cmd ,viewsPS3_cmd, viewsPS4_cmd


def get_dir_log_remote_hdfeos5(he5_file):
    # Get environment variables
    REMOTEHOST_DATA = os.getenv('REMOTEHOST_DATA')
    REMOTEUSER = os.getenv('REMOTEUSER')
    REMOTELOGFILE = os.getenv('REMOTELOGFILE')

    # SSH command to get log file
    command = f"ssh -i {os.getenv('HOME')}/.ssh/id_rsa_jetstream {REMOTEUSER}@{REMOTEHOST_DATA} 'cat {REMOTELOGFILE}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception('ERROR retrieving remote log file in upload_data_products.py')

    logfile_lines = result.stdout.splitlines()

    # Find the line matching the target he5 file
    target_line = next((line for line in logfile_lines if he5_file in line), None)
    if not target_line:
        raise ValueError(f"No entries found for {he5_file}")

    # Extract full path from line (second field)
    try:
        path = target_line.split()[1]
    except IndexError:
        raise ValueError(f"Unexpected line format: {target_line}")

    dir = os.path.dirname(path)
    suffix = [he5_file.split('_')[-1] if 'Del' in he5_file.split('_')[-1] else ''][0]  # e.g., filtDel4DS.he5

    # Extract prefix like RaungSenDT105
    target_prefix = path.split('/')[0]

    match = re.match(r"(?P<volcano>\w+)Sen(?P<node>[AD])\d*", target_prefix)
    if not match:
        raise ValueError(f"Invalid prefix format: {target_prefix}")

    volcano_name = match.group("volcano")
    node_letter = match.group("node")

    # Flip node letter to find counterpart
    counterpart_node = 'D' if node_letter == 'A' else 'A'
    counterpart_prefix = f"{volcano_name}Sen{counterpart_node}"

    # Try to find the counterpart directory
    for line in logfile_lines:
        if he5_file in line:
            continue  # skip the same line

        try:
            other_path = line.split()[1]
        except IndexError:
            continue

        if counterpart_prefix not in other_path:
            continue

        if suffix not in other_path:
            continue

        other_dir = os.path.dirname(other_path)
        print(f"Found counterpart directory for {he5_file}: {other_dir}")
        return dir, other_dir

    print(f"Only found target directory for {he5_file}: {dir}")
    return dir, None


def main():
    # Check for help flag.
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit(0)

    url = sys.argv[1]
    try:
        params = parse_insarmaps_url(url)
    except Exception as e:
        print(f"Error parsing URL: {e}")
        sys.exit(1)

    plot_data_cmd_parts, ts2velocity_cmd, extract_hdfeos5_cmd, view_cmd, viewsPS1_cmd, viewsPS2_cmd, viewsPS3_cmd, viewsPS4_cmd = build_commands(params=params)

    dir, other_node = get_dir_log_remote_hdfeos5(he5_file=params['file'])

    plot_data_cmd_parts = ["plot_data.py", dir, other_node] + plot_data_cmd_parts
    plot_data_cmd_parts = [str(part) if part is not None else '' for part in plot_data_cmd_parts]
    plot_data_cmd = " ".join(plot_data_cmd_parts)

    change_dir_cmd = f"cd {os.getenv('SCRATCHDIR')}/{dir}"

    print()
    print("To plot, run: (Note: *.he5 file is not used by viewPS.py but currently required")
    print()

    print("#"*50)
    print(change_dir_cmd)
    print()
    print("#"*50)
    print(ts2velocity_cmd)
    print()
    print("#"*50)
    print(extract_hdfeos5_cmd)
    print()
    print("#"*50)
    print(plot_data_cmd)
    print()

    # This checks whetehr the file is in GEO or RADAR coordinates
    if params['file'][-1].isdigit():
        print(view_cmd)
    else:
        print("geocode.py geometryRadar.h5")
        print(viewsPS1_cmd,' &')
        print()
        print(viewsPS2_cmd,' &')
        print(viewsPS3_cmd,' &')
        print(viewsPS4_cmd,' &')

    print()
if __name__ == '__main__':
    main()
