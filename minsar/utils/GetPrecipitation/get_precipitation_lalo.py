#!/usr/bin/env python3

import sys
import numpy
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import dates as dt
import os
from os import path
import h5py
import re
from datetime import datetime, timedelta
import requests
import argparse
import calendar
import json
import netCDF4 as nc

EXAMPLE = """example:
  
  date = yyyy-dd-mm
  get_precipitation_lalo.py --plot-[daily, weekly] latitude longitude startdate enddate
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 2019-01-01 2021-29-09

  get_precipitation_lalo.py --download start_date end_date
  get_precipitation_lalo.py --download 2019-01-01 2021-29-09

"""
workDir = 'SCRATCHDIR'
path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'

#TODO Adapt the script for hdf5 files too as it has been done for nc4
#TODO add requirements.txt
#TODO change SCRATCHDIR to WORKDIR or something else

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-d', '--download', nargs=2, metavar=('start', 'end'), help='download data')

    group.add_argument('--plot-daily', nargs=4, metavar=( 'lat', 'lon', 'start', 'end'))

    group.add_argument('--plot-weekly', nargs=4, metavar=( 'lat', 'lon', 'start', 'end'))

    # Add a subparser for the plot command
    # plot_parser = subparsers.add_parser('--plot', aliases=['-p'], help='plot data')
    # plot_parser.add_argument('plot', choices=['daily', 'weekly'], help='plot frequency')
    # plot_parser.add_argument('lat', help='latitude')
    # plot_parser.add_argument('lon', help='longitude')
    # plot_parser.add_argument('start', help='start date')
    # plot_parser.add_argument('end', help='end date')

    return parser


def date_to_decimal_year(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    year = date_obj.year
    day_of_year = date_obj.timetuple().tm_yday
    decimal_year = year + (day_of_year - 1) / 365.0
    decimal_year = round(decimal_year, 4)
    return decimal_year


def days_in_month(date):
    year, month, day = map(int, date.split("-"))
    num_days = calendar.monthrange(year, month)[1]
    return num_days


def generate_coordinate_array():
    lon = []
    lat = []
    lo = - 179.95
    la = - 89.95

    for i in range(0, 3600):
        lon.append(round(lo, 2))
        lo += 0.1

    for i in range(0, 1800):
        lat.append(round(la, 2))
        la += 0.1

    return lon, lat


def extract_volcanoes_info(jsonfile, volcanoName):
    f = open(jsonfile)
    data = json.load(f)
    for j in data['features']:
        if j['properties']['VolcanoName'] in volcanoName:

            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d')
            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d')
            except:
                end = 'None'
            print(f'{name} eruption started {start} and ended {end}')

def generate_url_download(date):
    # d = datetime.strptime(date, '%Y-%d-%m')
    year = str(date.year)
    day = str(date.strftime('%d'))
    month = str(date.strftime('%m'))
    url = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.06/' + year + '/' + month + '/3B-DAY.MS.MRG.3IMERG.' + year+month+day + '-S000000-E235959.V06.nc4'

    return url

def adapt_coordinates(lon, lat):
    lat = round(float(lat),1)
    lon = round(float(lon),1)

    if -179.95 <= lon <= 179.95:

        val = 0.05 if lon > 0 else  -0.05
        lon = lon + val

    else:
        raise ValueError(f'Values not in the Interval (-179.5, 179.5)')

    if -89.95 <= lat <= 89.95:

        val = 0.05 if lat > 0 else -0.05
        lat = lat + val

    else:
        raise ValueError(f'Values not in the Interval (-89.95, 89.95)')

    return lon, lat


def dload_site_list_nc4(folder, date_list):
    # Creates gpm_data folder if it doesn't exist
    for date in date_list:
        url = generate_url_download(date)
        filename = folder + '/' + str(date) + '.nc4'
        cnt = 0

        # Try download 4 times before sending an error
        while cnt < 4:
            if not os.path.exists(filename):
                result = requests.get(url.strip())

                try:
                    result.raise_for_status()
                    f = open(filename, 'wb')
                    f.write(result.content)
                    f.close()

                    if os.path.exists(filename):
                        print('Contents of URL written to ' + filename)
                        break

                    # Retry
                    else:
                        cnt += 1

                except requests.exceptions.HTTPError as err:
                    if err.response.status_code == 404:
                        print(f'Error: {err.response.status_code} Url Not Found')
                        cnt = 4
                    else:
                        print('An HTTP error occurred: ' + str(err.response.status_code))
                        cnt += 1

            else:
                print(f'File: {filename} already exists')
                break

        # Number of download retry exceeded
        if cnt >= 4:
           print(f'Failed to download file for date: {date} after 4 attempts. Exiting...')
           sys.exit(1)

    return folder


def dload_site_list_hdf5(folder, fpath):
    '''
    Creates data folder
    '''
    if not folder:
        folder = 'data'

    if not os.path.exists(folder):
        os.mkdir(folder)

    '''
    Looks for list of links i.e. the only txt file in the current folder
    '''
    if not fpath:

        txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]

        if len(txt_files) != 1:
            raise ValueError('should be only one txt file in the current directory')

        fpath = txt_files[0]
        print(fpath)

    '''
    Loop torough every line in the list of links .txt file and download every .HDF5 file within the list
    '''

    with open(fpath, "r") as ifile:
            for URL in ifile:
                if '.hdf5' in URL[-6:]:

                    d = re.search('\d{8}', URL)
                    d.group(0)
                    date = datetime.strptime(d.group(0), "%Y%m%d").date()

                    FILENAME = folder + '/'+ str(date) + '.hdf5'

                    if not os.path.exists(FILENAME):

                        result = requests.get(URL.strip())

                        try:
                            result.raise_for_status()
                            f = open(FILENAME,'wb')
                            f.write(result.content)
                            f.close()
                            print('contents of URL written to '+FILENAME)
                        except:
                            print('requests.get() returned an error code '+str(result.status_code))

                    else:
                        print(f'File: {FILENAME} already exists')
    return folder


