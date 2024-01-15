#!/usr/bin/env python3
# Authors: Farzaneh Aziz Zanjani & Falk Amelung
# This script plots velocity, DEM error, and estimated elevation on the backscatter.
############################################################
import argparse
import os
import sys
import re
from minsar.objects import message_rsmas

'''
PLOT REPO TODO:
    Subparser for editing style/format parameters
        o fig size
        o font size
        o point size
        o color map
    either as subparser or create parser that handles argparse.ArugmentParser
'''
EXAMPLE = """example:
            
            view_persistent_scatterers.py velocity.h5 demErr.h5 inputs/geometryRadar.h5 velocity --mask ../maskPS.h5 --slcStack ../inputs/slcStack.h5 --subset-lalo 25.875:25.8795,-80.123:-80.1205
            view_persistent_scatterers.py velocity.h5 demErr.h5 inputs/geometryRadar.h5 all  --subset-lalo 25.875:25.8795,-80.123:-80.1205
            view_persistent_scatterers.py velocity.h5 demErr.h5 inputs/geometryRadar.h5 velocity  --subset-lalo 25.875:25.8795,-80.123:-80.1205  -dl -60 60 -el -30 30 -esl -60 60
            view_persistent_scatterers.py velocity.h5 demErr.h5 inputs/geometryRadar.h5  all --subset-lalo 25.875:25.8795,-80.123:-80.1205  --gtif Miami.tif --geo
            view_persistent_scatterers.py velocity.h5 demErr.h5 inputs/geometryRadar.h5  velocity --subset-lalo 25.875:25.8795,-80.123:-80.1205 --geo

            view_persistent_scatterers.py velocity.h5 --mask ../maskPS.h5 --subset-lalo 25.8755:25.879,-80.1226:-80.1205
            """
DESCRIPTION = (
    "Plots velocity, DEM error, and estimated elevation on the backscatter."
)

def create_parser():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EXAMPLE,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'data_file', nargs='*', help='Data file to be plotted (e.g. velocity.h5, demErr.h5).\n'
    )
    parser.add_argument(
        "--background", dest='background', type=str, 
        choices=['open_street_map','backscatter', 'satellite','geotif'], default="open_street_map", 
        help='Background image (default: open_street_map).'
    )
    parser.add_argument(
        "--subset-lalo", type=str, required=True,
        help="Latitude and longitude box in format 'lat1:lat2,lon1:lon2'"
    )
    parser.add_argument(
        "--mask", metavar='FILE', type=str, default=None,  
        help="PS mask file",
    )
    parser.add_argument(
        "--geometry-file", metavar="", type=str, default='inputs/geometryRadar.h5', nargs='?', 
        help="Geolocation file",
    )
    parser.add_argument(
        "--ref-lalo", nargs=2,  metavar=('LAT', 'LON'), type=float, help="reference point"
    )
    parser.add_argument(
        "--dem-offset", metavar="", type=float, default=26,
        help="DEM offset (geoid deviation) (default: 26 m for Miami)"
    )
    parser.add_argument(
        "--dem-error", dest="estimated_elevation", action='store_false',
        help="Plot dem-error instead of estimated elevation (default: False)"
    )

    parser.add_argument(
        "--vlim", nargs=2, metavar=("VMIN", "VMAX"), default=None,
        type=float, help="Velocity limit for the colorbar. Default: None",
    )
    parser.add_argument(
        "--colormap", "-c", metavar="", type=str, default="jet",
        help="Colormap used for display, e.g., jet",
    )
    parser.add_argument(
        "--point-size", metavar="", default=50, type=float,
        help="Points size",
    )
    parser.add_argument(
        "--fontsize", "-f", metavar="", type=float, default=10,
        help="Font size",
    )
    parser.add_argument(
        "--figsize", metavar=("WID", "LEN"), type=float, nargs=2,
        default=(5,10), help="Width and length of the figure"
    )
    parser.add_argument(
        "--flip-lr", dest="flip_lr",  action='store_true', default=False, 
        help="Flip the figure Left-Right (Default: False)." 
    )
    parser.add_argument("--flip-ud", dest="flip_ud",  action='store_true', default=False, 
                        help="Flip the figure Up-Down (Default: False)."
    )
    parser.add_argument('-o', '--outfile', type=str,  default=None,
                    help="filename to save figure (default=scatter.png).")
    parser.add_argument('--save', dest='save_fig', action='store_true',
                    help='save the figure')
    parser.add_argument('--nodisplay', dest='disp_fig', action='store_false',
                    help='save and do not display the figure')
    parser.add_argument('--dpi', dest='fig_dpi', metavar='DPI', type=int, default=300,
                    help='DPI - dot per inch - for display/write (default: %(default)s).')
    parser.add_argument('--nowhitespace', dest='disp_whitespace',
                    action='store_false', help='do not display white space')

    inps = parser.parse_args()

    # check: coupled option behaviors
    if not inps.disp_fig or inps.outfile:
        inps.save_fig = True
    if not inps.outfile:
        inps.outfile = 'scatter.png'
    return inps

def main():
    inps = cmd_line_parser()
    update_input_namespace(inps)

    fig, ax = configure_plot_settings(inps)

    # Adding background image
    if inps.background == 'open_street_map':
        add_open_street_map_image(ax, inps.coords)
    elif inps.background == 'backscatter':
        add_backscatter_image(ax, inps.amplitude)
    elif inps.background == 'satellite':
        add_satellite_image(ax)
    elif inps.background == 'geotif':
        add_geotif_image(ax, inps.geotif, inps.coords)
    else:
        raise Exception("USER ERROR: background option not supported:", inps.background )
        
    plot_scatter(ax=ax, inps=inps)

    # save figure
    if inps.save_fig:
        print(f'save figure to {inps.outfile} with dpi={inps.fig_dpi}')
        if not inps.disp_whitespace:
            fig.savefig(inps.outfile, transparent=True, dpi=inps.fig_dpi, pad_inches=0.0)
        else:
            fig.savefig(inps.outfile, transparent=True, dpi=inps.fig_dpi, bbox_inches='tight')
    
    plt.show()

###################################################################################
def main(iargs=None):
    if len(sys.argv) == 1:
        cmd = EXAMPLE.splitlines()[-2]
        cmd = re.sub(' +', ' ', cmd) .rstrip()
        sys.argv = cmd.split()
        print('CLI arguments:', sys.argv)
    
    message_rsmas.log(os.getcwd(), os.path.basename(__file__) + ' ' + ' '.join(sys.argv[1:]))

    # parse
    inps = create_parser()

    # import  (first remove the cli directory from sys.path)
    sys.path.pop(0)
    from minsar.persistent_scatterers import persistent_scatterers

    # run
    persistent_scatterers(inps)

   ################################################################################
if __name__ == '__main__':
    main()
