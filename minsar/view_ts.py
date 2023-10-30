#!/usr/bin/env python3
# Authors: Farzaneh Aziz Zanjani & Falk Amelung
# This script plots velocity and times series.
############################################################
import argparse
import os
import numpy as np
import glob
import h5py
import matplotlib.pyplot as plt
import georaster
import mintpy
from mintpy.utils import arg_utils
from mintpy.utils import readfile, utils as ut
import matplotlib as mpl
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from osgeo import gdal
from mintpy.utils import plot as pp
from mintpy.utils import readfile, utils as ut
import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from mintpy import view
from mintpy.objects import timeseries
from operator import itemgetter 
import datetime
from datetime import timedelta
from scipy import interpolate
import matplotlib.dates as mdates
from miaplpy.objects.invert_pixel import process_pixel 
from scipy import stats
from mpl_toolkits.axes_grid1 import make_axes_locatable
from miaplpy.dev import modified_dem_error
from miaplpy import correct_geolocation as corg
import matplotlib.ticker as mticker
import geopandas as gpd
import contextily as ctx
from shapely.geometry import box
import geopandas as gpd
from shapely.geometry import box
import matplotlib.cm as cm

EXAMPLE = """example:

For Gtiff background and timeseries of one point:

    view_ts.py 25.876047 -80.1222 timeseries.h5 velocity.h5 inputs/geometryRadar.h5 --lalo 25.877169 -80.121302 --subset-lalo 25.874:25.8795,-80.123:-80.1205  --point-size 40 --shift 4 --marker-size 5 --mask ../maskPS.h5

For Openstreetmap background and list of points:

    view_ts.py 25.876047 -80.1222 timeseries.h5 velocity.h5 inputs/geometryRadar.h5 --lalo-file list --subset-lalo 25.874:25.8795,-80.123:-80.1205 --point-size 40 --shift 4 --marker-size 5 --mask ../maskPS.h5

To show displacement instead of velocity:

    view_ts.py 25.876047 -80.1222 timeseries.h5 velocity.h5 inputs/geometryRadar.h5 --lalo-file list --subset-lalo 25.874:25.8795,-80.123:-80.1205 --point-size 40 --shift 4 --marker-size 5 --mask ../maskPS.h5 --disp --dates-to-average 3

"""

