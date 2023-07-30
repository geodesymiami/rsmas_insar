#!/usr/bin/env python3
"""Plot GPS data"""
import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from mintpy.utils import arg_utils

GPS_COMPONENTS = ['__east(m)', '_north(m)', '____up(m)']


def create_parser(subparsers=None):
    """Create command line parser for plotting GPS data."""
    synopsis = 'Plot GPS data'
    epilog = 'Written by almost M.Sc. Amelung for some Zweibelmetbrotchen'
    name = __name__.split('.')[-1]

    parser = arg_utils.create_argument_parser(
        name, synopsis=synopsis, description=synopsis, epilog=epilog, subparsers=subparsers)

    # required arguments
    parser.add_argument('sites', nargs='+', type=str,
                        help='File or Filestem to display. Example: PAT3 or PAT3.tenv3')
    parser.add_argument('-nd', '--no-display', action='store_true',
                        help='Save figure instead of display')
    parser.add_argument('-s', '--start-date', type=str,
                        help='Start date for plot')
    parser.add_argument('-e', '--end-date', type=str, help='End date for plot')
    parser.add_argument('-sl', '--start-vline', type=str,
                        help='Start date for veritcal lines')
    parser.add_argument('-el', '--end-vline', type=str,
                        help='End date for vertical lines')
    parser.add_argument('-ms', '--marker-size-factor', type=int,
                        help='Scale marker size by this factor, default is based on number of points (between 1 and 20))')
# scale marker size
# scale figure size

    return parser


def cmd_line_parse(iargs=None):
    """Parse inputs."""

    parser = create_parser()
    inps = parser.parse_args(args=iargs)

    # save argv (to check the manually specified arguments)
    # use iargs        for python call
    # use sys.argv[1:] for command line call
    inps.argv = iargs if iargs else sys.argv[1:]

    for i, site in enumerate(inps.sites):
        site = Path(site).resolve()
        if not site.exists():
            raise FileNotFoundError(f'{site} NOT exist!')
        inps.sites[i] = site

    for key in ['start_date', 'end_date', 'start_vline', 'end_vline']:
        year = vars(inps)[key]
        setattr(inps, key, pd.to_datetime(year))

    return inps


def capitalize_first_letter(s):
    return f"{s[:1].upper()}{s[1:]}"


def get_marker_scale_factor(gps_df):
    """Get marker size based on number of points"""
    num_days = len(gps_df.index.day)
    if num_days < 365:
        return 20
    elif num_days < 365*2:
        return 10
    else:
        return 1


def plot_east_north_up(gps_df, site_name, inps, marker_size_factor=None):
    """Plot east, north, up components of a GPS timeseries."""

    fig, axes = plt.subplots(len(GPS_COMPONENTS), 1, figsize=(10, 6))
    fig.suptitle(f'{site_name} Displacement Timeseries')

    if marker_size_factor is None:
        marker_size_factor = get_marker_scale_factor(gps_df)

    for i in range(len(GPS_COMPONENTS)):

        data_mm = gps_df[GPS_COMPONENTS[i]] * 1000  # convert m to mm

        axes[i].scatter(gps_df.index, data_mm,
                        label=site_name, marker='o', s=1*marker_size_factor)

        y_label = capitalize_first_letter(
            GPS_COMPONENTS[i].strip('_')).replace('(m)', ' (mm)')
        axes[i].set_ylabel(y_label)

        # optionally add vertical lines
        if inps.start_vline or inps.end_vline:
            axes[i].axvline(x=inps.start_vline, linestyle='dashed',
                            color='red', alpha=0.2)
            axes[i].axvline(x=inps.end_vline, linestyle='dashed',
                            color='red', alpha=0.2)
            # optionally add shaded region based on vertical lines
            if inps.start_vline and inps.end_vline:
                axes[i].axvspan(inps.start_vline, inps.end_vline,
                                alpha=0.2, color='gray')


def main(iargs=None):
    inps = cmd_line_parse(iargs)

    for site in inps.sites:
        gps_df = pd.read_csv(site,  sep='\s+')
        gps_df.index = pd.to_datetime(gps_df['YYMMMDD'], format='%y%b%d')

        # optionally trim data to start and end dates
        if inps.start_date:
            gps_df = gps_df.loc[inps.start_date:]
        if inps.end_date:
            gps_df = gps_df.loc[:inps.end_date]

        site_name = capitalize_first_letter(site.stem)

        plot_east_north_up(gps_df=gps_df,
                           site_name=site_name,
                           inps=inps,
                           marker_size_factor=inps.marker_size_factor)
        if inps.no_display:
            save_path = (site.parent / 'images' / f'{site.stem}.png')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path)
        else:
            plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
