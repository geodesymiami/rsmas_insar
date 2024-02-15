#!/usr/bin/env python3

import sys
import numpy as np
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
from dateutil.relativedelta import relativedelta


EXAMPLE = """example:
  
  date = yyyy-mm-dd
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 2019-01-01 2021-29-09

  get_precipitation_lalo.py --download start_date end_date
  get_precipitation_lalo.py --download 2019-01-01 2021-09-29

"""
workDir = 'SCRATCHDIR'
path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'
#TODO change jsonVolcano path
jsonVolcano = 'volcanoes.json'
json_download_url = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wms?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Eruptions1960&outputFormat=application%2Fjson'

#TODO Adapt the script for hdf5 files too as it has been done for nc4
#TODO add requirements.txt
#TODO change SCRATCHDIR to WORKDIR or something else
#TODO possible to go back to version 7 of Final Run 

def create_parser():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('-d', '--download', nargs=2, metavar=('start_date', 'end_date'), help='download data')

    group.add_argument('--plot-daily', nargs=4, metavar=( 'latitude', 'longintude', 'start_date', 'end_date'))

    group.add_argument('--plot-weekly', nargs=4, metavar=( 'latitude', 'longintude', 'start_date', 'end_date'))

    group.add_argument('-vd', '--volcano-daily', nargs=1, metavar=( 'volcanoName'), help='plot eruption dates and precipitation levels')

    group.add_argument('-ls', '--list', action='store_true', help='list volcanoes')

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


def volcanoes_list(jsonfile):
    ############################## Alternative API but only with significant eruptions ##############################
    
    # r = requests.get('https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/volcanoes?nameInclude=Cerro')
    # volcan_json = r.json()
    # volcanoName = []

    # for item in volcan_json['items']:
    #     if item['name'] not in volcanoName:
    #         volcanoName.append(item['name'])

    # for volcano in volcanoName:
    #     print(volcano)

    # print(os.getcwd())

    ####################################################################################################################

    if not os.path.exists(jsonfile):
        crontab_volcano_json(jsonfile)

    f = open(jsonfile)
    data = json.load(f)
    volcanoName = []

    for j in data['features']:
        if j['properties']['VolcanoName'] not in volcanoName:
            volcanoName.append(j['properties']['VolcanoName'])

    for volcano in volcanoName:
        print(volcano)


def crontab_volcano_json(json_path):
    # TODO add crontab to update json file every ???
    json_download_url = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wms?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Eruptions1960&outputFormat=application%2Fjson'
    result = requests.get(json_download_url)
    f = open(json_path, 'wb')
    f.write(result.content)
    f.close()


def extract_volcanoes_info(jsonfile, volcanoName):
    f = open(jsonfile)
    data = json.load(f)
    start_dates = []
    first_day = datetime.strptime('2000-06-01', '%Y-%m-%d').date()
    last_day = datetime.today().date() - relativedelta(days=1)

    for j in data['features']:
        if j['properties']['VolcanoName'] == volcanoName:

            name = (j['properties']['VolcanoName'])
            start = datetime.strptime((j['properties']['StartDate']), '%Y%m%d').date()
            try:
                end = datetime.strptime((j['properties']['EndDate']), '%Y%m%d').date()
            except:
                end = 'None'
            
            print(f'{name} eruption started {start} and ended {end}')

            if start >= first_day and start <= last_day:
                start_dates.append(start)
                coordinates = j['geometry']['coordinates']

    if not start_dates:
        print(f'Error: {volcanoName} eruption date is out of range')
        sys.exit(1)

    start_dates = sorted(start_dates)
    first_date = start_dates[0]

    if first_date - relativedelta(days=90) >= first_day:
        first_date = first_date - relativedelta(days=90)
    else:
        first_date = first_day

    date_list = pd.date_range(start = first_date, end = start_dates[-1]).date

    return start_dates, date_list, coordinates


def plot_eruptions(start_date):
    for date in start_date:
        plt.axvline(x = date_to_decimal_year(str(date)), color='red', linestyle='--', label='Eruption Date')


def generate_url_download(date):
    # Creates gpm_data folder if it doesn't exist
    intervals = {"Final06": datetime.strptime('2021-09-30', '%Y-%m-%d').date(),
                 "Final07": datetime.strptime('2023-07-31', '%Y-%m-%d').date(),
                 "Late06": datetime.today().date() - relativedelta(days=1)}
    
    # Final Run 06
    if date <= intervals["Final06"]:    
        head = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.06/'
        body = '/3B-DAY.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V06.nc4'

    # Late Run 06
    elif date > intervals["Final07"]:
        head = 'https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDL.06/'
        body = '/3B-DAY-L.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V06.nc4'

    # Final Run 07
    else:
        head = 'https://data.gesdisc.earthdata.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/'
        body = '/3B-DAY.MS.MRG.3IMERG.'
        tail = '-S000000-E235959.V07B.nc4'

    year = str(date.year)
    day = str(date.strftime('%d'))
    month = str(date.strftime('%m'))

    url = head + year + '/' + month + body + year+month+day + tail

    return url


def adapt_coordinates(lon, lat):
    lat = float("%.1f"%lat)
    lon = float("%.1f"%lon)

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

    return round(float(lon),2), round(float(lat),2)


def dload_site_list(folder, date_list):
    if not os.path.exists(folder):
        os.makedirs(folder)

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