def cmd_line_parser():
    """
    Parse command line arguments and return the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
    """

    description = (
        "Plots velocity, DEM error, and estimated elevation on the backscatter."
    )
    epilog = EXAMPLE
    parser = arg_utils.create_argument_parser(
        name=__name__.split(".")[-1],
        synopsis=description,
        description=description,
        epilog=epilog,
        subparsers=None,
    )

    parser.add_argument(
        "--subset-lalo",
        type=str,
        required=True,
        help="Latitude and longitude box in format 'lat1:lat2,lon1:lon2'",
     )

    parser.add_argument(
        "ref",
        nargs=2,
        metavar="",
        type=float,
        help="reference point",
    )

    parser.add_argument(
        "--outfile",
        "-o",
        metavar="",
        type=str,
        default="timeseries.png",
        help="Output PNG file name",
    )

    parser.add_argument(
        "timeseries",
        metavar="",
        type=str,
        help="timeseries file",
    )

    parser.add_argument(
        "velocity",
        metavar="",
        type=str,
        help="Velocity file",
    )

    parser.add_argument(
        "geometry",
        metavar="",
        type=str,
        help="Geolocation file",
    )
    parser.add_argument(
        "--mask",
        type=str,
        metavar="",
#        default="../maskPS.h5",
        help="Mask PS file",
    )

    parser.add_argument(
        "--dates-to-average",
        metavar="",
        default=1,
        type=int,
        help="number of dates to average at the beginning and at end of the time series. Default is 1, meaning no average",
    )

    parser.add_argument(
        "--gtiff",
        type=str,
        metavar="",
        default="./dsm_reprojected_wgs84.tif",
        help="Path to Lidar elevation file",
    )

    parser.add_argument(
        "--vlim",
        nargs=2,
        metavar=("VMIN", "VMAX"),
        default=(-0.6, 0.6),
        type=float,
        help="Velocity limit for the colorbar. Default is -0.6 0.6",
    )

    parser.add_argument(
        "--dlim",
        nargs=2,
        metavar=("DMIN", "DMAX"),
        default=(-0.5, 0.5),
        type=float,
        help="Displacement limit for the colorbar. Default is -0.6 0.6",
    )


    parser.add_argument(
        "--colormap",
        "-c",
        metavar="",
        type=str,
        default="jet",
        help="Colormap used for display, e.g., jet",
    )
    parser.add_argument(
        "--point-size",
        dest="point_size",
        metavar="",
        default=10,
        type=float,
        help="Points size, Default is 10",
    )

    parser.add_argument(
        "--marker-size",
        dest="marker_size",
        metavar="",
        default=10,
        type=float,
        help="Points size. Default is 10",
    )

    parser.add_argument(
        "--fontsize",
        "-f",
        metavar="",
        type=float,
        default=10,
        help="Font size",
    )
    parser.add_argument(
        "--figsize",
        metavar=("WID", "LEN"),
        help="Width and length of the figure. Default is 10 and 5",
        type=float,
        nargs=2,
    )

    parser.add_argument(
        "--shift",
        metavar="",
        help="Shifting plotted timeseries",
        type=float,
        nargs=1,
    )

    parser.add_argument(
        "--lalo",
        type=float,
        nargs=2,
        metavar=("LAT", "LON"),
        help="Single point as LAT LON",
    )

    parser.add_argument(
        "--lalo-file",
        type=str,
        metavar="FILE",
        help="File containing points (each line as LAT LON)",
    )

    parser.add_argument(
        "--no-crosses",
        dest="no_crosses",
        default="False",
        help=" If True, does not shows the reference point and points on the map",
    )

    parser.add_argument(
        "--no-labels",
        dest="no_labels",
        default="False",
        help=" If True, does not shows labels for  points and timeseries using numbers",
    )

    parser.add_argument(
        "--disp",
        dest="disp",
        action="store_true", 
        help="Define if plotting in Geo coordinate or Radar coordinate",
    )

    args = parser.parse_args()

    return args

def get_data_ts(points, lat1, lat2, lon1, lon2, refy, refx):

    args = cmd_line_parser()
    vl = args.vlim[0]
    vh = args.vlim[1]
    vel_file = args.velocity
    geo_file = args.geometry
    mask_file_ps = args.mask
    outfile = args.outfile
    ts_file = args.timeseries
    num = args.dates_to_average

    velocity = readfile.read(vel_file, datasetName='velocity')[0]*1000
    latitude = readfile.read(geo_file, datasetName='latitude')[0]
    longitude = readfile.read(geo_file, datasetName='longitude')[0]


    stack_obj = timeseries(ts_file)
    stack_obj.open(print_msg=False)
    date_list = stack_obj.get_date_list()
    num_dates = len(date_list)
    time, atr = readfile.read(ts_file, datasetName='timeseries')

    if num != 1:
        displacement = np.empty_like(velocity)
        for i in range(time.shape[1]):
            for j in range(time.shape[2]):
                first_values = time[:num,i,j].mean(axis=0)
                last_values = time[-num:,i,j].mean(axis=0)
                displacement[i,j] = last_values - first_values         
    else:
        displacement = time[-1] - time[0]


 

    mask = np.ones(velocity.shape, dtype=np.int8)
    mask[latitude<lat1] = 0
    mask[latitude>lat2] = 0
    mask[longitude<lon1] = 0
    mask[longitude>lon2] = 0

    if args.mask is not None:
        mask_file = args.mask
        mask_p = readfile.read(mask_file, datasetName='mask')[0]
        mask *= mask_p  # Apply mask_p within the specified ymin, ymax, xmin, xmax

    vel = np.array(velocity[mask==1])
    lat = np.array(latitude[mask==1])
    lon = np.array(longitude[mask==1])
    disp= np.array(displacement[mask==1])

    ts = np.zeros([len(lat), num_dates])

    ts_p = np.zeros([points.shape[0], num_dates])
    ts_std = np.zeros([points.shape[0], num_dates])

    for i, point in enumerate(points):
        dates_ts, ts_p[i,:], ts_std[i,:] = ut.read_timeseries_lalo(points[i, 0], points[i, 1], ts_file,
                                                                      lookup_file=geo_file, ref_lat=refy, ref_lon=refx,
                                                                       win_size=2, unit='cm', print_msg=True)
    return lon, lat, vel, disp, dates_ts, ts, ts_p, ts_std

