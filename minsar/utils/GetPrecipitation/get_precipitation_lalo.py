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
from datetime import datetime, date
import requests
import argparse
import calendar
import json
import netCDF4 as nc
from dateutil.relativedelta import relativedelta
import geopandas as gpd
from matplotlib.path import Path


EXAMPLE = """
!WARNING for negative values you may need to use the following format: 

--latitude=-10
--latitude=-10.5:-9.5

Date format: YYYYMMDD

Example:
  
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 20190101 20210929
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 --start-date 20190101 --end-date 20210929
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --latitude 19.5 --longitude -156.5
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --latitude=19.5 --longitude=-156.5
  get_precipitation_lalo.py --plot-daily 20190101 20210929 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'
  get_precipitation_lalo.py --download 20190101 20210929
  get_precipitation_lalo.py --download 20190101 20210929 --dir '/home/user/Downloads'
  get_precipitation_lalo.py --volcano-daily 'Cerro Azul'
  get_precipitation_lalo.py --list
  get_precipitation_lalo.py --colormap 20000601 --latitude 19.5 --longitude -156.5
  get_precipitation_lalo.py --colormap 20000601 --latitude 19.5 --longitude -156.5 --vlim 0 10
  get_precipitation_lalo.py --colormap 20000601 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'

"""
workDir = 'WORKDIR'
# TODO remove this
workDir = 'SCRATCHDIR'

path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'
#TODO change jsonVolcano path
jsonVolcano = 'volcanoes.json'
json_download_url = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wms?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Eruptions1960&outputFormat=application%2Fjson'

#TODO Adapt the script for hdf5 files too as it has been done for nc4
#TODO add requirements.txt
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

    group.add_argument('--plot-weekly', nargs=4, metavar=( 'latitude', 'longitude', 'start_date', 'end_date'))

    group.add_argument('--plot-monthly', nargs=4, metavar=( 'latitude', 'longitude', 'start_date', 'end_date'))

    group.add_argument('-vd', '--volcano-daily', nargs=1, metavar=( 'NAME'), help='plot eruption dates and precipitation levels')

    group.add_argument('-ls', '--list', action='store_true', help='list volcanoes')

    group.add_argument('--map', nargs=1, metavar=('date'),help='Heat map of precipitation')

    return parser

###################### NEW PARSER ######################

