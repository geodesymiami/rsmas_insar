# Author: Emirhan Pehlivanli

import os
import argparse
import sys
import pandas as pd
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import Transformer

DESCRIPTION = (
    "Add LIDAR elevation statistics to a CSV of geocorrected InSAR points."
)

EXAMPLE = """\
Reads X_geocorr and Y_geocorr columns (in degrees) and queries the LIDAR DEM at each point.
Computes the mean and variance of elevation within a given search radius (default 5 meters).

Adds the following columns:
  - lidar_dem_mean
  - lidar_dem_var

Examples:
  # Use default radius (5 meters):
  add_lidar_elevation.py MiamiSenA28_MDCBeaches_20191001_20231031.csv --dem DEM/MiamiBeach.tif

  # Use custom radius (10 meters):
  add_lidar_elevation.py MiamiSenA28_MDCBeaches_20191001_20231031.csv --dem DEM/MiamiBeach.tif --radius 10
"""
def parse_arguments():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EXAMPLE,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("csv_file", help="Input CSV")
    parser.add_argument("--dem", required=True, help="Path to LIDAR DEM GeoTIFF")
    parser.add_argument("--radius", type=float, default=5.0, help="Search radius in meters (default: 5)")
    return parser.parse_args()

def reproject_dem_to_utm(dem_path, output_path):
    with rasterio.open(dem_path) as src:
        dst_crs = "EPSG:32617"  # UTM Zone 17N for Miami
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )

        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(output_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear
                )

    print(f"DEM reprojected to UTM and saved to: {output_path}")

def compute_lidar_stats(df, utm_dem_path, radius_m):
    with rasterio.open(utm_dem_path) as src:
        dem_array = src.read(1)
        transform = src.transform
        pixel_size = transform.a  # Assumes square pixels

        radius_pixels = int(radius_m / pixel_size)

        means = []
        vars_ = []

        for x, y in zip(df["x_utm"], df["y_utm"]):
            col, row = ~transform * (x, y)
            col, row = int(round(col)), int(round(row))

            row_start = max(0, row - radius_pixels)
            row_end   = min(src.height, row + radius_pixels + 1)
            col_start = max(0, col - radius_pixels)
            col_end   = min(src.width, col + radius_pixels + 1)

            window = dem_array[row_start:row_end, col_start:col_end]
            valid = window[np.isfinite(window)]  # remove NaNs

            if valid.size == 0:
                means.append(np.nan)
                vars_.append(np.nan)
            else:
                means.append(np.mean(valid))
                vars_.append(np.var(valid))

    df["lidar_dem_mean"] = means
    df["lidar_dem_var"] = vars_
    return df

def reproject_points_to_utm(df):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32617", always_xy=True)
    x_utm, y_utm = transformer.transform(df["X_geocorr"].values, df["Y_geocorr"].values)
    df["x_utm"] = x_utm
    df["y_utm"] = y_utm
    return df

def main():
    args = parse_arguments()

    #read csv
    try:
        df = pd.read_csv(args.csv_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    #required columns
    required_cols = {"X_geocorr", "Y_geocorr"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"Missing required columns in CSV: {missing}")
        sys.exit(1)

    print("CSV loaded and all required columns found.")
    print(f"DEM path: {args.dem}")
    print(f"Radius: {args.radius} meters")

    #reproject dem
    utm_dem_path = args.dem.replace(".tif", "_utm.tif")
    reproject_dem_to_utm(args.dem, utm_dem_path)

    #reproject csv coordinates to UTM
    df = reproject_points_to_utm(df)
    print("CSV coordinates reprojected to UTM.")

    #compute mean/var from UTM dem
    df = compute_lidar_stats(df, utm_dem_path, args.radius)
    print("LIDAR elevation stats computed.")

    #insert lidar_dem_mean and lidar_dem_var before 'velocity' column if it exists
    if "velocity" in df.columns:
        point_id_index = df.columns.get_loc("velocity")
        for col_name in ["lidar_dem_mean", "lidar_dem_var"]:
            col_data = df.pop(col_name)
            df.insert(point_id_index, col_name, col_data)
    else:
        print("'velocity' column not found, appending new columns at the end.")

    #save output csv
    output_csv = args.csv_file.replace(".csv", "_with_lidar.csv")
    df.to_csv(output_csv, index=False)
    print(f"Output saved to: {output_csv}")

if __name__ == "__main__":
    main()