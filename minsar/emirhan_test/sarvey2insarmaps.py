#!/usr/bin/env python3
import argparse
import os
import subprocess
from pathlib import Path


def find_script(script_name, search_paths):
    for path in search_paths:
        full_path = Path(path) / script_name
        if full_path.exists():
            return str(full_path)
    raise FileNotFoundError(f"Could not find {script_name} in {search_paths}")


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
        
        f.write(f"cat >> insarmaps.log<<EOF\nhttps://insarmaps.miami.edu/start/26.1/-80.1/11.0?flyToDatasetCenter=true&startDataset={dataset_name}_geocorr\nEOF\n\n")
        f.write(f"cat >> insarmaps.log<<EOF\nhttps://149.165.153.50/start/26.1/-80.1/11.0?flyToDatasetCenter=true&startDataset={dataset_name}_geocorr\nEOF\n")
    print(f"\nJobfile created: {jobfile_path}")


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end pipeline for: SARvey shapefiles -> csv -> Geocorrected csv -> JSON -> MBTiles -> Insarmaps",
        epilog="""\
    Example:
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp --make-jobfile
      sarvey2insarmaps.py ./input/shp/p2_coh70_ts.shp --skip-upload
    """,
        formatter_class=argparse.RawTextHelpFormatter
    )    
    parser.add_argument("shapefile", help="Input shapefile path")
    parser.add_argument("--skip-upload", action="store_true", help="Skip upload to Insarmaps")
    parser.add_argument("--make-jobfile", action="store_true", help="Generate jobfile")
    parser.add_argument("--insarmaps-host", default="insarmaps.miami.edu")
    parser.add_argument("--insarmaps-user", default="insaradmin")
    parser.add_argument("--insarmaps-pass", default="insaradmin")
    parser.add_argument("--insarmaps-email", default="insarmaps@insarmaps.com")
    args = parser.parse_args()

    #use $RSMASINSAR_HOME as the root for now (temporarily)
    rsmasinsar_env = os.environ.get("RSMASINSAR_HOME")
    if not rsmasinsar_env:
        raise EnvironmentError("Environment variable RSMASINSAR_HOME is not set.")
    scripts_root = Path(rsmasinsar_env).resolve()

    #input/output paths
    shp_path = Path(args.shapefile).resolve()
    stem = shp_path.stem
    base_dir = shp_path.parent.parent.parent.resolve()  # go from input/shp/ -> a/

    outdir = base_dir / "output_csv"
    outdir.mkdir(parents=True, exist_ok=True)

    csv_path = outdir / f"{stem}.csv"
    geocorr_csv = outdir / f"{stem}_geocorr.csv"

    json_dir = base_dir / "JSON"
    json_dir.mkdir(parents=True, exist_ok=True)

    mbtiles_path = json_dir / f"{stem}_geocorr.mbtiles"

    #locate scripts
    search_dirs = [
        scripts_root / "minsar" / "emirhan_test",
        scripts_root / "tools",
        scripts_root / "tools" / "insarmaps_scripts",
    ]
    correct_geolocation = find_script("correct_geolocation.py", search_dirs)
    to_json = find_script("hdfeos5_or_csv_2json_mbtiles.py", search_dirs)
    to_insarmaps = find_script("json_mbtiles2insarmaps.py", search_dirs)

    #commands
    cmd1 = ["ogr2ogr", "-f", "CSV", "-lco", "GEOMETRY=AS_XY", "-t_srs", "EPSG:4326", str(csv_path), str(shp_path)]
    cmd2 = ["python3", correct_geolocation, str(csv_path), "--outfile", str(geocorr_csv)]
    cmd3 = ["hdfeos5_or_csv_2json_mbtiles.py", str(geocorr_csv), str(json_dir)]
    cmd4 = ["json_mbtiles2insarmaps.py", "--num-workers", "3", "-u", args.insarmaps_user, "-p", args.insarmaps_pass,
            "--host", args.insarmaps_host, "-P", "insarmaps", "-U", args.insarmaps_email,
            "--json_folder", str(json_dir), "--mbtiles_file", str(mbtiles_path)]

    if args.make_jobfile:
        slurm_commands = [
	    f"{' '.join(cmd1)}",
    	    f"{' '.join(cmd2)}",
            f"rm -rf {json_dir}",
            f"{' '.join(cmd3)}",
            f"{' '.join(cmd4)} &",
            f"{' '.join(cmd4).replace(args.insarmaps_host, '149.165.153.50')} &"
        ]
        create_jobfile(base_dir / "sarvey2insarmaps.job", slurm_commands, mbtiles_path, stem)
        return

    #run all steps sequentially
    run_command(cmd1)
    run_command(cmd2)
    run_command(cmd3)
    if not args.skip_upload:
        run_command(cmd4)

    print("\nAll done!")
    print(f"\nView on Insarmaps: https://{args.insarmaps_host}/start/26.1/-80.1/11.0?flyToDatasetCenter=true&startDataset={stem}_geocorr")


if __name__ == "__main__":
    main()
