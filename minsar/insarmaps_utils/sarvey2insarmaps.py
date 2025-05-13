#!/usr/bin/env python3
import argparse
import os
import subprocess
from pathlib import Path
import json
import ast
from mintpy.utils import readfile
from datetime import date
import re
import pickle
from shapely.geometry import box
import webbrowser


def find_script(script_name, search_paths):
    for path in search_paths:
        full_path = Path(path) / script_name
        if full_path.exists():
            return str(full_path)
    raise FileNotFoundError(f"Could not find {script_name} in {search_paths}")

def extract_metadata_from_inputs(inputs_path):
    attributes = {}
    standardized_stem = None

    slc_path = inputs_path / "slcStack.h5"
    geom_path = inputs_path / "geometryRadar.h5"

    if slc_path.exists():
        slc_attr = readfile.read_attribute(str(slc_path))
        for key in ["mission", "beam_mode", "flight_direction", "relative_orbit", "processing_method",
                    "REF_LAT", "REF_LON", "areaName", "DATE", "LAT_REF1", "LAT_REF2", "LAT_REF3", "LAT_REF4",
                    "LON_REF1", "LON_REF2", "LON_REF3", "LON_REF4"]:
            if key in slc_attr:
                attributes[key] = slc_attr[key]

    if geom_path.exists():
        geom_attr = readfile.read_attribute(str(geom_path))
        if "beamSwath" in geom_attr:
            attributes["beamSwath"] = geom_attr["beamSwath"]

    attributes["data_type"] = "LOS_TIMESERIES"
    attributes["look_direction"] = "R" if attributes.get("mission", "").upper() != "NISAR" else "L"
    attributes["start_date"] = "TO_INFER"
    attributes["end_date"] = "TO_INFER"
    attributes["history"] = str(date.today())
    attributes["data_footprint"] = "TO_INFER"

    #build standardized_stem from slcStack.h5
    try:
        mission = attributes.get("mission", "S1")
        rel_orbit = f"{int(attributes.get('relative_orbit', 0)):03d}"
        start_date = attributes.get("DATE", "YYYYMMDD")
        end_date = "XXXXXXXX"

        # bbox from LAT_REF/LON_REF
        lat_vals = [float(attributes[k]) for k in ["LAT_REF1", "LAT_REF2", "LAT_REF3", "LAT_REF4"] if k in attributes]
        lon_vals = [float(attributes[k]) for k in ["LON_REF1", "LON_REF2", "LON_REF3", "LON_REF4"] if k in attributes]

        if lat_vals and lon_vals:
            min_lat = min(lat_vals)
            max_lat = max(lat_vals)
            min_lon = min(lon_vals)
            max_lon = max(lon_vals)

            lat1 = f"N{int(min_lat * 10000):05d}"
            lat2 = f"N{int(max_lat * 10000):05d}"
            lon1 = f"W{abs(int(max_lon * 10000)):06d}"
            lon2 = f"W{abs(int(min_lon * 10000)):06d}"

            standardized_stem = f"{mission}_{rel_orbit}_{start_date}_{end_date}_{lat1}_{lat2}_{lon1}_{lon2}"
    except Exception as e:
        print(f"Warning: Could not generate standardized_stem: {e}")

    return attributes, standardized_stem

def run_command(command, shell=False):
    print(f"\nRunning: {' '.join(command) if isinstance(command, list) else command}")
    subprocess.run(command, check=True, shell=shell)


