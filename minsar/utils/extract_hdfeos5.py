#!/usr/bin/env python
import argparse
import glob
import sys
import os
import shutil
import h5py
import numpy as np  
from pathlib import Path
from mintpy.utils import readfile, writefile
from mintpy.objects import HDFEOS

def find_attribute(obj, key):
    """
    Recursively search for an attribute 'key' in the HDF5 object 'obj'.
    Returns the attribute value if found, or None otherwise.
    """
    if key in obj.attrs:
        return obj.attrs[key]
    for subkey in obj:
        try:
            subobj = obj[subkey]
        except Exception:
            continue
        result = find_attribute(subobj, key)
        if result is not None:
            return result
    return None

def determine_coordinates(file_path):
    """
    Determine coordinate system from the mask dataset attributes.
    Returns 'GEO' if Y_FIRST is in the attribute keys, else 'RADAR'.
    """
    try:
        _, attr = readfile.read(file_path, datasetName='HDFEOS/GRIDS/timeseries/quality/mask')
        if 'Y_FIRST' in attr.keys():
            print("Detected coordinates: GEO")
            return 'GEO'
    except Exception:
        pass
    print("Detected coordinates: RADAR")
    return 'RADAR'

def extract_mask(file_path, coords):
    data, attr = readfile.read(file_path, datasetName='HDFEOS/GRIDS/timeseries/quality/mask')
    attr['FILE_TYPE'] = 'mask'
    out_file = "geo_mask.h5" if coords=="GEO" else "mask.h5"
    writefile.write(data, out_file=out_file, metadata=attr)
    print(f"Extracted mask -> {out_file}")

def extract_avgSpatialCoherence(file_path, coords):
    data, attr = readfile.read(file_path, datasetName='HDFEOS/GRIDS/timeseries/quality/avgSpatialCoherence')
    attr['FILE_TYPE'] = 'avgSpatialCoherence'
    out_file = "geo_avgSpatialCoherence.h5" if coords=="GEO" else "avgSpatialCoherence.h5"
    writefile.write(data, out_file=out_file, metadata=attr)
    print(f"Extracted avgSpatialCoherence -> {out_file}")

def extract_temporalCoherence(file_path, coords):
    data, attr = readfile.read(file_path, datasetName='HDFEOS/GRIDS/timeseries/quality/temporalCoherence')
    attr['FILE_TYPE'] = 'temporalCoherence'
    out_file = "geo_temporalCoherence.h5" if coords=="GEO" else "temporalCoherence.h5"
    writefile.write(data, out_file=out_file, metadata=attr)
    print(f"Extracted temporalCoherence -> {out_file}")

def extract_geometry(file_path, coords):
    group_path = 'HDFEOS/GRIDS/timeseries/geometry'
    slices = ['azimuthAngle', 'height', 'incidenceAngle', 'latitude', 'longitude', 'shadowMask', 'slantRangeDistance']
    geo_data = {}
    geo_attr = {}
    for s in slices:
        dset_path = f"{group_path}/{s}"
        try:
            data, attr = readfile.read(file_path, datasetName=dset_path)
            geo_data[s] = data
            if not geo_attr:
                geo_attr = attr
        except Exception as e:
            print(f"Warning: Could not extract slice '{s}' from {dset_path}: {e}", file=sys.stderr)
    geo_attr['FILE_TYPE'] = 'geometry'
    geo_attr['COORDINATES'] = coords
    out_file = "geo_geometryRadar.h5" if coords=="GEO" else "geometryRadar.h5"
    writefile.write(geo_data, out_file=out_file, metadata=geo_attr)
    print(f"Extracted geometry -> {out_file}")

    if coords=="RADAR":
        os.makedirs('inputs',exist_ok=True)
        shutil.copy('geometryRadar.h5', 'inputs')
        print("Copied geometryRadar.h5 into inputs")

def extract_timeseries(file_path, coords):
    """
    Extract all displacement datasets from HDFEOS/GRIDS/timeseries/observation.
    Uses HDFEOS from mintpy.objects to obtain the date list.
    Each displacement dataset (named as displacement-YYYYMMDD) is read with readfile.read,
    then renamed to timeseries-YYYYMMDD. The sorted date list is forced into the metadata,
    ensuring that the 'date' dataset exists.
    """
    h = HDFEOS(file_path)
    date_list = h.get_date_list()
    if not date_list:
        print("Error: No displacement datasets found.", file=sys.stderr)
        sys.exit(1)
    date_list = sorted(date_list)
    
    dataset_name_list = []
    for date_str in date_list:
        dataset_name_list.append(f'HDFEOS/GRIDS/timeseries/observation/displacement-{date_str}')
    
    data, attr  = readfile.read(file_path, datasetName=dataset_name_list)

    with h5py.File(file_path, 'r') as f:
        original_file_path = f.attrs.get('FILE_PATH')
        basename = Path(original_file_path).name

    attr['FILE_TYPE'] = 'timeseries'
    out_file = f"geo_{basename}" if coords=="GEO" else basename

    dates = np.array(date_list, dtype='S8')

    num_date, length, width = data.shape

    with h5py.File(file_path, 'r') as f:
        bperp = f["HDFEOS/GRIDS/timeseries/observation/bperp"][()]

    pbase = bperp 
    ds_name_dict = {
        "date"       : [dates.dtype, (num_date,), dates],
        "bperp"      : [np.float32,  (num_date,), pbase],
        "timeseries" : [np.float32,  (num_date, length, width), None],
        }

    box = [0, 0, data.shape[2], data.shape[1]]
    block = [0, num_date, box[1], box[3], box[0], box[2]]
    writefile.layout_hdf5(out_file, ds_name_dict, metadata=attr)
    writefile.write_hdf5_block(out_file, data=data, datasetName= 'timeseries', block=block)
    print(f"Extracted timeseries (displacement) -> {out_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract slices from a MintPy HDFEOS file (reverse of save_hdfeos5.py).  "
                    "By default extracts mask, avgSpatialCoherence, temporalCoherence, and geometry. "
                    "Use --all to also extract the displacement (timeseries) datasets."
    )
    parser.add_argument("infile", help="Input S1* HDFEOS file.")
    parser.add_argument("--all", action="store_true",
                        help="Extract all slices including the displacement (timeseries) datasets.")
    args = parser.parse_args()

    file_list = glob.glob(args.infile)
    if not file_list:
        print(f"Error: No file found at path {args.infile}.", file=sys.stderr)
        sys.exit(1)
    file_path = file_list[0]

    coords = determine_coordinates(file_path)
    extract_mask(file_path, coords)
    extract_avgSpatialCoherence(file_path, coords)
    extract_temporalCoherence(file_path, coords)
    extract_geometry(file_path, coords)

    if args.all:
        extract_timeseries(file_path, coords)

if __name__ == "__main__":
    main()
