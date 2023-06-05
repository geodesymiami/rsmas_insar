#!/usr/bin/env python3
# Authors: Farzaneh Aziz Zanjani & Falk Amelung              
# This script plots velocity, DEM error, and estimated elevation on the backscatter.
############################################################
import argparse
import os
import numpy as np
import glob
import matplotlib.pyplot as plt
import matplotlib
import mintpy
from osgeo import gdal
from mintpy.utils import plot as pp
from mintpy.utils import readfile, utils as ut 
import h5py
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
from mintpy.utils import arg_utils
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

#####

EXAMPLE = """example:
            ./view_scatterplot.py velocity.h5 demErr.h5 geometryRadar.h maskTempCoh.h5 maskPS.h5 timeseries_demErr.h5 slcStack.h5 --subset_lalo 25.875  25.8795  -80.122  -80.121 

            ./view_scatterplot_dem.py velocity.h5 demErr.h5 geometryRadar.h maskTempCoh.h5 maskPS.h5 timeseries_demErr.h5 slcStack.h5 --subset_lalo 25.8384 25.909 -80.147 -80.1174 -el -50 50

            ./view_scatterplot.py velocity.h5 demErr.h5 geometryRadar.h maskTempCoh.h5 maskPS.h5 timeseries_demErr.h5 slcStack.h5 --subset_lalo 25.87525.8795-80.122-80.121 --timeseries ./timeseries_demErr.h5            
"""
####
def cmd_line_parser():
    # This fuction gets the inputs and parameters from command line
    synopsis = 'plots velocity, DEM error, and estimated elevation on the backscatter'
    epilog = EXAMPLE
    name = __name__.split('.')[-1]
    parser = arg_utils.create_argument_parser(name, synopsis=synopsis, description=synopsis, epilog=epilog, subparsers=None)
    parser.add_argument('--subset_lalo', nargs=4, default=(25.875, 25.8795, -80.122, -80.121), metavar='', type=float, help='latitude and longitude for the corners of the box')
    parser.add_argument('--outfile', '-o', metavar='', type=str, default='scatter_backscatter_dem.png', help='output png file name')
    parser.add_argument("velocity", metavar='', type=str, help = "Velocity file")
    parser.add_argument("dem_error", metavar='', type=str, help = "Dem error file")
    parser.add_argument("geometry", metavar='', type=str, help = "Geolocation file")
    parser.add_argument("masktemp", type=str, metavar='', help = "Temporal coherence mask file")
    parser.add_argument("PS", type=str, metavar='', help = "PS file")
    parser.add_argument("timeseries", metavar='', type=str, help = "Timeseries file")
    parser.add_argument("slcStack", metavar='', type=str, help = "slcstack file")
    parser.add_argument("--out_amplitude", metavar='', type=str, default="./mean_amplitude.npy", help = "file to write the amplitude from slcSack")
    parser.add_argument("--project_dir", metavar='', type=str, default="./", help = "path to the directory containing data files")
    parser.add_argument('--vlim', nargs=2, metavar=('VMIN','VMAX'), default=(-0.6, 0.6), type=float, help='velocity limit for the colorbar. Default is -0.6 0.6')
    parser.add_argument('--dem_lim', '-dl', nargs=2, metavar='', type=float, help='Dem limit for color bar e.g., 0 50')
    parser.add_argument('--dem_error_lim', '-el', nargs=2, metavar='', type=float, help='Dem error limit for color bar e.g., -5 20')
    parser.add_argument('--dem_estimated_lim', '-esl', nargs=2, metavar='', type=float, help='Estimated elevation limit for color bar e.g., 0 50')

    parser.add_argument('--colormap', '-c', metavar='', type=str, default="jet", help='colormap used for display e.g., jet')
    parser.add_argument('--point_size', metavar='', default=10, type=float, help='points size')
    parser.add_argument('--offset', metavar='', type=float, default=26, help='dem offset (geoid deviation) e.g., it is 26 for Miami')
    parser.add_argument('--fontsize', '-f', metavar='', type=float, default=10, help='font size')
    parser.add_argument("--figsize", metavar=('WID','LEN'), help="width and length of the figure", type=float, nargs= 2)

    parser.add_argument('--flip_lr', metavar='', type=str, default='NO', help='If YES, flips the figure Left-Right. Default is NO.')
    parser.add_argument('--flip_ud', metavar='', type=str, default='NO', help='If YES, flips the figure Up-Down. Default is NO.')

    args = parser.parse_args()

    return args

####

def calculate_mean_amplitude(slcStack, out_amplitude):
    with h5py.File(slcStack, 'r') as f:
        slcs = f['slc']
        s_shape = slcs.shape
        mean_amplitude = np.zeros((s_shape[1], s_shape[2]), dtype='float32')
        lines = np.arange(0, s_shape[1], 100)
        for t in lines:
            last = t + 100
            if t == lines[-1]:
                lst = s_shape[1]
            mean_amplitude[t:last, :] = np.mean(np.abs(f['slc'][:,t:last,:]), axis=0)
            np.save(out_amplitude, mean_amplitude)
    return


