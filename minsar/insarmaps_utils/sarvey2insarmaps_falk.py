#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import json
import re
import webbrowser
import h5py
from pathlib import Path
from datetime import date
import pickle
from mintpy.utils import readfile


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
        print("slcStack.h5 attributes:", slc_attr)

        for key in ["mission", "PLATFORM", "beam_mode", "flight_direction", "relative_orbit", "processing_method",
                    "REF_LAT", "REF_LON", "areaName", "DATE", "LAT_REF1", "LAT_REF2", "LAT_REF3", "LAT_REF4",
                    "LON_REF1", "LON_REF2", "LON_REF3", "LON_REF4"]:
            if key in slc_attr:
                attributes[key] = slc_attr[key]

    if geom_path.exists():
        geom_attr = readfile.read_attribute(str(geom_path))
        if "beamSwath" in geom_attr:
            attributes["beamSwath"] = geom_attr["beamSwath"]

    # Default values
    attributes["data_type"] = "LOS_TIMESERIES"
    attributes["look_direction"] = "R" if attributes.get("mission", "").upper() != "NISAR" else "L"
    attributes["start_date"] = "TO_INFER"
    attributes["end_date"] = "TO_INFER"
    attributes["history"] = str(date.today())
    attributes["data_footprint"] = "TO_INFER"

    # Attempt to build standardized_stem
    try:
        platform_raw = (attributes.get("PLATFORM") or attributes.get("mission") or "").upper()
        platform_aliases = {
            "TSX": "TSX",
            "TERRASAR-X": "TSX",
            "SENTINEL-1": "S1",
            "S1": "S1",
            "ERS": "ERS",
            "ENVISAT": "ENVISAT",
            "ALOS": "ALOS",
        }
        mission = platform_aliases.get(platform_raw, platform_raw or "S1")
        rel_orbit_raw = attributes.get("relative_orbit", "")
        rel_orbit = f"{int(rel_orbit_raw):03d}" if str(rel_orbit_raw).isdigit() else "000"

        # Default fallback values
        start_date = "YYYYMMDD"
        end_date = "XXXXXXXX"

        # Try reading from /date dataset in slcStack.h5
        if slc_path.exists():
            try:
                with h5py.File(slc_path, "r") as f:
                    if "date" in f:
                        date_list = [d.decode() if isinstance(d, bytes) else str(d) for d in f["date"][:]]
                        if date_list:
                            start_date = date_list[0]
                            end_date = date_list[-1]
            except Exception as e:
                print(f"Warning: Could not read 'date' dataset: {e}")

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
        else:
            standardized_stem = f"{mission}_{rel_orbit}_{start_date}_{end_date}"

    except Exception as e:
        print(f"Warning: Could not generate standardized_stem: {e}")

    print("standardized_stem:", standardized_stem)
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
    Examples:

        sarvey2insarmaps.py ./outputs/shp/p2_coh70_ts.shp
        sarvey2insarmaps.py ./outputs/shp/p2_coh70_ts.shp --no-geocorr
        sarvey2insarmaps.py ./outputs/shp/p2_coh70_ts.shp --make-jobfile
        sarvey2insarmaps.py ./outputs/shp/p2_coh70_ts.shp --insarmaps-host 149.165.153.50
        sarvey2insarmaps.py ./outputs/shp/p2_coh70_ts.shp --skip-upload

    """,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("ts_file", help="Input ts file path (.)")
    parser.add_argument("--config-json", help="Path to config.json (overrides default detection)")
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload to Insarmaps")
    parser.add_argument("--make-jobfile", action="store_true", help="Generate jobfile")
    parser.add_argument("--no-geocorr", dest="do_geocorr", action="store_false", help="Skip geolocation correction step")
    parser.set_defaults(do_geocorr=False)
    parser.add_argument("--insarmaps-host",
        default=os.environ.get("INSARMAPS_HOST", os.getenv("INSARMAPSHOST")),
        help="Insarmaps server host (default: environment variable INSARMAPS_HOST)"
    )

    inps = parser.parse_args()

    sys.path.insert(0, os.getenv('SSARAHOME'))
    import password_config as password

    print(f"Geolocation correction enabled: {inps.do_geocorr}")

    #load config.json if provided or found in working dir
    inputs_path = None

    if inps.config_json:
        config_json_path = Path(inps.config_json).resolve()
    elif Path("config.json").exists():
        config_json_path = Path("config.json").resolve()
    else:
        config_json_path = None

    if config_json_path:
        print(f"Using config file: {config_json_path}")
        with open(config_json_path) as f:
            config_text = f.read()
            # formatting to valid JSON because SARvey's config.json uses unquoted keys and trailing commas
            config_text = re.sub(r"(?<![\w\"]) (\w+) *:", r'"\1":', config_text)
            config_text = re.sub(r",\s*([\]}])", r"\1", config_text)
            config_text = config_text.replace("null", "null").replace("true", "true").replace("false", "false")
            config_data = json.loads(config_text)

        try:
            inputs_path = Path(config_data["general"]["input_path"]).resolve()
            print(f"Inputs path set from config.json: {inputs_path}")
        except (KeyError, TypeError):
            inputs_path = Path("inputs").resolve()
            print("'input_path' not found in config.json. Defaulting to ./inputs/")
    else:
        inputs_path = Path(inps.ts_file).resolve().parents[1] / "inputs"
        print(f"Using inferred inputs path: {inputs_path}")



    # Ensure required files exist
    required_files = ["slcStack.h5", "geometryRadar.h5"]
    for fname in required_files:
        fpath = inputs_path / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Required file not found: {fpath}")
    
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
    ts_fullpath = Path(inps.ts_file).resolve()
    stem = ts_fullpath.stem
    final_stem = standardized_stem if standardized_stem else stem

    base_dir = ts_fullpath.parent.parent.resolve()

    outputs_dir = base_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    outdir = outputs_dir / "output_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = outdir / f"{final_stem}.csv"
    geocorr_csv = outdir / f"{final_stem}_geocorr.csv"

    json_dir = outputs_dir / "JSON"
    json_dir.mkdir(parents=True, exist_ok=True)

    mbtiles_path = json_dir / f"{final_stem}_geocorr.mbtiles" if inps.do_geocorr else json_dir / f"{final_stem}.mbtiles"

    #locate scripts
    search_dirs = [
        scripts_root / "minsar" / "insarmaps_utils",
        scripts_root / "tools",
        scripts_root / "tools" / "insarmaps_scripts",
    ]
    correct_geolocation = find_script("correct_geolocation.py", search_dirs)
    # to_json = find_script("hdfeos5_or_csv_2json_mbtiles.py", search_dirs)
    # to_insarmaps = find_script("json_mbtiles2insarmaps.py", search_dirs)

    #commands
    import subprocess

    env_bin = os.path.dirname(sys.executable)
    miniforge_root = os.path.dirname(env_bin)
    sarvey_export_path = os.path.join(miniforge_root, 'bin', 'sarvey_export')
    sarvey_export_path = os.path.join(miniforge_root, 'envs', 'sarvey', 'bin', 'sarvey_export')

    # env_bin: miniforge3/bin
    # Falk:    miniforge3/bin/sarvey_export
    # Emirhan: miniforge3/envs/sarvey/bin/sarvey_export

    # cmd0 = [sarvey_export_path, ts_fullpath, '-o', f"{outdir}/{stem}.shp"]
    cmd0 = [sarvey_export_path, inps.ts_file, '-o', f"{outdir}/{stem}.shp"]

    # subprocess.run(cmd, check=True)
    # cmd1 = ["ogr2ogr", "-f", "CSV", "-lco", "GEOMETRY=AS_XY", "-t_srs", "EPSG:4326", str(csv_path), str(shp_path)]
    cmd1 = ["ogr2ogr", "-f", "CSV", "-lco", "GEOMETRY=AS_XY", "-t_srs", "EPSG:4326", str(csv_path),  f"{outdir}/{stem}.shp"]
    cmd2 = [correct_geolocation, str(csv_path), "--outfile", str(geocorr_csv)]

    #for geocorr option
    if inps.do_geocorr:
        input_csv = geocorr_csv
    else:
        input_csv = csv_path
    cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]
    cmd4 = ["json_mbtiles2insarmaps.py", "--num-workers", "3", "-u", password.docker_insaruser, "-p", password.docker_insarpass,
            "--host", inps.insarmaps_host, "-P", "insarmaps", "-U", password.docker_databaseuser,
            "--json_folder", str(json_dir), "--mbtiles_file", str(mbtiles_path)]

    # if inps.make_jobfile:
    #     slurm_commands = [
    #         f"{' '.join(cmd1)}",
    #     ]
    #     if inps.do_geocorr:
    #         slurm_commands.append(f"{' '.join(cmd2)}")
    #         input_csv = geocorr_csv
    #     else:
    #         input_csv = csv_path

    #     cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(input_csv), str(json_dir)]

    #     slurm_commands.extend([
    #         f"rm -rf {json_dir}",
    #         f"{' '.join(cmd3)}",
    #         f"{' '.join(cmd4)} &",
    #         f"{' '.join(cmd4).replace(inps.insarmaps_host, '149.165.153.50')} &"
    #     ])
    #     create_jobfile(base_dir / "sarvey2insarmaps.job", slurm_commands, mbtiles_path, final_stem)
    #     return

    #run all steps sequentially
    run_command(cmd0)
    run_command(cmd1)
    if inps.do_geocorr:
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

    if not inps.skip_upload:
        run_command(cmd4)

    print("\nAll done!")
    ref_lat = metadata.get("REF_LAT", 26.1)
    ref_lon = metadata.get("REF_LON", -80.1)

    suffix = "_geocorr" if inps.do_geocorr else ""

    protocol = "https" if inps.insarmaps_host == "insarmaps.miami.edu" else "http"
    url = f"{protocol}://{inps.insarmaps_host}/start/{ref_lat:.4f}/{ref_lon:.4f}/11.0?flyToDatasetCenter=true&startDataset={final_stem}{suffix}"

    print(f"\nView on Insarmaps:\n{url}")

    webbrowser.open(url)

if __name__ == "__main__":
    main()