def create_parser_new():
    """ Creates command line argument parser object. """

    parser = argparse.ArgumentParser(
        description='Plot precipitation data from GPM dataset for a specific location at a given date range',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)
    
    parser.add_argument('--download', 
                        nargs='*', 
                        metavar=('STARTDATE', 'ENDDATE'),
                        default=None,
                        help='Download data')
    parser.add_argument('--volcano', 
                        nargs=1, 
                        metavar='NAME', 
                        help='Plot eruption dates and precipitation levels')
    parser.add_argument('--plot-daily', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with daily precipitation data')
    parser.add_argument('--plot-weekly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with weekly precipitation data')
    parser.add_argument('--plot-monthly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with monthly precipitation data')
    parser.add_argument('--plot-yearly', 
                        nargs='*', 
                        metavar=( 'LATITUDE, LONGITUDE, STARTDATE, ENDDATE'), 
                        help='Bar plot with yearly precipitation data')
    parser.add_argument('--start-date', 
                        metavar='DATE', 
                        type=datetime, 
                        help='Start date of the search')
    parser.add_argument('--end-date', 
                        metavar='DATE', 
                        type=datetime, 
                        help='End date of the search')
    parser.add_argument('--latitude', 
                        nargs='+',  
                        metavar=('MIN', 'MAX'),
                        help='Latitude')
    parser.add_argument('--longitude', 
                        nargs='+', 
                        metavar=('MIN', 'MAX'), 
                        help='Longitude')
    parser.add_argument('--list', 
                        action='store_true', 
                        help='List volcanoes')
    parser.add_argument('--colormap', 
                        nargs=1, 
                        metavar=('DATE, use polygon or latitude/longitude args'), 
                        help='Heat map of precipitation')
    parser.add_argument('--dir', 
                        nargs=1, 
                        metavar=('PATH'), 
                        help='Specify path to download the data, if not specified, the data will be downloaded either in WORKDIR or HOME directory')
    parser.add_argument("--vlim", 
                        nargs=2, 
                        metavar=("VMIN", "VMAX"), 
                        default=None,
                        type=float, 
                        help="Velocity limit for the colorbar (default: None)")
    parser.add_argument('--polygon', 
                        metavar='POLYGON', 
                        help='Poligon of the wanted area (Format from ASF Vertex Tool https://search.asf.alaska.edu/#/)')

    inps = parser.parse_args()

    if not inps.dir:
        inps.dir = (os.getenv(workDir)) if workDir in os.environ else (os.getenv('HOME'))

    inps.start_date = datetime.strptime(inps.start_date[0], '%Y%m%d').date() if inps.start_date else datetime.strptime('20000601', '%Y%m%d').date()

    inps.end_date = datetime.strptime(inps.end_date[0], '%Y%m%d').date() if inps.end_date else datetime.today().date() - relativedelta(days=1)

    if inps.download is None:
        pass

    elif len(inps.download) == 0:
        inps.download = datetime.strptime('20000601', '%Y%m%d').date(), (datetime.today().date() - relativedelta(days=1))

    elif len(inps.download) == 1:
        inps.download = inps.download[0], (datetime.today().date() - relativedelta(days=1))

    elif len(inps.download) == 2:
        inps.download = [datetime.strptime(inps.download[0], '%Y%m%d').date(), datetime.strptime(inps.download[1], '%Y%m%d').date()]

    else:
        parser.error("--download requires 0, 1 or 2 arguments")

    if not inps.polygon:
        
        if inps.latitude:
            if len(inps.latitude) == 1:
                inps.latitude = parse_coordinates(inps.latitude[0])

            elif len(inps.latitude) == 2:
                inps.latitude = [float(inps.latitude[0]), float(inps.latitude[1])]

            else:
                parser.error("--latitude requires 1 or 2 arguments")

        if inps.longitude:
            if len(inps.longitude) == 1:
                inps.longitude = parse_coordinates(inps.longitude[0])

            elif len(inps.longitude) == 2:
                inps.longitude = [float(inps.longitude[0]), float(inps.longitude[1])]

            else:
                parser.error("--longitude requires 1 or 2 arguments")

    else:
            inps.latitude, inps.longitude = parse_polygon(inps.polygon)

    if inps.plot_daily:
        inps.plot_daily = parse_plot(inps.plot_daily, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_weekly:
        inps.plot_weekly = parse_plot(inps.plot_weekly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_monthly:
        inps.plot_monthly = parse_plot(inps.plot_monthly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)

    if inps.plot_yearly:
        inps.plot_yearly = parse_plot(inps.plot_yearly, inps.latitude, inps.longitude, inps.start_date, inps.end_date)    

    if inps.colormap:
        if len(inps.colormap) == 1:
            try:
                inps.colormap = datetime.strptime(inps.colormap[0], '%Y%m%d').date(), inps.latitude, inps.longitude

            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)

        elif len(inps.colormap) == 2:
            parser.error("--colormap 2 arguments are ambiguous, requires 1 or 3 arguments")
        
        elif len(inps.colormap) == 3:
            try:
                inps.colormap = datetime.strptime(inps.colormap[0], '%Y%m%d').date(), parse_coordinates(inps.colormap[1]), parse_coordinates(inps.colormap[2])

            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)

    return inps

###################### END NEW PARSER ######################
'''
Prompt images
'''
def prompt_subplots(inps):
    prompt_plots = []

    if inps.latitude and inps.longitude:
        inps.latitude, inps.longitude = adapt_coordinates(inps.latitude, inps.longitude)

    if inps.download:
        date_list = generate_date_list(inps.download[0], inps.download[1])
        dload_site_list(inps.dir, date_list)
        prompt_plots.append('download')
    
    if inps.plot_daily:
        inps.plot_daily[0], inps.plot_daily[1] = adapt_coordinates(inps.plot_daily[0], inps.plot_daily[1])
        date_list = generate_date_list(inps.plot_daily[2], inps.plot_daily[3])
        # prec = extract_precipitation(inps.plot_daily[0], inps.plot_daily[1], date_list, inps.dir + '/gpm_data')
        prec = create_map(inps.plot_daily[0], inps.plot_daily[1], date_list, inps.dir + '/gpm_data')
        bar_plot(prec, inps.plot_daily[0], inps.plot_daily[1])
        prompt_plots.append('plot_daily')

    if inps.plot_weekly:
        inps.plot_weekly[0], inps.plot_weekly[1] = adapt_coordinates(inps.plot_weekly[0], inps.plot_weekly[1])
        date_list = generate_date_list(inps.plot_weekly[2], inps.plot_weekly[3])
        prec = create_map(inps.plot_weekly[0], inps.plot_weekly[1], date_list, inps.dir + '/gpm_data')
        prec = weekly_precipitation(prec)
        bar_plot(prec, inps.plot_weekly[0], inps.plot_weekly[1])
        prompt_plots.append('plot_weekly')

    if inps.plot_monthly:
        inps.plot_monthly[0], inps.plot_monthly[1] = adapt_coordinates(inps.plot_monthly[0], inps.plot_monthly[1])
        date_list = generate_date_list(inps.plot_monthly[2], inps.plot_monthly[3])
        prec = create_map(inps.plot_monthly[0], inps.plot_monthly[1], date_list, inps.dir + '/gpm_data')
        prec = monthly_precipitation(prec)
        bar_plot(prec, inps.plot_monthly[0], inps.plot_monthly[1])
        prompt_plots.append('plot_monthly')

    if inps.plot_yearly:    
        inps.plot_yearly[2], inps.plot_yearly[3] = adapt_coordinates(inps.plot_yearly[2], inps.plot_yearly[3])
        date_list = generate_date_list(inps.plot_yearly[0], inps.plot_yearly[1])
        prec = create_map(inps.plot_yearly[2], inps.plot_yearly[3], date_list, inps.dir + '/gpm_data')
        prec = yearly_precipitation(prec)
        bar_plot(prec, inps.plot_yearly[2], inps.plot_yearly[3])
        prompt_plots.append('plot_yearly')

    if inps.volcano:
        eruption_dates, date_list, lalo = extract_volcanoes_info(inps.dir + '/' + jsonVolcano, inps.volcano[0])
        la, lo = adapt_coordinates(lalo[0], lalo[1])
        dload_site_list(inps.dir, date_list)
        prec = create_map(lo, la, date_list, inps.dir)
        bar_plot(prec, la, lo, volcano=inps.volcano[0])
        plot_eruptions(eruption_dates)

        prompt_plots.append('volcano')

    if inps.list:
        volcanoes_list(inps.dir + '/' + jsonVolcano)

        prompt_plots.append('list')

    if inps.colormap:
        la, lo = adapt_coordinates(inps.colormap[1], inps.colormap[2])
        date_list = generate_date_list(inps.colormap[0])
        # prova = extract_precipitation(la, lo, date_list, inps.dir + '/gpm_data')
        prova = create_map(la, lo, date_list, inps.dir + '/gpm_data')

        #TODO condition monthly, yearly, maybe specific date range
        prova = monthly_precipitation(prova)
        print(prova)
        
        map_precipitation(prova, lo, la, date_list, inps.vlim)

    # TODO dynamic plot
    # if prompt_plots != []:
    #     inps.plot_weekly[0], inps.plot_weekly[1] = adapt_coordinates(inps.plot_weekly[0], inps.plot_weekly[1])
    #     date_list = generate_date_list(inps.plot_weekly[2], inps.plot_weekly[3])
    #     prec = create_map(inps.plot_weekly[0], inps.plot_weekly[1], date_list, inps.dir + '/gpm_data')
    #     prec = weekly_precipitation(prec)
    #     bar_plot(prec, inps.plot_weekly[0], inps.plot_weekly[1])



'''
Parse for polygon
'''
def parse_polygon(polygon):
    latitude = []
    longitude = []
    pol = polygon.replace("POLYGON((", "").replace("))", "")

    for word in pol.split(','):
        if (float(word.split(' ')[1])) not in latitude:
            latitude.append(float(word.split(' ')[1]))
        if (float(word.split(' ')[0])) not in longitude:
            longitude.append(float(word.split(' ')[0]))

    longitude = [round(min(longitude),2), round(max(longitude),2)]
    latitude = [round(min(latitude),2), round(max(latitude),2)]

    return latitude, longitude


'''
Parse for bar plotting
'''
def parse_plot(plot, latitudes, longitudes, start_date=None, end_date=None):

    if len(plot) == 1:
        print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     " --plot-daily LATITUDE LONGITUDE arguments \n"
                     " --plot-weekly --latitude LATITUDE -- longitude LONGITUDE \n"
                     " START_DATE END_DATE are optional")
        sys.exit(1)

    elif len(plot) == 2:
        if latitudes and longitudes:
            plot = [latitudes[0], longitudes[0], datetime.strptime(plot[0], "%Y%m%d"), datetime.strptime(plot[1], "%Y%m%d")]

        elif start_date and end_date:
            plot = [parse_coordinates(plot[0]), parse_coordinates(plot[1]), start_date[0], end_date[0]]

        else:
            print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     " --plot-daily LATITUDE LONGITUDE arguments \n"
                     " --plot-weekly --latitude LATITUDE -- longitude LONGITUDE \n"
                     " START_DATE END_DATE are optional")
            sys.exit(1)

    elif len(plot) == 3:
            print("--plot-[daily, weekly, monthly, yearly] requires at least LATITUDE LONGITUDE arguments \n"
                     "Three arguments are ambiguous")
            sys.exit(1)

    elif len(plot) == 4:
        try:
            plot = [parse_coordinates(plot[0]), parse_coordinates(plot[1]), datetime.strptime(plot[2], "%Y%m%d"), datetime.strptime(plot[3], "%Y%m%d")]

        except ValueError:
            plot = [datetime.strptime(plot[0], "%Y%m%d"), datetime.strptime(plot[1], "%Y%m%d"), parse_coordinates(plot[2]), parse_coordinates(plot[3])]

        except Exception as e:
            print(e)
            sys.exit(1)

    return plot


