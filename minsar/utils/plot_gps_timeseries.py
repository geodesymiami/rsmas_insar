#!/usr/bin/env python3
"""Plot GPS data.

I'm sorry the structure of this code is shite.
Prof. Amelung told me to write it this way (daily and five-minute in one module)
and he isn't paying me enough (or at all) so no refactor."""
import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from mintpy.utils import arg_utils

GPS_COMPONENTS = ['__east(m)', '_north(m)', '____up(m)']

FIVE_MIN_GPS_COMPONENTS = ['___e-ref(m)', '___n-ref(m)', '___v-ref(m)']

EXAMPLE = """example:
    plot_gps_timeseries.py PAT3.tenv3
    plot_gps_timeseries.py PAT3.tenv3 SLPC.tenv3                                           # multiple file
    plot_gps_timeseries.py S*                                                              # multiple files
    plot_gps_timeseries.py *.tenv3                                                         # multiple files

    plot_gps_timeseries.py PAT3.tenv3 --start-date 20180115                                # start date
    plot_gps_timeseries.py PAT3.tenv3 --start-date 20180115 --end-date 20190115            # start and end date
    plot_gps_timeseries.py *.tenv3 --start-date 2020 --end-date Jan2022                    # flexible dates parsed into datetime object
    plot_gps_timeseries.py *.tenv3 --start-date 2018-01-01  --end-date 2018-01-01          # flexible dates parsed into datetime object

    plot_gps_timeseries.py *.tenv3 --start-vline 2018-01-01                                # vertical lines
    plot_gps_timeseries.py *.tenv3 --start-vline 2018-01-01 --end-vline 2019-01-01         # region between start and end veritcal lines will be shaded

    plot_gps_timeseries.py *.tenv3 --marker-size-factor 10                                 # override default marker size

    plot_gps_timeseries.py *.tenv3 --start-date 2020 --no-display                          # save figure instead of display (./images/*.png)

    plot_gps_timeseries.py *.tenv3 --five-minutes --dates 2020-01-01 2020-01-02           # download and plot 5 minute data with two plots at
                                                                                          # 2020-01-01 and 2020-01-02
    plot_gps_timeseries.py *.tenv3 --fm -d 2020-01-01 2020-01-02 -h 14                    # with vertical lines at 14
    plot_gps_timeseries.py *.tenv3 --fm -d 2020-01-01 2020-01-02 -h 14 -nd                # without displaying

    Written by almost M.Sc. Amelung for some Zweibelmett Brotchen.
    """


def create_parser(subparsers=None):
    """Create command line parser for plotting GPS data."""
    synopsis = 'Plot GPS data'

    name = __name__.split('.')[-1]

    parser = arg_utils.create_argument_parser(
        name, synopsis=synopsis, description=synopsis, epilog=EXAMPLE, subparsers=subparsers)

    # daily = parser.add_subparsers(title='data_source', dest='data_source')

    parser.add_argument('sites', nargs='+', type=str,
                        help='File or Filestem to display. Example: PAT3 or PAT3.tenv3')

    parser.add_argument('-nd', '--no-display', action='store_true',
                        help='Save figure instead of display')

    # for plotting daily data (from the *.tenv3 files)
    parser.add_argument('-s', '--start-date', type=str,
                        help='Start date for plot')
    parser.add_argument(
        '-e', '--end-date', type=str, help='End date for plot')

    parser.add_argument('-sl', '--start-vline', type=str,
                        help='Start date for veritcal lines')
    parser.add_argument('-el', '--end-vline', type=str,
                        help='End date for vertical lines')
    parser.add_argument('-ms', '--marker-size-factor', type=int,
                        help='Scale marker size by this factor, default is based on number of points (between 1 and 20))')

    # if 5 min is called, start date is the plotted date and end date is ignored
    # BUG: overloaded options will not work
    # move to separate parser or subparser
    parser.add_argument('-fm', '--five-minutes', action='store_true',
                        help='Get and plot 5 minute data')
    parser.add_argument('-d', '--dates', nargs='+',
                        type=str, help='End date for plot (5 min data only)')
    parser.add_argument('-hr', '--hours', nargs='+',
                        type=int, help='Hour (1-24) for plotting a vertical line (5 min data only)')
    # for plotting daily data (from the *.kenv files)

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
        site = Path(site).resolve().with_suffix('.tenv3')
        if not site.exists():
            raise FileNotFoundError(f'"{site} "NOT exist!')
        inps.sites[i] = site

    if inps.five_minutes:
        new_site_files = []
        for site in inps.sites:
            download_gps_data_five_minutes(inps, site)
            new_site_files.extend(get_files_five_minutes(inps, site))
        inps.sites = new_site_files

    return inps


def get_files_five_minutes(inps, site):
    new_site_files = []
    for date in inps.dates:
        date = pd.to_datetime(date)
        day = date.strftime('%j')
        site_path = Path(
            f'{site.stem}_five_min/{site.stem}.{date.year}.{day}.kenv')
        new_site_files.append(site_path)
    return new_site_files


