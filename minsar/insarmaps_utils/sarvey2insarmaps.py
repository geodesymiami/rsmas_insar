#!/usr/bin/env python3
import os
import argparse
import subprocess
import json
import re
import pickle
import h5py
from pathlib import Path
from datetime import date
from mintpy.utils import readfile
import webbrowser
import sys

sys.path.insert(0, os.getenv("SSARAHOME"))
import password_config as password


def create_parser():
    parser = argparse.ArgumentParser(
        description="End-to-end pipeline for: SARvey shapefiles -> CSV -> JSON -> MBTiles -> Insarmaps",
        epilog="""\
    Examples:

        sarvey2insarmaps.py outputs/shp/p2_coh70_ts.shp
        sarvey2insarmaps.py outputs/shp/p2_coh70_ts.shp --geocorr
        sarvey2insarmaps.py outputs/shp/p2_coh70_ts.shp --make-jobfile
        sarvey2insarmaps.py outputs/shp/p2_coh70_ts.shp --skip-upload

        sarvey2insarmaps.py outputs/p2_coh80_ts.h5
        sarvey2insarmaps.py outputs/p2_coh80_ts.h5 --sarvey-geocorr
    """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", nargs="?", help="Optional input .h5 or .shp file (uses config.json if omitted)")
    parser.add_argument("--config-json", help="Path to config.json (overrides default detection)")
    parser.add_argument("--insarmaps-host",
        default=os.environ.get("INSARMAPS_HOST", os.getenv("INSARMAPSHOST")),
        help="Insarmaps server host (default: environment variable INSARMAPS_HOST)"
    )
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload to Insarmaps")
    parser.add_argument("--make-jobfile", action="store_true", help="Generate jobfile")
    parser.add_argument(
        "--geocorr", dest="do_geocorr", action="store_true",
        help="Enable geolocation correction step (default: off)"
    )
    parser.set_defaults(do_geocorr=False)
    parser.add_argument("--sarvey-geocorr", action="store_true", help="Apply geolocation correction for sarvey_export (--correct_geo)")

    return parser

def load_config_and_input_path(inps):
    """
    Load input path from config.json or infer it from the input file location.
    """
    config_json_path = Path(inps.config_json).resolve() if inps.config_json else None

    if config_json_path and config_json_path.exists():
        print(f"Using config file: {config_json_path}")
        with open(config_json_path) as f:
            config_text = f.read()
            config_text = re.sub(r"(?<![\w\"])(\w+) *:", r'"\1":', config_text)
            config_text = re.sub(r",\s*([\]}])", r"\1", config_text)
            config_data = json.loads(config_text)

        try:
            inputs_path = Path(config_data["general"]["input_path"]).resolve()
            print(f"Inputs path set from config.json: {inputs_path}")
        except (KeyError, TypeError):
            inputs_path = Path("inputs").resolve()
            print("'input_path' not found in config.json. Defaulting to ./inputs/")
    elif inps.input_file:
        inputs_path = Path(inps.input_file).resolve().parents[1] / "inputs"
        print(f"Using inferred inputs path: {inputs_path}")
    else:
        raise ValueError("Must provide either --input_file or a valid config.json.")

    return inputs_path


def set_output_paths(shp_path, dataset_name, do_geocorr):
    """
    Create output directories and return key paths.
    Returns: csv_path, geocorr_csv, json_dir, mbtiles_path, outdir, base_dir
    """
    base_dir = shp_path.parent.parent.resolve()
    outputs_dir = base_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    outdir = outputs_dir / "output_csv"
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{dataset_name}.csv"
    geocorr_csv = outdir / f"{dataset_name}_geocorr.csv"

    json_dir = outputs_dir / "JSON"
    json_dir.mkdir(parents=True, exist_ok=True)
    mbtiles_name = f"{dataset_name}_geocorr.mbtiles" if do_geocorr else f"{dataset_name}.mbtiles"
    mbtiles_path = json_dir / mbtiles_name

    return csv_path, geocorr_csv, json_dir, mbtiles_path, outdir, base_dir

def build_commands(shp_path, csv_path, geocorr_csv, json_dir, mbtiles_path, input_csv, inps):
    """
    Build the list of shell command sequences for the SARvey-to-Insarmaps pipeline.

    Returns four commands:
        cmd1 - Convert SHP to CSV using ogr2ogr with WGS84 coordinates.
        cmd2 - Apply geolocation correction using correct_geolocation.py (if --geocorr).
        cmd3 - Convert CSV or HDF5 to JSON and MBTiles format using hdfeos5_or_csv_2json_mbtiles.py.
        cmd4 - Upload MBTiles and JSON data to the Insarmaps server using json_mbtiles2insarmaps.py.
    """
    cmd1 = ["ogr2ogr", "-f", "CSV", "-lco", "GEOMETRY=AS_XY", "-t_srs", "EPSG:4326", str(csv_path), str(shp_path)]
    cmd2 = ["correct_geolocation.py", str(csv_path), "--outfile", str(geocorr_csv)]
    cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]

    host = inps.insarmaps_host.split(",")[0]
    cmd4 = [
        "json_mbtiles2insarmaps.py",
         "--num-workers", "3",
         "-u", password.docker_insaruser,
         "-p", password.docker_insarpass,
         "--host", host,
         "-P", password.docker_databasepass,
         "-U", password.docker_databaseuser,
         "--json_folder", str(json_dir),
         "--mbtiles_file", str(mbtiles_path),
    ]
    return cmd1, cmd2, cmd3, cmd4