def plot_precipitaion_nc4(longitude, latitude, date_list, folder):

        finaldf = {}
        df = pd.DataFrame()
        dictionary = {}

        longitude, latitude = adapt_coordinates(longitude, latitude)
        lon, lat = generate_coordinate_array()

        lon_index = lon.index(longitude)
        lat_index = lat.index(latitude)

        # For each file in the data folder that has nc4 extension
        for f in os.listdir(folder):

            if f.endswith('.nc4'):
                file = folder + '/' + f

                #Extract date from file name
                d = re.search('\d{4}[-]\d{2}[-]\d{2}', file)
                date = datetime.strptime(d.group(0), "%Y-%m-%d").date()

                if date in date_list:
                    #Open the file
                    ds = nc.Dataset(file)

                    dictionary[str(date)] = {}

                    try:
                        data = ds['precipitationCal']
                    except:
                        data = ds['precipitation']

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


def generate_date_list(start, end):
        sdate = datetime.strptime(start,'%Y-%m-%d').date()
        edate = datetime.strptime(end,'%Y-%m-%d').date()

        if edate >= datetime.today().date():
            edate = datetime.today().date() - relativedelta(days=1)

        #Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start = sdate,end = edate).date

        return date_list


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
    # plt.ylabel("Precipitation [mm/day]")
    # plt.gca().xaxis.set_major_locator(dt.DayLocator(interval=intervals))
    # plt.xticks(rotation=90)
    # plt.bar(df1['Date'],df1['Precipitation'], color ='maroon',
    #         width = 0.5)
    plt.show()


def daily_precipitation(dictionary, lat, lon, volcano=''):

    rainfalldfNoNull = dictionary.dropna()

    # Convert date strings to decimal years
    rainfalldfNoNull['Decimal_Year'] = rainfalldfNoNull['Date'].apply(date_to_decimal_year)
    rainfalldfNoNull["cum"] = rainfalldfNoNull.Precipitation.cumsum()

    fig, ax = plt.subplots(layout='constrained')

    if 1==1:
        lower = rainfalldfNoNull['Precipitation'].quantile(0.33)
        upper = rainfalldfNoNull['Precipitation'].quantile(0.66)

        rainfalldfNoNull['color'] = np.where(rainfalldfNoNull['Precipitation'] < lower, 'yellow', 
                                     np.where(rainfalldfNoNull['Precipitation'] < upper, 'green', 'blue'))
        
        plt.bar(rainfalldfNoNull.Decimal_Year, rainfalldfNoNull.Precipitation, color=rainfalldfNoNull['color'], width=0.00001 * len(rainfalldfNoNull))
    
    # fig, ax = plt.subplots(layout='constrained')
    else:
        plt.bar(rainfalldfNoNull.Decimal_Year, rainfalldfNoNull.Precipitation, color='maroon', width=0.00001 * len(rainfalldfNoNull))
    
    plt.ylabel("Precipitation [mm/day]")
    rainfalldfNoNull.plot('Decimal_Year', 'cum', secondary_y=True, ax=ax)

    if volcano == '':
        plt.title(f'Latitude: {lat}, Longitude: {lon}')
    else:
        plt.title(f'{volcano} - Latitude: {lat}, Longitude: {lon}')

    ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    ax.get_legend().remove()

    plt.xticks(rotation=90)

    return plt


if workDir in os.environ:
    work_dir = os.getenv(workDir) + '/' + 'gpm_data'

else:
    work_dir = os.getenv('HOME') + '/gpm_data'

if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.download:
        dload_site_list(work_dir, generate_date_list(args.download[0], args.download[1]))
        crontab_volcano_json(work_dir + '/' + jsonVolcano)  # TODO modify path

    else:
        if args.plot_daily:
            la = round(float(args.plot_daily[0]), 1)
            lo = round(float(args.plot_daily[1]), 1)
            start_date = args.plot_daily[2]
            end_date = args.plot_daily[3]

        elif args.plot_weekly:
            la = round(float(args.plot_weekly[0]), 1)
            lo = round(float(args.plot_weekly[1]), 1)
            start_date = args.plot_weekly[2]
            end_date = args.plot_weekly[3]

        elif args.volcano_daily:
            eruption_dates, date_list, lon_lat = extract_volcanoes_info(work_dir + '/' + jsonVolcano, args.volcano_daily[0])
            lo,la = adapt_coordinates(lon_lat[0], lon_lat[1])

            dload_site_list(work_dir, date_list)
            prec = plot_precipitaion_nc4(lo, la, date_list, work_dir)
            plt = daily_precipitation(prec, la, lo, volcano=args.volcano_daily[0])
            plot_eruptions(eruption_dates, args.volcano_daily[0])
            plt.show()
            sys.exit(0)

        elif args.list:
            volcanoes_list(work_dir + '/' + jsonVolcano)
            sys.exit(0)

        else:
            print('Error: no plot frequency specified')
            sys.exit(1)

        date_list = generate_date_list(start_date, end_date)
        dload_site_list(work_dir, date_list)
        prec = plot_precipitaion_nc4(lo, la, date_list, work_dir)

        if args.plot_daily:
            plt = daily_precipitation(prec, la, lo)
            plt.show()

        elif args.plot_weekly:
            weekly_precipitation(prec, la, lo)