def plot_precipitaion_hdf5(longitude, latitude, start_date, end_date, folder, fpath):

        finaldf = {}
        df = pd.DataFrame()
        dictionary = {}

        lon,lat = generate_coordinate_array()

        longitude, latitude = adapt_coordinates(longitude, latitude)

        sdate = datetime.strptime(start_date,'%Y-%d-%m')
        edate = datetime.strptime(end_date,'%Y-%d-%m')

        #Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start = sdate,end = edate).date

        #If the folder name is left blank, it will be automatically named 'data'
        if not folder:
            folder = 'data'

        '''
        Check if files date is in range with the input dates
        '''

        #Check if folder exists, otherwise execute download function
        if not os.path.exists(folder):
            folder = dload_site_list_hdf5(folder, fpath)

        else:

            try:

                #Converts file names within the data folder in date
                biggest = datetime.strptime(os.listdir(folder)[-1].replace('.nc4',''),'%Y-%m-%d').date()
                smallest = datetime.strptime(os.listdir(folder)[0].replace('.nc4',''),'%Y-%m-%d').date()

                for file in os.listdir(folder):

                    if file.endswith('.nc4') and datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date() < smallest:
                        smallest = datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date()

                    if file.endswith('.nc4') and datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date() > biggest:
                        biggest = datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date()

                #Create a range of dates with the name of the files within the data folder
                file_date_list = pd.date_range(start = smallest,end = biggest).date

                #Check if the date range passed as input is within the date range created from the downloaded files
                #if not, launch the download function
                if not all(elem in file_date_list for elem in date_list):

                    folder = dload_site_list_nc4(folder, )
            except:

                folder = dload_site_list_hdf5(folder, fpath)

        '''
        Loops trough every HDF5 file
        '''

        #For each file in the data folder that as HDF5 extension
        for f in os.listdir(folder):

            if f.endswith('.HDF5'):

                file = './' + folder + '/'+ f

                data = h5py.File(file,'r')

                d = re.search('\d{4}[-]\d{2}[-]\d{2}', file)
                date = datetime.strptime(d.group(0), "%Y-%d-%m").date()

                if date in date_list:

                    dictionary[str(date)] = {}

                    for key in data.keys():
                        pre = data[key]['precipitation']
                        lonPrec = dict(zip(lon, zip(*pre)))

                    lonPrec[longitude]

                    i = list(lat).index(latitude)
                    dictionary[str(date)] = lonPrec[longitude][0][i]

                    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
                    finaldf = pd.concat([df,df1], ignore_index=True, sort=False)

                else: continue

        finaldf = finaldf.sort_values(by='Date', ascending=True)

        return finaldf