def get_sarvey_export_path():
    """
    Find the path to the 'sarvey_export' executable in the 'sarvey' conda environment.
    """

    #try guessing from the current python executable path
    try:
        conda_root = Path(sys.executable).resolve().parents[2]
        expected_path = conda_root / "envs" / "sarvey" / "bin" / "sarvey_export"
        if expected_path.exists():
            return str(expected_path)
    except Exception as e:
        print(f"[WARN] Could not locate 'sarvey_export' by guessing: {e}")

    #fallback: use conda run
    try:
        result = subprocess.check_output(
            ["conda", "run", "-n", "sarvey", "which", "sarvey_export"],
            universal_newlines=True
        )
        return result.strip()
    except Exception as e:
        raise RuntimeError(f"Could not find 'sarvey_export' using conda run: {e}")


def extract_metadata_from_inputs(inputs_path):
    """
    Extract essential metadata from slcStack.h5 and geometryRadar.h5 to generate a dataset name.
    Returns a dict of metadata and a created dataset name string based on platform, dates, and bbox.
    """
    attributes = {}
    dataset_name = None

    slc_path = inputs_path / "slcStack.h5"
    geom_path = inputs_path / "geometryRadar.h5"

    #load slcStack.h5 attributes
    if slc_path.exists():
        slc_attr = readfile.read_attribute(str(slc_path))
        
        keys_to_extract = [
            "mission", "PLATFORM", "beam_mode", "flight_direction", "relative_orbit",
            "processing_method", "REF_LAT", "REF_LON", "areaName", "DATE",
            "LAT_REF1", "LAT_REF2", "LAT_REF3", "LAT_REF4",
            "LON_REF1", "LON_REF2", "LON_REF3", "LON_REF4"
        ]
        for key in keys_to_extract:
            if key in slc_attr:
                attributes[key] = slc_attr[key]

    #load geometryRadar.h5 attributes
    if geom_path.exists():
        geom_attr = readfile.read_attribute(str(geom_path))
        if "beamSwath" in geom_attr:
            attributes["beamSwath"] = geom_attr["beamSwath"]

    #set default/fallback attributes
    attributes.setdefault("data_type", "LOS_TIMESERIES")
    attributes.setdefault("look_direction", "R" if attributes.get("mission", "").upper() != "NISAR" else "L")
    attributes.setdefault("start_date", "TO_INFER")
    attributes.setdefault("end_date", "TO_INFER")
    attributes.setdefault("history", str(date.today()))
    attributes.setdefault("data_footprint", "TO_INFER")

    #generate dataset name
    try:
        #normalize platform name
        platform_raw = (attributes.get("PLATFORM") or attributes.get("mission") or "").upper()
        platform_aliases = {
            "TSX": "TSX", "TERRASAR-X": "TSX", "SENTINEL-1": "S1", "S1": "S1",
            "ERS": "ERS", "ENVISAT": "ENVISAT", "ALOS": "ALOS"
        }
        mission = platform_aliases.get(platform_raw, platform_raw or "S1")

        #orbit
        rel_orbit_raw = attributes.get("relative_orbit", "")
        rel_orbit = f"{int(rel_orbit_raw):03d}" if str(rel_orbit_raw).isdigit() else "000"

        #default date values
        start_date, end_date = "YYYYMMDD", "YYYYMMDD"

        #try to get actual start/end dates from dataset
        if slc_path.exists():
            try:
                with h5py.File(slc_path, "r") as f:
                    if "date" in f:
                        date_list = [d.decode() if isinstance(d, bytes) else str(d) for d in f["date"][:]]
                        if date_list:
                            start_date, end_date = date_list[0], date_list[-1]
            except Exception as e:
                print(f"[WARN] Could not read 'date' dataset from slcStack.h5: {e}")

        #use bounding box to generate geographic part of the name
        lat_vals = [float(attributes[k]) for k in ["LAT_REF1", "LAT_REF2", "LAT_REF3", "LAT_REF4"] if k in attributes]
        lon_vals = [float(attributes[k]) for k in ["LON_REF1", "LON_REF2", "LON_REF3", "LON_REF4"] if k in attributes]

        if lat_vals and lon_vals:
            lat1 = f"N{int(min(lat_vals) * 10000):05d}"
            lat2 = f"N{int(max(lat_vals) * 10000):05d}"
            lon1 = f"W{abs(int(max(lon_vals) * 10000)):06d}"
            lon2 = f"W{abs(int(min(lon_vals) * 10000)):06d}"
            dataset_name = f"{mission}_{rel_orbit}_{start_date}_{end_date}_{lat1}_{lat2}_{lon1}_{lon2}"
        else:
            dataset_name = f"{mission}_{rel_orbit}_{start_date}_{end_date}"

    except Exception as e:
        print(f"[WARN] Could not generate dataset_name: {e}")

    #info summary
    mission = attributes.get('mission') or attributes.get('PLATFORM')
    platform = attributes.get('PLATFORM')
    beam = attributes.get('beam_mode')
    orbit = attributes.get('relative_orbit')

    bbox = f"({attributes.get('LAT_REF3')}, {attributes.get('LON_REF4')}) to ({attributes.get('LAT_REF2')}, {attributes.get('LON_REF1')})"

    print(f"[INFO] slcStack.h5: mission={mission}, platform={platform}, beam_mode={beam}, orbit={orbit}")
    print(f"[INFO] bounding box: {bbox}")
    print(f"[INFO] dataset name: {dataset_name}")
    
    return attributes, dataset_name