'''
Convert the coordinates to list of floats
'''
def parse_coordinates(coordinates):
    coordinates = coordinates.replace("'", '').replace('"', '')

    try:
        if ',' in coordinates:
            coordinates = coordinates.split(',')
            coordinates = [float(i) for i in coordinates]

        elif ':' in coordinates:
            coordinates = coordinates.split(':')
            print(coordinates)
            coordinates = [float(i) for i in coordinates]

        elif ' ' in coordinates:
            coordinates = coordinates.split(' ')
            print(coordinates)
            coordinates = [float(i) for i in coordinates]

        else:
            coordinates = [float(coordinates), float(coordinates)]

    except ValueError:
        print(f'Error: {coordinates} invalid coordinate/s')
        sys.exit(1)

    return coordinates


'''
Convert date string to decimal year
'''
def date_to_decimal_year(date_str):
    if type(date_str) == str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    else:
        date_obj = date_str

    year = date_obj.year
    day_of_year = date_obj.timetuple().tm_yday
    decimal_year = year + (day_of_year - 1) / 365.0
    decimal_year = round(decimal_year, 4)
    return decimal_year


'''
Count days in a month
'''
def days_in_month(date):
    try:
        year, month, day = map(int, date.split("-"))
    except:
        year, month = date.year, date.month 
    
    num_days = calendar.monthrange(year, month)[1]

    return num_days