def plot_subset_geo(lon1, lon2, lat1, lat2, ymin, ymax, xmin, xmax, v_min, v_max, points):

    lon, lat, vel, disp, dates_ts, ts, ts_p, ts_std = get_data_ts(points, lat1, lat2, lon1, lon2, refy, refx)
    print(vel.shape, disp.shape)
   
    args = cmd_line_parser()
    gtiff = args.gtiff

    if args.disp:
       vl = args.dlim[0]
       vh = args.dlim[1]
    else:
       vl = args.vlim[0]
       vh = args.vlim[1]

    size=args.point_size
    marksize=args.marker_size

    if args.shift is not None:
        shift = args.shift
    else:
        shift = 3

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=args.figsize or (10, 5))

    def plot_scatter(ax, data, cmap, c_label, clim=None, marker='o', colorbar=True):
        im = ax.scatter(lon, lat, c=data, s=size, cmap=cmap, marker=marker)
        if colorbar:
            cbar = plt.colorbar(im, ax=ax, shrink=0.4, orientation='horizontal', pad=0.1)
            cbar.set_label(c_label)
            if clim is not None:
                im.set_clim(clim[0], clim[1])
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)

    if os.path.isfile(gtiff):
        cmap = 'Greys_r'
        clim_raster = (-100, 100)
    else:
        cmap = args.colormap
        clim_raster = None

    if os.path.isfile(gtiff):
        my_image = georaster.MultiBandRaster(gtiff, bands='all', load_data=(lon1, lon2, lat1, lat2), latlon=True)
        ax.imshow(my_image.r, extent=my_image.extent, cmap=cmap, vmin=clim_raster[0], vmax=clim_raster[1])
    else:
        geometry = [box(lon1, lat1, lon2, lat2)]
        gdf = gpd.GeoDataFrame({'geometry': geometry}, crs='EPSG:4326')
        gdf.plot(ax=ax, facecolor="none", edgecolor='none')
        ctx.add_basemap(ax, crs=gdf.crs, source=ctx.providers.OpenStreetMap.Mapnik)
        ax.set_xlim(lon1, lon2)
        ax.set_ylim(lat1, lat2)
        ax.set_axis_off()

    ref_lon, ref_lat = refx, refy

    if args.disp:
        plot_scatter(ax, disp*100, args.colormap,'displacement (cm)', (vl, vh))
    else:
        plot_scatter(ax, vel/10, args.colormap,'velocity (cm/yr)', (vl, vh))

    if args.no_crosses == "False":
        ax.scatter(ref_lon, ref_lat, c='black', marker='s')
    if args.no_crosses and args.no_labels == "False":
        for i, point in enumerate(points):
            ax.scatter(points[i, 1], points[i, 0], c='red', marker='x', s=30, label=f'{i}')
            ax.text(points[i, 1], points[i, 0], str(i+1), fontsize=12, color='black', ha='center', va='bottom')

    fig, axs = plt.subplots(nrows=1, ncols=1, figsize=args.figsize or (10, 5))
    plt.xlabel('Date')
    plt.ylabel('Displacement (cm)')
    num_time_series = len(points)
    colormap = plt.get_cmap('Dark2')
    color_levels = np.linspace(0, 1, num_time_series)
 
  
    for i, point in enumerate(points):
        color = colormap(color_levels[i])  # Assign a color from the colormap
        if i == 0:
            axs.plot(dates_ts[4::], ts_p[i, 4::]-ts_p[i, 4], '.', color=color, markeredgecolor='black', markeredgewidth=0.4 ,markersize=marksize)
            x_label, y_label = dates_ts[4], ts_p[i, 4]
        else:
            shift = np.multiply(args.shift, i)
            axs.plot(dates_ts[4::], ts_p[i, 4::]-ts_p[i, 4] - shift  , '.', color=color, markeredgecolor='black', markeredgewidth=0.4, markersize=marksize)
            x_label, y_label = dates_ts[4], ts_p[i, 4] - shift

        if args.no_labels == "False":
            label_text = f'{i+1}'
            axs.text(x_label, y_label, label_text, fontsize=10, color='black', va='bottom', ha='right', rotation=0)
 