def run_command(command, shell=False, cwd=None):
    """
    Execute a shell command and print the command string.
    """
    cmd_str = ' '.join(command) if isinstance(command, list) else command
    print(f"\nRunning: {cmd_str}")
    try:
        subprocess.run(command, check=True, shell=shell, cwd=str(cwd) if cwd else None)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with return code {e.returncode}: {cmd_str}")
        raise

def create_jobfile(inps, input_path, cmds, json_dir, base_dir, mbtiles_path, dataset_name, metadata):
    """
    Generate a SLURM-compatible jobfile with all processing steps and Insarmaps URL.
    """
    cmd0, cmd1, cmd2, cmd3, cmd4 = cmds
    jobfile_path = base_dir / "sarvey2insarmaps.job"
    slurm_commands = []

    if input_path.suffix == ".h5":
        slurm_commands.append(" ".join(cmd0))

    slurm_commands.append(" ".join(cmd1))

    if inps.do_geocorr:
        slurm_commands.append(" ".join(cmd2))

    main_host = inps.insarmaps_host.split(",")[0]
    slurm_commands.extend([
        f"rm -rf {json_dir}",
        " ".join(cmd3),
        " ".join(cmd4).replace(inps.insarmaps_host, "insarmaps.miami.edu") + " &",
        " ".join(cmd4).replace(inps.insarmaps_host, main_host) + " &"
    ])

    with open(jobfile_path, 'w') as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Generated by sarvey2insarmaps.py\n")
        f.write(f"# Dataset: {dataset_name}\n")
        f.write(f"# Generated on: {date.today()}\n\n")

        for cmd in slurm_commands:
            f.write(cmd + "\n")
            if any(key in cmd for key in ("rm -rf", "geolocation", "hdfeos5")):
                f.write("\n")

        f.write("wait\n\n")

        ref_lat = metadata.get("REF_LAT", 26.1)
        ref_lon = metadata.get("REF_LON", -80.1)
        suffix = "_geocorr" if "_geocorr" in mbtiles_path.stem else ""
        
        for host in ["insarmaps.miami.edu", "149.165.153.50"]:
            f.write(
                f"cat >> insarmaps.log<<EOF\n"
                f"https://{host}/start/{ref_lat:.4f}/{ref_lon:.4f}/11.0?flyToDatasetCenter=true&startDataset={dataset_name}{suffix}\n"
                f"EOF\n\n"
            )

    print(f"\nJobfile created: {jobfile_path}")