####
def get_data(ymin, ymax, xmin, xmax, ps, out_amplitude, shift=0):
 
    args=cmd_line_parser()
    project_dir=args.project_dir 
    vel_file=args.velocity
    demError_file=args.dem_error
    geo_file=args.geometry
    mask_file_t=args.masktemp
    mask_file_ps=args.PS
    tsStack=args.timeseries
    slcStack=args.slcStack
    

    velocity, atr = readfile.read(vel_file, datasetName='velocity') 

    if ymin >= ymax:
       tmp_ymin = ymin
       tmp_ymax = ymax
       ymin = tmp_ymax 
       ymax = tmp_ymin 
    if xmin >= xmax:
       tmp_xmin = xmin
       tmp_xmax = xmax
       xmin = tmp_xmax 
       xmax = tmp_xmin 

    # needed as for Tsx there is no ORBIT_DIRECTION attribute
    try:
        orbit_direction = atr['ORBIT_DIRECTION']
    except:
        result_list = []
        for x in ['TsxSMAT','TsxSLAT','TsxHSAT','CskAT']:
            result_list.append(x in project_dir )
        if any(result_list):
            orbit_direction = 'ASCENDING'
        for x in ['TsxSMDT','TsxSLDT','TsxHSDT','TsxSMD','CskDT']:
            result_list.append(x in project_dir )
        if any(result_list):
            orbit_direction = 'DESCENDING'

    if orbit_direction == 'ASCENDING':
        flipud_flag = True
        fliplr_flag = False
    if orbit_direction == 'DESCENDING':
        flipud_flag = False
        fliplr_flag = True
    # need to check in view.py how Yunjun is doing the flipping and whetehr it works for TSX (does he has the ORBIT_DIRECTION attribute?)
    if flipud_flag:
       DEM = np.flipud(readfile.read(geo_file, datasetName='height')[0][ymin:ymax, xmin:xmax]) + shift
       demError = np.flipud(readfile.read(demError_file, datasetName='dem')[0][ymin:ymax, xmin:xmax])
       amplitude = np.flipud(np.load(out_amplitude)[ymin:ymax, xmin:xmax]) 
       mask_t = np.flipud(readfile.read(mask_file_t, datasetName='mask')[0][ymin:ymax, xmin:xmax])
       mask_p = np.flipud(readfile.read(mask_file_ps, datasetName='mask')[0][ymin:ymax, xmin:xmax])
       if ps:
           mask = mask_p
       else:
           mask=mask_t
       velocity = np.flipud(velocity[ymin:ymax, xmin:xmax])
    if fliplr_flag:
       DEM = np.fliplr(readfile.read(geo_file, datasetName='height')[0][ymin:ymax, xmin:xmax]) + shift
       demError = np.fliplr(readfile.read(demError_file, datasetName='dem')[0][ymin:ymax, xmin:xmax])
       amplitude = np.fliplr(np.load(out_amplitude)[ymin:ymax, xmin:xmax]) 

       mask_t = np.fliplr(readfile.read(mask_file_t, datasetName='mask')[0][ymin:ymax, xmin:xmax])
       mask_p = np.fliplr(readfile.read(mask_file_ps, datasetName='mask')[0][ymin:ymax, xmin:xmax])
       if ps:
           mask = mask_p
       else:
           mask=mask_t
       velocity = np.fliplr(velocity[ymin:ymax, xmin:xmax])
  
    vel = velocity[mask==1]*1000
    demerr = demError[mask==1]
    dem = DEM[mask==1]
   # demerror_std = demError_std[mask==1]
    x = np.linspace(0, velocity.shape[1]-1, velocity.shape[1])
    y = np.linspace(0, velocity.shape[0]-1, velocity.shape[0])
    x, y = np.meshgrid(x, y)
    xv = x[mask==1]
    yv = y[mask==1]
   
    return amplitude, xv, yv, vel, demerr, dem, DEM, atr