def create_jobfile(jobfile_path, commands, mbtiles_path, dataset_name):
    with open(jobfile_path, 'w') as f:
        f.write("#!/bin/bash\n\n")

        for cmd in commands:
            f.write(cmd + "\n")
            if "rm -rf" in cmd or "geolocation" in cmd or "hdfeos5" in cmd:
                f.write("\n")

        f.write("wait\n\n")

        suffix = "_geocorr" if "_geocorr" in mbtiles_path.stem else ""
        f.write(f"cat >> insarmaps.log<<EOF\nhttps://insarmaps.miami.edu/start/26.1/-80.1/11.0?flyToDatasetCenter=true&startDataset={dataset_name}{suffix}\nEOF\n\n")
        f.write(f"cat >> insarmaps.log<<EOF\nhttps://149.165.153.50/start/26.1/-80.1/11.0?flyToDatasetCenter=true&startDataset={dataset_name}{suffix}\nEOF\n")
    print(f"\nJobfile created: {jobfile_path}")


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end pipeline for: SARvey shapefiles -> csv -> Geocorrected csv -> JSON -> MBTiles -> Insarmaps",
        epilog="""\
    Example:
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp --no-geocorr
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp --make-jobfile
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp --skip-upload
    """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("shapefile", help="Input shapefile path")
    parser.add_argument("--config-json", help="Path to config.json (overrides default detection)")
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload to Insarmaps")
    parser.add_argument("--make-jobfile", action="store_true", help="Generate jobfile")
    parser.add_argument("--no-geocorr", dest="do_geocorr", action="store_false", help="Skip geolocation correction step")
    parser.set_defaults(do_geocorr=True)
    parser.add_argument("--insarmaps-host", default="insarmaps.miami.edu")
    parser.add_argument("--insarmaps-user", default="insaradmin")
    parser.add_argument("--insarmaps-pass", default="insaradmin")
    parser.add_argument("--insarmaps-email", default="insarmaps@insarmaps.com")
    args = parser.parse_args()
    print(f"Geolocation correction enabled: {args.do_geocorr}")

    #load config.json if provided or found in working dir
    config_json_path = None
    if args.config_json:
        config_json_path = Path(args.config_json).resolve()
    elif Path("config.json").exists():
        config_json_path = Path("config.json").resolve()

    if config_json_path:
        print(f"Using config file: {config_json_path}")
        with open(config_json_path) as f:
            config_text = f.read()
            #formatting to valid JSON because SARvey's config.json uses unquoted keys and trailing commas
            config_text = re.sub(r"(?<![\w\"]) (\w+) *:", r'"\1":', config_text)  #quote keys
            config_text = re.sub(r",\s*([\]}])", r"\1", config_text)              #remove trailing commas
            config_text = config_text.replace("null", "null").replace("true", "true").replace("false", "false")  #keeps JSON-compatible
            config_data = json.loads(config_text)
        inputs_path = Path(config_data["general"]["input_path"]).resolve()
    else:
        inputs_path = Path("inputs").resolve()

    metadata, standardized_stem = extract_metadata_from_inputs(inputs_path)
    if not metadata:
        print("Warning: No metadata found in slcStack.h5 or geometryRadar.h5.")
    else:
        print("Extracted metadata:", metadata)

    #use $RSMASINSAR_HOME as the root for now (temporarily)
    rsmasinsar_env = os.environ.get("RSMASINSAR_HOME")
    if not rsmasinsar_env:
        raise EnvironmentError("Environment variable RSMASINSAR_HOME is not set.")
    scripts_root = Path(rsmasinsar_env).resolve()

    #input/output paths
    shp_path = Path(args.shapefile).resolve()
    stem = shp_path.stem
    final_stem = standardized_stem if standardized_stem else stem

    base_dir = shp_path.parent.parent.parent.resolve()

    outdir = base_dir / "output_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = outdir / f"{final_stem}.csv"
    geocorr_csv = outdir / f"{final_stem}_geocorr.csv"

    json_dir = base_dir / "JSON"
    json_dir.mkdir(parents=True, exist_ok=True)

    mbtiles_path = json_dir / f"{final_stem}_geocorr.mbtiles" if args.do_geocorr else json_dir / f"{final_stem}.mbtiles"

    #locate scripts
    search_dirs = [
        scripts_root / "minsar" / "insarmaps_utils",
        scripts_root / "tools",
        scripts_root / "tools" / "insarmaps_scripts",
    ]
    correct_geolocation = find_script("correct_geolocation.py", search_dirs)
    to_json = find_script("hdfeos5_or_csv_2json_mbtiles.py", search_dirs)
    to_insarmaps = find_script("json_mbtiles2insarmaps.py", search_dirs)

    #commands
    cmd1 = ["ogr2ogr", "-f", "CSV", "-lco", "GEOMETRY=AS_XY", "-t_srs", "EPSG:4326", str(csv_path), str(shp_path)]
    cmd2 = [correct_geolocation, str(csv_path), "--outfile", str(geocorr_csv)]
    #for geocorr option
    if args.do_geocorr:
        input_csv = geocorr_csv
    else:
        input_csv = csv_path
    cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]
    cmd4 = ["json_mbtiles2insarmaps.py", "--num-workers", "3", "-u", args.insarmaps_user, "-p", args.insarmaps_pass,
            "--host", args.insarmaps_host, "-P", "insarmaps", "-U", args.insarmaps_email,
            "--json_folder", str(json_dir), "--mbtiles_file", str(mbtiles_path)]

    if args.make_jobfile:
        slurm_commands = [
            f"{' '.join(cmd1)}",
        ]
        if args.do_geocorr:
            slurm_commands.append(f"{' '.join(cmd2)}")
            input_csv = geocorr_csv
        else:
            input_csv = csv_path

        cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]

        slurm_commands.extend([
            f"rm -rf {json_dir}",
            f"{' '.join(cmd3)}",
            f"{' '.join(cmd4)} &",
            f"{' '.join(cmd4).replace(args.insarmaps_host, '149.165.153.50')} &"
        ])
        create_jobfile(base_dir / "sarvey2insarmaps.job", slurm_commands, mbtiles_path, final_stem)
        return

    #run all steps sequentially
    run_command(cmd1)
    if args.do_geocorr:
        run_command(cmd2)
        input_csv = geocorr_csv
    else:
        input_csv = csv_path

    cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]
    run_command(cmd3)
    #update metadata with inferred values from *_metadata.pickle
    final_metadata_path = json_dir / "metadata.pickle"
    if final_metadata_path.exists():
        try:
            with open(final_metadata_path, "rb") as f:
                meta = pickle.load(f)

            final_metadata = meta.get("attributes", {})

            for key in ["first_date", "last_date", "data_footprint"]:
                if key in final_metadata:
                    metadata[key.replace("first_", "start_").replace("last_", "end_")] = final_metadata[key]

            #add REF_LAT and REF_LON to metadata
            for ref_key in ["REF_LAT", "REF_LON"]:
                if ref_key in final_metadata:
                    metadata[ref_key] = float(final_metadata[ref_key])

        except Exception as e:
            print(f"Warning: Failed to read final metadata from pickle: {e}")

    print("Final metadata with inferred values:", metadata)

    #store final metadata for documentation
    final_meta_path = outdir / f"{final_stem}_final_metadata.json"
    with open(final_meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved final metadata to: {final_meta_path}")

    if not args.skip_upload:
        run_command(cmd4)

    print("\nAll done!")
    ref_lat = metadata.get("REF_LAT", 26.1)
    ref_lon = metadata.get("REF_LON", -80.1)

    suffix = "_geocorr" if args.do_geocorr else ""

    protocol = "https" if args.insarmaps_host == "insarmaps.miami.edu" else "http"
    url = f"{protocol}://{args.insarmaps_host}/start/{ref_lat:.4f}/{ref_lon:.4f}/11.0?flyToDatasetCenter=true&startDataset={final_stem}{suffix}"

    print(f"\nView on Insarmaps:\n{url}")

    webbrowser.open(url)

if __name__ == "__main__":
    main()