#    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(0, num_time_series-1)), ax=axs)
#    cbar.set_ticks(range(num_time_series))
#    cbar.set_ticklabels(range(num_time_series))
#    cbar.set_label('Time Series Index')  # Set colorbar label

if __name__ == "__main__":
    args = cmd_line_parser()
    if args.lalo:
        # Single point provided as command-line arguments
        points = [tuple(args.lalo)]
    elif args.lalo_file:
        # Points provided in a file
        with open(args.lalo_file, 'r') as file:
            lines = file.readlines()
            points = [tuple(map(float, line.strip().split())) for line in lines]
    else:
        print("Error: You must provide either --lalo or --lalo-file.")
        points = []
    
    points = np.array(points).reshape(-1, 2)


    lat1, lat2, lon1, lon2 = [float(val) for val in args.subset_lalo.replace(':', ',').split(',')]
    mask = args.mask
    vel_file = args.velocity
    geo_file = args.geometry
    refx = args.ref[1]
    refy = args.ref[0]

    if args.disp:
       vl = args.dlim[0]
       vh = args.dlim[1]
    else:
       vl = args.vlim[0]
       vh = args.vlim[1]
 
    outfile = args.outfile
    size = args.point_size

    points_lalo = np.array([[lat1, lon1],
                            [lat2, lon2]])
    attr = readfile.read_attribute(vel_file)
    coord = ut.coordinate(attr, geo_file)
    yg1, xg1 = coord.geo2radar(points_lalo[0][0], points_lalo[0][1])[:2]
    yg2, xg2 = coord.geo2radar(points_lalo[1][0], points_lalo[1][1])[:2]
    yg3, xg3 = coord.geo2radar(points_lalo[0][0], points_lalo[1][1])[:2]
    yg4, xg4 = coord.geo2radar(points_lalo[1][0], points_lalo[1][1])[:2]
    print("Lat, Lon, y, x: ", points_lalo[0][0], points_lalo[0][1], yg1, xg1)
    print("Lat, Lon, y, x: ", points_lalo[1][0], points_lalo[1][1], yg2, xg2)
    print("Lat, Lon, y, x: ", points_lalo[0][0], points_lalo[1][1], yg3, xg3)
    print("Lat, Lon, y, x: ", points_lalo[1][0], points_lalo[1][1], yg4, xg4)
    ymin = min(yg1, yg2, yg3, yg4)
    ymax = max(yg1, yg2, yg3, yg4)
    xmin = min(xg1, xg2, xg3, xg4)
    xmax = max(xg1, xg2, xg3, xg4)
    print(ymin, xmin, ymax, xmax)

    plot_subset_geo(lon1=lon1, lon2=lon2, lat1=lat1, lat2=lat2, ymin=ymin, ymax=ymax, xmin=xmin, xmax=xmax, v_min=vl, v_max=vh, points=points)
    plt.show()

