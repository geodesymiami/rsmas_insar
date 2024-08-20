#!/usr/bin/env python3

import argparse
import sys

def parse_coordinates(coord_str):
    try:
        if ':' in coord_str and ',' in coord_str:
            south, north = map(float, coord_str.split(',')[0].split(':'))
            west, east = map(float, coord_str.split(',')[1].split(':'))
        else:
            south, north, west, east = map(float, coord_str.split())
        return south, north, west, east
    except ValueError:
        print("Error: Invalid coordinate format.")
        sys.exit(1)

def create_kml(south, north, west, east, output_file):
    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Bounding Box</name>
    <Style id="whiteOutline">
      <LineStyle>
        <color>ffffffff</color>
        <width>2</width>
      </LineStyle>
      <PolyStyle>
        <color>00ffffff</color>
      </PolyStyle>
    </Style>
    <Placemark>
      <name>Area of Interest</name>
      <styleUrl>#whiteOutline</styleUrl>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              {west},{south},0
              {east},{south},0
              {east},{north},0
              {west},{north},0
              {west},{south},0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>
"""
    with open(output_file, 'w') as file:
        file.write(kml_content)
    print(f"KML file created: {output_file}")

def main():

    EXAMPLE="""examples:
      bbox2kml.py -8.0 -7.3 121.0 126.0
      bbox2kml.py -- -8.0:-7.3,121.0:126.0
    """
    parser = argparse.ArgumentParser( description="Create a KML file from bounding box coordinates.", formatter_class=argparse.RawTextHelpFormatter, epilog=EXAMPLE)
    parser.add_argument("coordinates", nargs='+', help="Bounding box coordinates in the form 'South North West East' or 'South:North,West:East'")
    parser.add_argument("-o", "--outfile", default="bbox.kml", help="Output KML file name (default: bbox.kml)")
    args = parser.parse_args()

    if len(args.coordinates) == 1:
        south, north, west, east = parse_coordinates(args.coordinates[0])
    elif len(args.coordinates) == 4:
        south, north, west, east = map(float, args.coordinates)
    else:
        print("Error: Invalid number of coordinates.")
        sys.exit(1)

    create_kml(south, north, west, east, args.outfile)

if __name__ == "__main__":
    main()