def generate_coordinate_array(longitude = [- 179.95], latitude = [- 89.95]):
    try:
        lon = np.round(np.arange(longitude[0], longitude[1], 0.1), 2)
        lat = np.round(np.arange(latitude[0], latitude[1], 0.1), 2)

    except:
        lon = np.round(np.arange(longitude[0], 180.05, 0.1), 2)
        lat = np.round(np.arange(latitude[0], 90.05, 0.1), 2)

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
    
    try:
        result = requests.get(json_download_url)
    
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            print(f'Error: {err.response.status_code} Url Not Found')
            sys.exit(1)

        else:
            print('An HTTP error occurred: ' + str(err.response.status_code))
            sys.exit(1)

    f = open(json_path, 'wb')
    f.write(result.content)
    f.close()

    if os.path.exists(json_path):
        print(f'Json file downloaded in {json_path}')

    else:
        print('Cannot create json file')


def extract_volcanoes_info(jsonfile, volcanoName):
    if not os.path.exists(jsonfile):
        crontab_volcano_json(jsonfile)

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
                coordinates = coordinates[::-1]

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


def adapt_coordinates(latitude, longitude):
    if isinstance(longitude, float) or isinstance(longitude, str):
        longitude = [longitude, longitude]

    if isinstance(latitude, float) or isinstance(latitude, str):
        latitude = [latitude, latitude]

    for i in range(len(latitude)):
        
        la = int(float(latitude[i]) *  10) /  10.0

        if -89.95 <= la <= 89.95:

            val = 0.05 if la > 0 else -0.05
            latitude[i] = round(la + val, 2)

        else:
            raise ValueError(f'Values not in the Interval (-89.95, 89.95)')
            
    for i in range(len(longitude)):
        lo = int(float(longitude[i]) *  10) /  10.0

        if -179.95 <= lo <= 179.95:

            val = 0.05 if lo > 0 else  -0.05
            longitude[i] = round(lo + val, 2)
        else:
            raise ValueError(f'Values not in the Interval (-179.5, 179.5)')
        
    return latitude, longitude