def main():
    parser = create_parser()
    inps = parser.parse_args()
    print(f"Geolocation correction enabled: {inps.do_geocorr}")

    inputs_path = load_config_and_input_path(inps)

    #ensure required files exist
    required_files = ["slcStack.h5", "geometryRadar.h5"]
    for fname in required_files:
        fpath = inputs_path / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Required file not found: {fpath}")

    metadata, dataset_name = extract_metadata_from_inputs(inputs_path)
    
    if not metadata:
        print("[WARN] No metadata found in slcStack.h5 or geometryRadar.h5.")

    #use $RSMASINSAR_HOME as the root for now (temporarily)
    rsmasinsar_env = os.environ.get("RSMASINSAR_HOME")
    if not rsmasinsar_env:
        raise EnvironmentError("Environment variable RSMASINSAR_HOME is not set.")

    #input/output paths
    input_path = Path(inps.input_file).resolve()
    if input_path.suffix == ".h5":
        h5_path = input_path
        shp_path = h5_path.parent / "shp" / f"{h5_path.stem}.shp"
        print(f"[INFO] Input is HDF5. Inferred shapefile path: {shp_path}")
        #step0: always run sarvey_export if input is HDF5
        sarvey_export_path = get_sarvey_export_path()
        cmd0 = [sarvey_export_path, str(h5_path), "-o", str(shp_path)]
        if inps.sarvey_geocorr:
            print("[INFO] Applying SARvey geolocation correction")
            cmd0.append("--correct_geo")
    else:
        shp_path = input_path
        h5_path = shp_path.with_suffix(".h5")
        print(f"[INFO] Input is SHP. Inferred HDF5 path: {h5_path}")


    csv_path, geocorr_csv, json_dir, mbtiles_path, outdir, base_dir = set_output_paths(shp_path, dataset_name, inps.do_geocorr)

    input_csv = geocorr_csv if inps.do_geocorr else csv_path
    cmd1, cmd2, cmd3, cmd4 = build_commands(
        shp_path, csv_path, geocorr_csv, json_dir, mbtiles_path, input_csv, inps
    )

    if inps.make_jobfile:
            print("[INFO] Creating jobfile only, skipping execution.")
            create_jobfile(inps, input_path, (cmd0, cmd1, cmd2, cmd3, cmd4), json_dir, base_dir, mbtiles_path, dataset_name, metadata)
            return
    
    #only run if not --make-jobfile
    if input_path.suffix == ".h5":
        run_command(cmd0, cwd=h5_path.parent.parent)

    cmds = (cmd0, cmd1, cmd2, cmd3, cmd4)

    #run all steps sequentially
    run_command(cmd1)
    if inps.do_geocorr:
        run_command(cmd2)
    run_command(cmd3)

    final_metadata_path = json_dir / "metadata.pickle"
    if final_metadata_path.exists():
        try:
            with open(final_metadata_path, "rb") as f:
                meta = pickle.load(f)
            final_metadata = meta.get("attributes", {})
            for key in ["first_date", "last_date", "data_footprint"]:
                if key in final_metadata:
                    metadata[key.replace("first_", "start_").replace("last_", "end_")] = final_metadata[key]
            for ref_key in ["REF_LAT", "REF_LON"]:
                if ref_key in final_metadata:
                    metadata[ref_key] = float(final_metadata[ref_key])
        except Exception as e:
            print(f"Warning: Failed to read final metadata from pickle: {e}")

    #update metadata with inferred values from *_metadata.pickle
    final_meta_path = outdir / f"{dataset_name}_final_metadata.json"
    with open(final_meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"[INFO] Final metadata written to: {final_meta_path}")

    if not inps.skip_upload:
        run_command(cmd4)

    print("\nAll done!")
    ref_lat = metadata.get("REF_LAT", 26.1)
    ref_lon = metadata.get("REF_LON", -80.1)
    suffix = "_geocorr" if inps.do_geocorr else ""
    protocol = "https" if inps.insarmaps_host.startswith("insarmaps.miami.edu") else "http"
    main_host = inps.insarmaps_host.split(",")[0]
    url = f"{protocol}://{main_host}/start/{ref_lat:.4f}/{ref_lon:.4f}/11.0?flyToDatasetCenter=true&startDataset={dataset_name}{suffix}"
    print(f"\nView on Insarmaps:\n{url}")
    webbrowser.open(url)

if __name__ == "__main__":
    main()