def plot_precipitaion_nc4(longitude, latitude, start_date, end_date, folder):

        finaldf = {}
        df = pd.DataFrame()
        dictionary = {}

        longitude, latitude = adapt_coordinates(longitude, latitude)

        sdate = datetime.strptime(start_date, '%Y-%d-%m')
        edate = datetime.strptime(end_date, '%Y-%d-%m')

        # Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start=sdate, end=edate).date

        # If the folder name is left blank, it will be automatically named 'gpm_data'
        # if not folder:
        #     if 'SCRATCHDIR' in os.environ:
        #         folder = os.getenv('SCRATCHDIR') + '/' + 'gpm_data'
        #
        #     else:
        #         folder = './gpm_data'

        # Check if files date is in range with the input dates
        # Check if folder exists, otherwise execute download function
        if not os.path.exists(folder):
            folder = dload_site_list_nc4(folder, date_list)

        else:

            try:

                # Converts file names within the data folder in date
                # biggest = [f for f in os.listdir(folder) if f.endswith('.nc4')]
                biggest = datetime.strptime(os.listdir(folder)[-1].replace('.nc4',''),'%Y-%m-%d').date()
                smallest = datetime.strptime(os.listdir(folder)[0].replace('.nc4',''),'%Y-%m-%d').date()

                for file in os.listdir(folder):
                    if file.endswith('.nc4') and datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date() < smallest:
                        smallest = datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date()

                    if file.endswith('.nc4') and datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date() > biggest:
                        biggest = datetime.strptime(file.replace('.nc4',''),'%Y-%m-%d').date()

                # Create a range of dates with the name of the files within the data folder
                file_date_list = pd.date_range(start=smallest, end=biggest).date

                # Check if the date range passed as input is within the date range created from the downloaded files
                # if not, launch the download function
                if not all(elem in file_date_list for elem in date_list):
                    folder = dload_site_list_nc4(folder, date_list)
                else:
                    print('All files are present, no download needed')

            except:
                folder = dload_site_list_nc4(folder, date_list)

        '''
        Create longitude and latitude arrays
        '''

        lon, lat = generate_coordinate_array()

        lon_index = lon.index(longitude)
        lat_index = lat.index(latitude)

        '''
        Loops trough every nc4 file
        '''

        # For each file in the data folder that as nc4 extension
        for f in os.listdir(folder):

            if f.endswith('.nc4'):

                #Open the file
                file = folder + '/' + f
                ds = nc.Dataset(file)

                #Extract date from file name
                d = re.search('\d{4}[-]\d{2}[-]\d{2}', file)
                date = datetime.strptime(d.group(0), "%Y-%m-%d").date()

                if date in date_list:

                    dictionary[str(date)] = {}

                    data = ds['precipitationCal']
                    data[0,lon_index,lat_index]

                    dictionary[str(date)] = float(data[0,lon_index,lat_index])

                    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
                    finaldf = pd.concat([df,df1], ignore_index=True, sort=False)

                    df.sort_index()
                    df.sort_index(ascending=False)


                    ds.close()

                else: continue

        finaldf = finaldf.sort_values(by='Date', ascending=True)

        return finaldf


def check_nc4_hdf5_old(lo, la, start, end):

    # If the folder name is left blank, it will be automatically named 'gpm_data'
    if workDir in os.environ:
        folder = os.getenv(workDir) + '/' + 'gpm_data'

    else:
        folder = '$HOME/gpm_data'

    if not os.path.exists(folder):
        os.mkdir(folder)
        precip = plot_precipitaion_nc4(lo, la, start, end, folder)

    else:
        nc4_files = [f for f in os.listdir(folder) if f.endswith('.nc4')]
        hdf5_files = [f for f in os.listdir(folder) if f.endswith('.hdf5')]

        if len(nc4_files) >= len(hdf5_files):
            precip = plot_precipitaion_nc4(lo, la, start, end, folder)

        else:
            precip = plot_precipitaion_hdf5(lo, la, start, end, folder, 'fpath')

    return precip

def generate_date_list(start, end):
        sdate = datetime.strptime(start,'%Y-%d-%m')
        edate = datetime.strptime(end,'%Y-%d-%m')

        if edate >= datetime.today():
            edate = datetime.today() - timedelta(days=1)

        #Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start = sdate,end = edate).date

        return date_list

def check_nc4_hdf5_new(work_dir, start, end):    
        if not os.path.exists(work_dir):
            os.mkdir(work_dir)
    
        else:
            nc4_files = [f for f in os.listdir(work_dir) if f.endswith('.nc4')]
            hdf5_files = [f for f in os.listdir(work_dir) if f.endswith('.hdf5')]
    
            if len(nc4_files) >= len(hdf5_files):
                dload_site_list_nc4(work_dir, generate_date_list(start, end))
    
            else:
                dload_site_list_hdf5(work_dir, 'fpath')