def get_days_in_year(year):
    return (pd.Timestamp(year + 1, 1, 1) - pd.Timestamp(year, 1, 1)).days


def all_files_exist(file_paths):
    for path in file_paths:
        if not os.path.exists(path):
            return False
    return True


def download_gps_data_five_minutes(inps, site):
    """Download 5 minute GPS data from UNR website. Return list of unzipped files."""
    for date in inps.dates:
        date = pd.to_datetime(date)
        zipped_file_name = f'{site.stem}.{date.year}.kenv.zip'

        unzip_destination_folder = Path.cwd() / f'{site.stem}_five_min'
        days_in_year = get_days_in_year(date.year)
        expected_unziped_files = [
            (unzip_destination_folder
             / f'{site.stem}.{date.year}.{day:03d}.kenv') for day in range(1, days_in_year+1, 1)]

        if all_files_exist(expected_unziped_files):
            print(f'Already downloaded "{date.year}"')
            return
        zipped_file_path = (unzip_destination_folder / zipped_file_name)
        zipped_file_path.parent.mkdir(parents=True, exist_ok=True)

        import shutil
        import gzip
        import zipfile
        from urllib.request import urlretrieve

        url = f'http://geodesy.unr.edu/gps_timeseries/kenv/{site.stem}/{zipped_file_name}'
        urlretrieve(url, zipped_file_path)

        with zipfile.ZipFile(zipped_file_path, "r") as zip_ref:
            # extract all files into the destination folder
            zip_ref.extractall(unzip_destination_folder)
            # delete the zipped folder
            zipped_file_path.unlink()

        # unzip then delete all *.kenv.gz files
        gzip_files = unzip_destination_folder.glob(
            'f{site.stem}.{date.year}*.gz')
        for file in gzip_files:
            with gzip.open(file, 'rb') as f_in:
                with open(file.with_suffix(''), 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            file.unlink()  # delete the gzipped file


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


def plot_east_north_up(gps_df, plot_name, column_names, inps, marker_size_factor=None):
    """Plot east, north, up components of a GPS timeseries."""

    fig, axes = plt.subplots(len(column_names), 1, figsize=(10, 6))
    fig.suptitle(f'{plot_name} Displacement Timeseries')

    if marker_size_factor is None:
        marker_size_factor = get_marker_scale_factor(gps_df)

    for i in range(len(column_names)):

        data_mm = gps_df[column_names[i]] * 1000  # convert m to mm

        axes[i].scatter(gps_df.index, data_mm, marker='o',
                        s=1*marker_size_factor)

        y_label = capitalize_first_letter(
            column_names[i].strip('_')).replace('(m)', ' (mm)')
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

        if inps.hours:
            for hour in inps.hours:
                axes[i].axvline(x=gps_df.index[0].replace(
                    hour=hour), linestyle='dashed', color='red', alpha=0.2)


def plot_gps_daily(inps, site):

    for key in ['start_date', 'end_date', 'start_vline', 'end_vline']:
        year = vars(inps)[key]
        setattr(inps, key, pd.to_datetime(year))

    column_names = GPS_COMPONENTS

    gps_df = pd.read_csv(site,  sep='\s+')
    gps_df.index = pd.to_datetime(gps_df['YYMMMDD'], format='%y%b%d')

# optionally trim data to start and end dates
    if inps.start_date:
        gps_df = gps_df.loc[inps.start_date:]
    if inps.end_date:
        gps_df = gps_df.loc[:inps.end_date]

    site_name = capitalize_first_letter(site.stem)

    plot_east_north_up(gps_df=gps_df,
                       plot_name=site_name,
                       column_names=column_names,
                       inps=inps,
                       marker_size_factor=inps.marker_size_factor)
    return site_name


def plot_gps_five_minutes(inps, site):

    gps_df = pd.read_csv(site, sep='\s+')
    gps_df = gps_df.rename(
        columns={'mm': 'month', 'dd': 'day', 's-day': 'seconds'})
    gps_df.index = pd.to_datetime(
        gps_df[['year', 'month', 'day', 'seconds']])

    column_names = FIVE_MIN_GPS_COMPONENTS
    plot_name = f'{site.name.split(".")[0]}_{gps_df.index[0].strftime("%m-%d-%Y")}'
    plot_east_north_up(gps_df=gps_df,
                       plot_name=plot_name,
                       column_names=column_names,
                       inps=inps,
                       marker_size_factor=inps.marker_size_factor)

    return plot_name


def main(iargs=None):

    inps = cmd_line_parse(iargs)

    for site in inps.sites:
        if inps.five_minutes:
            name = plot_gps_five_minutes(inps, site)
        else:
            name = plot_gps_daily(inps, site)

        if inps.no_display:
            save_path = (Path.cwd() / 'images' / f'{name}.png')
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(save_path)
        else:
            plt.show()


if __name__ == '__main__':
    main(sys.argv[1:])