# TODO to change to parellel download and create a list of urls
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


def create_map(latitude, longitude, date_list, folder):
        finaldf = {}
        df = pd.DataFrame()
        dictionary = {}

        lon, lat = generate_coordinate_array()
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
                    data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']

                    subset = data[:, np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1, np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
                    dictionary[str(date)] = subset.astype(float)

                    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
                    finaldf = pd.concat([df,df1], ignore_index=True, sort=False)

                    df.sort_index()
                    df.sort_index(ascending=False)


                    ds.close()

                else: continue

        finaldf = finaldf.sort_values(by='Date', ascending=True)

        return finaldf


#TODO to remove, for now create_map works fine
def extract_precipitation(latitude, longitude, date_list, folder):
    dictionary = {}

    lon, lat = generate_coordinate_array()

    if longitude[1] and latitude[1]:
        last_longitude = longitude[1]
        last_latitude = latitude[1]

    else:
        last_longitude = longitude[0]
        last_latitude = latitude[0]

    # For each file in the data folder that has nc4 extension
    for f in os.listdir(folder):

        if f.endswith('.nc4'):
            file = folder + '/' + f

            #Extract date from file name
            d = re.search('\d{4}[-]\d{2}[-]\d{2}', file)
            file_date = datetime.strptime(d.group(0), "%Y-%m-%d").date()

            if file_date in date_list:
                #Open the file
                ds = nc.Dataset(file)

                dictionary[str(file_date)] = {}
                data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']
                
                subset = data[:, np.where(lon == longitude[0])[0][0]:np.where(lon == last_longitude)[0][0]+1, np.where(lat == latitude[0])[0][0]:np.where(lat == last_latitude)[0][0]+1]
                dictionary[str(file_date)] = subset.astype(float)
    print(dictionary)
    return dictionary

# TODO remove this function
def plot_precipitaion_nc4(longitude, latitude, date_list, folder):

    finaldf = {}
    df = pd.DataFrame()
    dictionary = {}

    lon, lat = generate_coordinate_array()

    lon_index = np.where(lon == longitude)[0][0]
    lat_index = np.where(lat == latitude)[0][0]

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

                data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']

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


def generate_date_list(start, end=None):
        if isinstance(start, str):
            sdate = datetime.strptime(start,'%Y-%m-%d').date()

        elif isinstance(start, date):
            try:
                sdate = start.date()

            except:
                sdate = start

        if isinstance(end, str):
            edate = datetime.strptime(end,'%Y-%m-%d').date()

        elif isinstance(end, date):
            try:
                edate = end.date()

            except:
                edate = end

        elif end is None:
            sdate = datetime(sdate.year, sdate.month, 1).date()
            edate = datetime(sdate.year, sdate.month, days_in_month(sdate)).date()

        if edate >= datetime.today().date():
            edate = datetime.today().date() - relativedelta(days=1)

        #Create a date range with the input dates, from start_date to end_date
        date_list = pd.date_range(start = sdate,end = edate).date

        return date_list


def bar_plot(precipitation, lat, lon, volcano=''):
    if type(precipitation) == dict:
        precipitation = pd.DataFrame(precipitation.items(), columns=['Date', 'Precipitation'])

    # Convert array into single values
    precipitation['Precipitation'] = precipitation['Precipitation'].apply(lambda x: x[0][0][0])
    precipitation.sort_values(by='Date', ascending=True, inplace=True)
    print(precipitation['Date'])
    # Convert date strings to decimal years
    if 'Non mensile o annuale':
        precipitation['Decimal_Year'] = precipitation['Date'].apply(date_to_decimal_year)
        precipitation_field = 'Decimal_Year'
    
    else:
        precipitation_field = 'Date'

    # Calculate the cumulative precipitation
    precipitation["cum"] = precipitation.Precipitation.cumsum()

    fig, ax = plt.subplots(layout='constrained')

    plt.bar(precipitation[precipitation_field], precipitation['Precipitation'], color='maroon', width=0.00001 * len(precipitation))
    plt.ylabel("Precipitation [mm]")

    print(precipitation)

    precipitation.plot(precipitation_field, 'cum', secondary_y=True, ax=ax)

    if volcano == '':
        plt.title(f'Latitude: {lat}, Longitude: {lon}')
    else:
        plt.title(f'{volcano} - Latitude: {lat}, Longitude: {lon}')

    # ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    ax.get_legend().remove()

    plt.xticks(rotation=90)
    plt.show()


def weekly_precipitation(dictionary):
    df = pd.DataFrame.from_dict(dictionary)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date_copy'] = df['Date']  # Create a copy of the 'Date' column
    df.set_index('Date_copy', inplace=True)

    if 'Precipitation' in df:
        # Resample the data by week and calculate the mean
        weekly_precipitation = df.resample('W').mean()

    else:
        print('Error: Precipitation field not found in the dictionary')
        sys.exit(1)

    return weekly_precipitation


def monthly_precipitation(dictionary):
    df = pd.DataFrame.from_dict(dictionary)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date_copy'] = df['Date']  # Create a copy of the 'Date' column
    df.set_index('Date_copy', inplace=True)

    if 'Precipitation' in df:
        # Resample the data by month and calculate the mean
        monthly_precipitation = df.resample('M').mean()

    else:
        print('Error: Precipitation field not found in the dictionary')
        sys.exit(1)

    return monthly_precipitation


def yearly_precipitation(dictionary):
    df = pd.DataFrame.from_dict(dictionary)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date_copy'] = df['Date']  # Create a copy of the 'Date' column
    df.set_index('Date_copy', inplace=True)

    if 'Precipitation' in df:
        # Resample the data by year and calculate the mean
        yearly_precipitation = df['Precipitation'].resample('Y').mean()

    else: 
        print('Error: Precipitation field not found in the dictionary')
        sys.exit(1)

    return yearly_precipitation


def map_precipitation(precipitation_series, lo, la, date, vlim=None):
    '''
    Example of global precipitations given by Nasa at: https://gpm.nasa.gov/data/tutorials
    '''  
    if type(precipitation_series) == pd.DataFrame:
        precip = precipitation_series.get('Precipitation')[0][0]

    elif type(precipitation_series) == dict:
        precip = precipitation_series[date[0].strftime('%Y-%m-%d')]
        
    precip = np.flip(precip.transpose(), axis=0)

    if not vlim:
        vmin = 0
        vmax = precip.max()

    else:
        vmin = vlim[0]
        vmax = vlim[1]

    plt.imshow(precip, vmin=vmin, vmax=vmax, extent=[lo[0],lo[1],la[0],la[1]])
    plt.ylim(la[0], la[1])
    plt.xlim(lo[0], lo[1])
    
    mapEarth = '/Users/giacomo/Desktop/ne_10m_land/ne_10m_land.shp'

    island_boundary = gpd.read_file(mapEarth)
    geometry = island_boundary['geometry']

    # Extract coordinates
    coordinates = []
    for geom in geometry:
        # Check the type of the geometry and extract coordinates accordingly
        if geom.geom_type == 'Polygon':
            # For polygons, extract exterior coordinates
            coords = geom.exterior.coords[:]
            coordinates.append(coords)
        elif geom.geom_type == 'MultiPolygon':
            # For multi-polygons, extract exterior coordinates for each polygon
            for polygon in geom.geoms:  # Use the 'geoms' attribute to iterate over polygons
                coords = polygon.exterior.coords[:]
                coordinates.append(coords)

    island_boundary.plot(ax=plt.gca(), edgecolor='white', facecolor='none') #plot shapefile

    # -- add a color bar
    cbar = plt.colorbar( )
    cbar.set_label('millimeters')

    plt.show()
    print('DONE')

###################### TEST ##########################
# lo, la = adapt_coordinates([(-93.680)+1,(-87.4981)-1], [(-3.113)+1, (3.353)-1])
# lo, la = adapt_coordinates([92.05, 92.05], [0.05, 0.05])
# date_list = generate_date_list('2000-06-01', '2000-06-30')
# prova = extract_precipitation(lo, la, date_list, work_dir)

# prova = monthly_precipitation(prova)

# bar_plot(prova, la, lo)
# inps = create_parser_new()
# prompt_subplots(inps)
# print(inps)

# sys.exit(0)

#################### END TEST ########################

################    NEW MAIN    #######################

def main():
    inps = create_parser_new()

    prompt_subplots(inps)

if __name__ == "__main__":
    main()

sys.exit(0)

################    END NEW MAIN    #######################

if __name__ == "__main__":
    parser = create_parser()
    inps = parser.parse_args()

    if inps.download:
        dload_site_list(work_dir, generate_date_list(inps.download[0], inps.download[1]))
        crontab_volcano_json(work_dir + '/' + jsonVolcano)  # TODO modify path

    else:
        if inps.plot_daily:
            la, lo = adapt_coordinates(inps.plot_daily[1], inps.plot_daily[0])
            start_date = inps.plot_daily[2]
            end_date = inps.plot_daily[3]

        elif inps.plot_weekly:
            la, lo = adapt_coordinates(inps.plot_weekly[1], inps.plot_weekly[0])
            start_date = inps.plot_weekly[2]
            end_date = inps.plot_weekly[3]

        elif inps.plot_monthly:
            la, lo = adapt_coordinates(inps.plot_monthly[1], inps.plot_monthly[0])
            start_date = inps.plot_monthly[2]
            end_date = inps.plot_monthly[3]

        elif inps.volcano_daily:
            eruption_dates, date_list, lon_lat = extract_volcanoes_info(inps.dir + '/' + jsonVolcano, inps.volcano_daily[0])
            la, lo = adapt_coordinates(lon_lat[0], lon_lat[1])

            dload_site_list(inps.dir, date_list)
            prec = plot_precipitaion_nc4(lo, la, date_list, inps.dir)
            plt = daily_precipitation(prec, la, lo, volcano=inps.volcano_daily[0])
            plot_eruptions(eruption_dates)
            plt.show()
            sys.exit(0)

        elif inps.list:
            volcanoes_list(inps.dir + '/' + jsonVolcano)
            sys.exit(0)
        #TODO restructure the code
        elif inps.map:
            map_precipitation(inps.dir, inps.map[0])
            sys.exit(0)

        else:
            print('Error: no plot frequency specified')
            sys.exit(1)

        date_list = generate_date_list(start_date, end_date)
        dload_site_list(work_dir, date_list)
        prec = plot_precipitaion_nc4(lo, la, date_list, work_dir)

        if inps.plot_daily:
            plt = daily_precipitation(prec, la, lo)
            plt.show()

        elif inps.plot_weekly:
            precipitation_values = weekly_precipitation(prec, la, lo)

        elif inps.plot_monthly:
            precipitation_values = monthly_precipitation(prec)

    bar_plot(precipitation_values, la, lo)