####
def plot_subset(ymin, ymax, xmin, xmax, ps, v_min, v_max, amplitude_im, dem_offset, dem_name, out_name, size=200):

    amplitude, xv, yv, vel, demerr, dem, DEM, atr = get_data(ymin, ymax, xmin, xmax, ps, amplitude_im, dem_offset)
    
    args=cmd_line_parser()
    vl=args.vlim[0]
    vh=args.vlim[1]
    


    if args.figsize is not None:
       fs=(args.figsize[0],args.figsize[1])
    else:
       fs=(13, 4.5)
    fig, axs = plt.subplots(nrows=1, ncols=5,figsize=fs)

    ax = axs[0]
    ax.imshow(amplitude, cmap='gray', vmin=0, vmax=300)
    im = ax.scatter(xv, yv, c=vel/10, s=size, cmap=args.colormap, vmin=vl, vmax=vh);
    cbar = plt.colorbar(im, ax=ax, shrink=1, orientation='horizontal', pad=0.04)
    im.set_clim(vl, vh)

    cbar.set_label('velocity [cm/yr]')

    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    ax = axs[1]
    im=ax.imshow(amplitude, cmap='gray', vmin=0, vmax=300)
    cbar = plt.colorbar(im, ax=ax, shrink=1, orientation='horizontal', pad=0.04)
    cbar.set_label('Amplitude')
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    ax = axs[2]
    ax.imshow(amplitude, cmap='gray', vmin=0, vmax=300)
    im = ax.scatter(xv, yv, c=dem, s=size, cmap=args.colormap);
    cbar = plt.colorbar(im, ax=ax, shrink=1, orientation='horizontal', pad=0.04)
    cbar.set_label('SRTM DEM [m]')
    if args.dem_lim is not None:
       im.set_clim(args.dem_lim[0], args.dem_lim[1])

    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)


    ax = axs[3]
    ax.imshow(amplitude, cmap='gray', vmin=0, vmax=300)
    im = ax.scatter(xv, yv, c=-demerr, s=size, cmap=args.colormap);
    cbar = plt.colorbar(im, ax=ax, shrink=1, orientation='horizontal', pad=0.04)
    cbar.set_label('DEM Error [m]')
    if args.dem_error_lim is not None:
       im.set_clim(args.dem_error_lim[0], args.dem_error_lim[1])
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    ax = axs[4]
    ax.imshow(amplitude, cmap='gray', vmin=0, vmax=300)
    im = ax.scatter(xv, yv, c=-demerr+dem, s=size, cmap=args.colormap);
    cbar = plt.colorbar(im, ax=ax, shrink=1, orientation='horizontal', pad=0.04)
    cbar.set_label('Estimated \nelevation [m]')
    if args.dem_estimated_lim is not None:
       im.set_clim(args.dem_estimated_lim[0], args.dem_estimated_lim[1])
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    ax.axes.get_yaxis().set_visible(False)

    if ps:
        psds = 'ps'
    else:
        psds = 'ds'
    plt.savefig(out_name, bbox_inches='tight', dpi=300)

####
def main():

    args=cmd_line_parser()

    lat1=args.subset_lalo[0]
    lat2=args.subset_lalo[1]
    lon1=args.subset_lalo[2]
    lon2=args.subset_lalo[3]
    vl=args.vlim[0]
    vh=args.vlim[1]
    dem_offset=args.offset
    
    vel_file=args.velocity  
    demError_file=args.dem_error
    geo_file=args.geometry
    mask_file_t=args.masktemp
    mask_file_ps=args.PS
    tsStack=args.timeseries
    slcStack=args.slcStack
  
    outfile=args.outfile
    out_amplitude=args.out_amplitude
    project_dir=args.project_dir


    plt.rcParams["font.size"] = args.fontsize

    if args.flip_lr=='YES':
       print('flip figure left and right')
       plt.gca().invert_xaxis()
     
    if args.flip_ud=='YES':
       print('flip figure up and down')
       plt.gca().invert_yaxis()         

    if not os.path.exists(out_amplitude):
       calculate_mean_amplitude(slcStack, out_amplitude)
   
    points_lalo = np.array([[lat1, lon1],
                  [lat2, lon2]])

    attr = readfile.read_attribute(tsStack)
    coord = ut.coordinate(attr, geo_file)
    yg1, xg1 = coord.geo2radar(points_lalo[0][0], points_lalo[0][1])[0:2]
    yg2, xg2 = coord.geo2radar(points_lalo[1][0], points_lalo[1][1])[0:2]
    print (yg1, xg1, yg2, xg2)
    yg1, xg1 = coord.geo2radar(points_lalo[0][0], points_lalo[0][1])[0:2]
    yg2, xg2 = coord.geo2radar(points_lalo[0][0], points_lalo[1][1])[0:2]
    yg3, xg3 = coord.geo2radar(points_lalo[1][0], points_lalo[0][1])[0:2]
    yg4, xg4 = coord.geo2radar(points_lalo[1][0], points_lalo[1][1])[0:2]
    print("Lat, Lon, y, x: ",points_lalo[0][0], points_lalo[0][1], yg1, xg1)
    print("Lat, Lon, y, x: ",points_lalo[0][0], points_lalo[1][1], yg2, xg2)
    print("Lat, Lon, y, x: ",points_lalo[1][0], points_lalo[0][1], yg3, xg3)
    print("Lat, Lon, y, x: ",points_lalo[1][0], points_lalo[1][1], yg4, xg4)
    print (yg1, xg1, yg2, xg2, yg3, xg3, yg4, xg4)
    ymin = min(yg1, yg2, yg3, yg4)
    ymax = max(yg1, yg2, yg3, yg4)
    xmin = min(xg1, xg2, xg3, xg4)
    xmax = max(xg1, xg2, xg3, xg4)
    print (ymin, xmin, ymax, xmax)
    #import pdb; pdb.set_trace() 

    plot_subset(ymin=ymin, ymax=ymax, xmin=xmin, xmax=xmax, ps=True, v_min=vl, v_max=vh,
            amplitude_im=out_amplitude, dem_offset=dem_offset, dem_name='dem',
            out_name=outfile, size=args.point_size)
    plt.show()

if __name__ == '__main__':
    main()