def weekly_precipitation(dictionary, lat, lon):
    weekly_dict = {}
    Precipitation = []
    dictionary['Date'] = pd.to_datetime(dictionary['Date'])
    dictionary.reset_index(drop=True, inplace=True)

    if 'Precipitation' in dictionary:
        # Iterate through the dictionary and extract the values for the specified field
        for key, value in dictionary.items():
            if key == 'Precipitation':
                Precipitation.append(value)

    Dates = []
    if 'Date' in dictionary:
        # Iterate through the dictionary and extract the values for the specified field
        for key, value in dictionary.items():
            if key == 'Date':
                Dates.append(value)

    dates_len = len(Dates[0])
    precipitation_len = len(Precipitation[0])
    resto = dates_len % 7

    if dates_len == precipitation_len:
        index = 0
        value = 0

        for i in range(0, dates_len - resto):
            if index < 7:

                value += Precipitation[0][i]
                week = Dates[0][i]
                index += 1

            else:

                weekly_dict[week] = value
                index = 0
                value = 0

        index = 0
        value = 0

        for j in range((dates_len - resto), dates_len):

            value += Precipitation[0][j]
            week = Dates[0][j]
            index += 1

        weekly_dict[week] = value

    df1 = pd.DataFrame(weekly_dict.items(), columns=['Date', 'Precipitation'])
    df1.sort_values(by='Date', ascending=True)

    df1["cum"] = df1.Precipitation.cumsum()
    fig, ax = plt.subplots(layout='constrained')

    plt.bar(df1['Date'],df1['Precipitation'], color='maroon', width=0.01 * len(df1))
    plt.ylabel("Precipitation [mm/week]")

    df1.plot('Date', 'cum', secondary_y=True, ax=ax)

    plt.title(f'Latitude: {lat}, Longitude: {lon}')
    ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    ax.get_legend().remove()

    plt.xticks(rotation=90)

    print(df1)

    # plt.ylabel("Precipitation [mm/day]")
    # plt.gca().xaxis.set_major_locator(dt.DayLocator(interval=intervals))
    # plt.xticks(rotation=90)
    # plt.bar(df1['Date'],df1['Precipitation'], color ='maroon',
    #         width = 0.5)
    plt.show()


def daily_precipitation(dictionary, lat, lon):

    rainfalldfNoNull = dictionary.dropna()

    # Convert date strings to decimal years
    rainfalldfNoNull['Decimal_Year'] = rainfalldfNoNull['Date'].apply(date_to_decimal_year)
    rainfalldfNoNull["cum"] = rainfalldfNoNull.Precipitation.cumsum()
    print(rainfalldfNoNull)
    fig, ax = plt.subplots(layout='constrained')

    plt.bar(rainfalldfNoNull.Decimal_Year, rainfalldfNoNull.Precipitation, color='maroon', width=0.00001 * len(rainfalldfNoNull))

    plt.ylabel("Precipitation [mm/day]")

    rainfalldfNoNull.plot('Decimal_Year', 'cum', secondary_y=True, ax=ax)

    plt.title(f'Latitude: {lat}, Longitude: {lon}')
    ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")

    ax.get_legend().remove()

    plt.xticks(rotation=90)

    # #Eruptions
    # plt.axvline(x = date_to_decimal_year('2020-03-06'), color='red', linestyle='--', label='Eruption Date')
    # plt.axvline(x = date_to_decimal_year('2019-12-06'), color='red', linestyle='--', label='Eruption Date')

    # Data plot
    plt.show()


if workDir in os.environ:
    work_dir = os.getenv(workDir) + '/' + 'gpm_data'

else:
    work_dir = '$HOME/gpm_data'

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.download:
        nc4_files = [f for f in os.listdir(work_dir) if f.endswith('.nc4')]
        hdf5_files = [f for f in os.listdir(work_dir) if f.endswith('.hdf5')]

        if len(nc4_files) >= len(hdf5_files):
            check_nc4_hdf5_new(work_dir, args.download[0], args.download[1])

        else:
            dload_site_list_hdf5(args.download[0], args.download[1])

    elif args.plot_daily:
        la = round(float(args.plot_daily[0]), 1)
        lo = round(float(args.plot_daily[1]), 1)
        prec = check_nc4_hdf5(lo, la, args.plot_daily[2], args.plot_daily[3])

    elif args.plot_weekly:

        if args.plot[0] == 'daily':
            daily_precipitation(prec, la, lo)

        elif args.plot[0] == 'weekly':
            weekly_precipitation(prec, la, lo)

        else:
            daily_precipitation(prec, la, lo)
            plot_precipitaion_nc4(lo, la, args.start, args.end, work_dir)

    #HARDCODED TO BE PARAMETERISED

    # if args.plot == 'daily':
    #     daily_precipitation(prec, la, lo)
    # elif args.plot == 'weekly':
    #     weekly_precipitation(prec, la, lo)
    # else:
    #     daily_precipitation(prec, la, lo)

