#!/usr/bin/env python3

import numpy
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import dates as dt
import os
from os import path
import h5py
import re
from datetime import datetime
import requests
import argparse
import calendar
import json
import netCDF4 as nc

EXAMPLE = """example:
  
  date = yyyy-dd-mm
  get_precipitation_lalo.py latitude longitude startdate enddate
  get_precipitation_lalo.py 19.5 -156.5 2019-01-01 2021-29-09

"""

path_data = 'Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    parser.add_argument('--plot', choices=['daily', 'weekly'], required=False)
    parser.add_argument('la', help='latitude')
    parser.add_argument('lo', help='longitude')
    parser.add_argument('strt', help='start date')
    parser.add_argument('end', help='end date')

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


def dload_site_list_nc4(folder, fpath):
    '''
    Creates gpm_data folder
    '''

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
                if '.nc4' in URL[-6:]:

                    d = re.search('\d{8}', URL)
                    d.group(0)
                    date = datetime.strptime(d.group(0), "%Y%m%d").date()

                    FILENAME = folder + '/'+ str(date) + '.nc4'

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

                    folder = dload_site_list_nc4(folder, fpath)
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


def plot_precipitaion_nc4(longitude, latitude, start_date, end_date, folder, fpath):

        finaldf = {}
        df = pd.DataFrame()
        dictionary = {}

        longitude, latitude = adapt_coordinates(longitude, latitude)

        sdate = datetime.strptime(start_date,'%Y-%d-%m')
        edate = datetime.strptime(end_date,'%Y-%d-%m')

        #Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start=sdate, end=edate).date

        #If the folder name is left blank, it will be automatically named 'data'
        if not folder:
            folder = 'gpm_data'

        '''
        Check if files date is in range with the input dates
        '''

        #Check if folder exists, otherwise execute download function
        if not os.path.exists(folder):
            folder = dload_site_list_nc4(folder, fpath)

        else:

            try:

                #Converts file names within the data folder in date
                #biggest = [f for f in os.listdir(folder) if f.endswith('.nc4')]
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
                    folder = dload_site_list_nc4(folder, fpath)

                print('All files are present, no download needed')
            except:
                folder = dload_site_list_nc4(folder, fpath)

        '''
        Create longitude and latitude arrays
        '''

        lon, lat = generate_coordinate_array()

        lon_index = lon.index(longitude)
        lat_index = lat.index(latitude)

        '''
        Loops trough every nc4 file
        '''

        #For each file in the data folder that as nc4 extension
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


def check_nc4_hdf5(folder, lo, la, start, end, fpath):
    if not folder:
        folder = '.'

    nc4_files = [f for f in os.listdir(folder) if f.endswith('.nc4')]
    hdf5_files = [f for f in os.listdir(folder) if f.endswith('.hdf5')]

    if len(nc4_files) >= len(hdf5_files):
        #dload_site_list_nc4(folder, fpath)
        precip = plot_precipitaion_nc4(lo, la, start, end, folder, fpath)

    else:
        #dload_site_list_hdf5(folder, fpath)
        precip = plot_precipitaion_hdf5(lo, la, start, end, folder, fpath)

    return precip


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

    plt.bar(df1['Date'],df1['Precipitation'], color='maroon', width=0.01)
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

    plt.bar(rainfalldfNoNull.Decimal_Year, rainfalldfNoNull.Precipitation, color='maroon', width=0.01)
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


if 'SCRATCHDIR' in os.environ:
    work_dir = os.getenv('SCRATCHDIR') + '/' + 'gpm_data'

else:
    work_dir = './gpm_data'

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()
    la = round(float(args.la), 1)
    lo = round(float(args.lo), 1)

    #HARDCODED TO BE PARAMETERISED
    prec = check_nc4_hdf5('/' + path_data + 'data', lo, la, args.strt, args.end, '/' + path_data + 'subset_GPM_3IMERGDF_06_20230906_204147_.txt')

    if args.plot == 'daily':
        daily_precipitation(prec, la, lo)
    elif args.plot == 'weekly':
        weekly_precipitation(prec, la, lo)
    else:
        daily_precipitation(prec, la, lo)

