#!/usr/bin/env python3

import os
import sys
import folium
from shapely import wkt
import webbrowser

def print_help():
    print("""
Usage:
  display_bbox.py LATMIN:LATMAX,LONMIN:LONMAX
  display_bbox.py 'POLYGON((lon1 lat1, lon2 lat2, ..., lon1 lat1))'

Examples:
  display_bbox.py 25.937:25.958,-80.126:-80.114
  display_bbox.py 'POLYGON((-82.04 26.53, -81.92 26.53, -81.92 26.61, -82.04 26.61, -82.04 26.53))'

Note:
  If you are using a POLYGON, you **must** wrap it in single quotes to prevent a shell syntax error.
""")

def draw_rectangle(subset):
    lat_part, lon_part = subset.split(',')
    lat_min, lat_max = map(float, lat_part.split(':'))
    lon_min, lon_max = map(float, lon_part.split(':'))
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
    folium.Rectangle(
        bounds=[[lat_min, lon_min], [lat_max, lon_max]],
        color='blue', fill=True, fill_opacity=0.3
    ).add_to(m)
    return m

def draw_polygon(wkt_string):
    shape = wkt.loads(wkt_string)
    coords = list(shape.exterior.coords)
    latlon = [[lat, lon] for lon, lat in coords]

    avg_lat = sum(p[0] for p in latlon) / len(latlon)
    avg_lon = sum(p[1] for p in latlon) / len(latlon)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=14)
    folium.Polygon(
        locations=latlon,
        color='green', fill=True, fill_opacity=0.3
    ).add_to(m)
    return m

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        print_help()
        sys.exit(0)

    # Detect common unquoted polygon misuse
    if len(sys.argv) > 2 and sys.argv[1].startswith("POLYGON"):
        print("[ERROR] It looks like you're using a POLYGON without quotes.")
        print("Please wrap the POLYGON string in single quotes like this:\n")
        print("  ./display_bbox.py 'POLYGON((...))'\n")
        sys.exit(1)

    arg = " ".join(sys.argv[1:])  # Join all arguments back into one string

    try:
        if arg.lower().startswith("polygon"):
            m = draw_polygon(arg)
        else:
            m = draw_rectangle(arg)
    except Exception as e:
        print(f"[ERROR] Failed to parse input: {e}")
        print_help()
        sys.exit(1)

    output_file = "bbox_map.html"
    m.save(output_file)
    print(f"[INFO] Map saved to {output_file}")
    print(f"[INFO] Open it with:\nopen -a Safari {output_file}\n")

    url = f"file:///{os.getcwd()}/{output_file}"
    webbrowser.open(url)

if __name__ == "__main__":
    main()
