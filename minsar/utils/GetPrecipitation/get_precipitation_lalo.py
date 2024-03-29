#!/usr/bin/env python3

import sys
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import dates as dt
import os
import re
from datetime import datetime, date
import requests
import argparse
import calendar
import json
import netCDF4 as nc
from dateutil.relativedelta import relativedelta
import geopandas as gpd
import concurrent.futures
import subprocess
import threading
import sys
import time
import subprocess
from scipy.interpolate import interp2d



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
  get_precipitation_lalo.py --volcano 'Cerro Azul'
  get_precipitation_lalo.py --list
  get_precipitation_lalo.py --colormap 20000601 --latitude=-2.11:2.35 --longitude=-92.68:-88.49
  get_precipitation_lalo.py --colormap 20000601 --latitude 19.5:20.05 --longitude 156.5:158.05 --vlim 0 10
  get_precipitation_lalo.py --colormap 20000601 --latitude 19.5:20.05 --longitude 156.5:158.05 --vlim 0 10 --interpolate 5
  get_precipitation_lalo.py --colormap 20000601 --polygon 'POLYGON((113.4496 -8.0893,113.7452 -8.0893,113.7452 -7.817,113.4496 -7.817,113.4496 -8.0893))'
  get_precipitation_lalo.py --colormap 20000601 --latitude=-2.11:2.35 --longitude=-92.68:-88.49 --colorbar jet

"""
workDir = 'WORKDIR'
# TODO remove this
workDir = 'SCRATCHDIR'

path_data = '/Users/giacomo/Library/CloudStorage/OneDrive-UniversityofMiami/GetPrecipitation/'
#TODO change jsonVolcano path
jsonVolcano = 'volcanoes.json'
json_download_url = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wms?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Eruptions1960&outputFormat=application%2Fjson'

#TODO possible to go back to version 7 of Final Run 


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
                        help='Start date of the search')
    parser.add_argument('--end-date', 
                        metavar='DATE', 
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
                        nargs='+', 
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
    parser.add_argument('--interpolate',
                        nargs=1,
                        metavar=('GRANULARITY'), 
                        help='Interpolate data')
    parser.add_argument('--average', 
                        nargs=1, 
                        metavar=('TIME_PERIOD'), 
                        help='Average data')
    parser.add_argument('--check', 
                        action='store_true', 
                        help='Check if the file is corrupted')
    parser.add_argument('--colorbar', 
                        nargs=1,
                        metavar=('COLORBAR'), 
                        help='Colorbar')

    inps = parser.parse_args()

    if not inps.dir:
        inps.dir = (os.getenv(workDir)) if workDir in os.environ else (os.getenv('HOME'))
        inps.dir = inps.dir + '/gpm_data'

    else:
        inps.dir = inps.dir[0]

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
                inps.colormap = datetime.strptime(inps.colormap[0], '%Y%m%d').date(), None

            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)

        elif len(inps.colormap) == 2:
            try:
                inps.colormap = datetime.strptime(inps.colormap[0], '%Y%m%d').date(), datetime.strptime(inps.colormap[1], '%Y%m%d').date()
            
            except ValueError:
                print('Error: Date format not valid, if only 1 argument is given, it must be in the format YYYYMMDD')
                sys.exit(1)
     
        else:
            parser.error("--colormap requires 1 or 2 arguments")

    if not inps.colorbar:
        inps.colorbar = 'viridis'

    return inps

###################### END NEW PARSER ######################
'''
Prompt images
'''
def prompt_subplots(inps):
    prompt_plots = []
    gpm_dir = inps.dir
    volcano_json_dir = inps.dir + '/' + jsonVolcano

    if inps.latitude and inps.longitude:
        inps.latitude, inps.longitude = adapt_coordinates(inps.latitude, inps.longitude)

    if inps.download:
        dload_site_list_parallel(gpm_dir, generate_date_list(inps.download[0], inps.download[1]))
    
    if inps.plot_daily:
        inps.plot_daily[0], inps.plot_daily[1] = adapt_coordinates(inps.plot_daily[0], inps.plot_daily[1])
        date_list = generate_date_list(inps.plot_daily[2], inps.plot_daily[3])
        prec = create_map(inps.plot_daily[0], inps.plot_daily[1], date_list, gpm_dir)
        bar_plot(prec, inps.plot_daily[0], inps.plot_daily[1])
        prompt_plots.append('plot_daily')

    if inps.plot_weekly:
        inps.plot_weekly[0], inps.plot_weekly[1] = adapt_coordinates(inps.plot_weekly[0], inps.plot_weekly[1])
        date_list = generate_date_list(inps.plot_weekly[2], inps.plot_weekly[3])
        prec = create_map(inps.plot_weekly[0], inps.plot_weekly[1], date_list, gpm_dir)
        prec = weekly_monthly_yearly_precipitation(prec, "W")
        bar_plot(prec, inps.plot_weekly[0], inps.plot_weekly[1])
        prompt_plots.append('plot_weekly')

    if inps.plot_monthly:
        inps.plot_monthly[0], inps.plot_monthly[1] = adapt_coordinates(inps.plot_monthly[0], inps.plot_monthly[1])
        date_list = generate_date_list(inps.plot_monthly[2], inps.plot_monthly[3])
        prec = create_map(inps.plot_monthly[0], inps.plot_monthly[1], date_list, gpm_dir)
        prec = weekly_monthly_yearly_precipitation(prec, "M")
        bar_plot(prec, inps.plot_monthly[0], inps.plot_monthly[1])
        prompt_plots.append('plot_monthly')

    if inps.plot_yearly:    
        inps.plot_yearly[2], inps.plot_yearly[3] = adapt_coordinates(inps.plot_yearly[2], inps.plot_yearly[3])
        date_list = generate_date_list(inps.plot_yearly[0], inps.plot_yearly[1])
        prec = create_map(inps.plot_yearly[2], inps.plot_yearly[3], date_list, gpm_dir)
        prec = yearly_precipitation(prec) #weekly_monthly_yearly_precipitation(prec, "Y")
        bar_plot(prec, inps.plot_yearly[2], inps.plot_yearly[3])
        prompt_plots.append('plot_yearly')

    if inps.volcano:
        eruption_dates, date_list, lola = extract_volcanoes_info(volcano_json_dir, inps.volcano[0])
        lo, la = adapt_coordinates(lola[0], lola[1])
        dload_site_list_parallel(gpm_dir, date_list)
        prec = create_map(lo, la, date_list, gpm_dir)
        bar_plot(prec, la, lo, volcano=inps.volcano[0])
        plot_eruptions(eruption_dates) 
        plt.show()
        prompt_plots.append('volcano')

    if inps.list:
        volcanoes_list(volcano_json_dir)

        prompt_plots.append('list')

    if inps.colormap:
        la, lo = adapt_coordinates(inps.latitude, inps.longitude)
        date_list = generate_date_list(inps.colormap[0], inps.colormap[1])
        print(date_list[0], date_list[-1])
        prova = create_map(la, lo, date_list, gpm_dir)

        #TODO condition monthly, yearly, maybe specific date range
        #TODO if no time_period here, it will avarage the whole period
        # prova = weekly_monthly_yearly_precipitation(prova, 'M')
        print(prova)
        prova = weekly_monthly_yearly_precipitation(prova, inps.average)
        print(prova)

        if inps.interpolate:
            prova = interpolate_map(prova, int(inps.interpolate[0]))

        map_precipitation(prova, lo, la, date_list, './ne_10m_land', inps.colorbar,inps.vlim)

    if inps.check:
        check_nc4_files(gpm_dir)


def parse_polygon(polygon):
    """
    Parses a polygon string retreive from ASF vertex tool and extracts the latitude and longitude coordinates.

    Args:
        polygon (str): The polygon string in the format "POLYGON((lon1 lat1, lon2 lat2, ...))".

    Returns:
        tuple: A tuple containing the latitude and longitude coordinates as lists.
               The latitude list contains the minimum and maximum latitude values.
               The longitude list contains the minimum and maximum longitude values.
    """
    latitude = []
    longitude = []
    pol = polygon.replace("POLYGON((", "").replace("))", "")

    # Split the string into a list of coordinates
    for word in pol.split(','):
        if (float(word.split(' ')[1])) not in latitude:
            latitude.append(float(word.split(' ')[1]))
        if (float(word.split(' ')[0])) not in longitude:
            longitude.append(float(word.split(' ')[0]))

    longitude = [round(min(longitude),2), round(max(longitude),2)]
    latitude = [round(min(latitude),2), round(max(latitude),2)]

    return latitude, longitude


def parse_plot(plot, latitudes, longitudes, start_date=None, end_date=None):
    """
    Parses the plot parameters for precipitation data.

    Args:
        plot (list): The plot input parameters.
        latitudes (list): The latitude values.
        longitudes (list): The longitude values.
        start_date (datetime, optional): The start date. Defaults to None.
        end_date (datetime, optional): The end date. Defaults to None.

    Returns:
        list: The parsed plot parameters.
    """
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



def parse_coordinates(coordinates):
    """
    Parse the given coordinates string and convert it into a list of floats.

    Args:
        coordinates (str): The coordinates string to be parsed.

    Returns:
        list: A list of floats representing the parsed coordinates.

    Raises:
        ValueError: If the coordinates string is invalid.

    """
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



def date_to_decimal_year(date_str):
    """
    Converts a date string or date object to a decimal year.

    Parameters:
    date_str (str or datetime.date): The date string in the format 'YYYY-MM-DD' or a datetime.date object.

    Returns:
    float: The decimal year representation of the input date.

    Example:
    >>> date_to_decimal_year('2022-01-01')
    2022.0
    """
    if type(date_str) == str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    else:
        date_obj = date_str

    year = date_obj.year
    day_of_year = date_obj.timetuple().tm_yday
    decimal_year = year + (day_of_year - 1) / 365.0
    decimal_year = round(decimal_year, 4)
    return decimal_year


def days_in_month(date):
    """
    Get the number of days in a given month.

    Args:
        date (str or datetime.date): The date in the format "YYYY-MM-DD" or a datetime.date object.

    Returns:
        int: The number of days in the month.

    Raises:
        ValueError: If the date is not in the correct format.

    """
    try:
        year, month, day = map(int, date.split("-"))
    except:
        year, month = date.year, date.month 
    
    num_days = calendar.monthrange(year, month)[1]

    return num_days


def generate_coordinate_array(longitude=[-179.95], latitude=[-89.95]):
    """
    Generate an array of coordinates based on the given longitude and latitude ranges.

    Args:
        longitude (list, optional): A list containing the minimum and maximum longitude values. Defaults to [-179.95].
        latitude (list, optional): A list containing the minimum and maximum latitude values. Defaults to [-89.95].

    Returns:
        tuple: A tuple containing the generated longitude and latitude arrays.

    The default list generated is used to reference the indexes of the precipitation array in the netCDF4 file.
    """
    try:
        lon = np.round(np.arange(longitude[0], longitude[1], 0.1), 2)
        lat = np.round(np.arange(latitude[0], latitude[1], 0.1), 2)

    except:
        lon = np.round(np.arange(longitude[0], 180.05, 0.1), 2)
        lat = np.round(np.arange(latitude[0], 90.05, 0.1), 2)

    return lon, lat


def volcanoes_list(jsonfile):
    """
    Retrieves a list of volcano names from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.

    Returns:
        None
    """
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
    """
    Downloads a JSON file containing volcano eruption data from a specified URL and saves it to the given file path.

    Args:
        json_path (str): The file path where the JSON file will be saved.

    Raises:
        requests.exceptions.HTTPError: If an HTTP error occurs while downloading the JSON file.

    Returns:
        None
    """
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
    """
    Extracts information about a specific volcano from a JSON file.

    Args:
        jsonfile (str): The path to the JSON file containing volcano data.
        volcanoName (str): The name of the volcano to extract information for.

    Returns:
        tuple: A tuple containing the start dates of eruptions, a date list, and the coordinates of the volcano.
    """
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
    """
    Plot vertical lines on a graph to indicate eruption dates.

    Parameters:
    start_date (list): A list of eruption start dates.

    Returns:
    None
    """
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
    """
    Adjusts the latitude and longitude coordinates to ensure they fall within the valid range (GPM dataset resolution).

    Parameters:
    latitude (float or str or list): The latitude coordinate(s) to be adjusted.
    longitude (float or str or list): The longitude coordinate(s) to be adjusted.

    Returns:
    tuple: A tuple containing the adjusted latitude and longitude coordinates.

    Raises:
    ValueError: If any of the latitude or longitude values are not within the valid range.

    """
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


def generealte_urls_list(date_list):
    """
    Generate a list of URLs for downloading precipitation data.

    Parameters:
    date_list (list): A list of dates for which the precipitation data will be downloaded.

    Returns:
    list: A list of URLs for downloading precipitation data.

    """
    urls = []

    for date in date_list:
        url = generate_url_download(date)
        urls.append(url)

    return urls


# TODO check if the file has been downlaoded every time
def dload_site_list_parallel(folder, date_list):
    """
    Downloads files from a list of URLs in parallel using multiple threads.

    Args:
        folder (str): The folder path where the downloaded files will be saved.
        date_list (list): A list of dates or URLs to download.

    Returns:
        None
    """

    if not os.path.exists(folder):
        os.makedirs(folder)

    urls = generealte_urls_list(date_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for url in urls:
            filename = os.path.basename(url)
            file_path = os.path.join(folder, filename)

            if not os.path.exists(file_path):
                print(f"Starting download of {url} on {threading.current_thread().name}")
                attempts = 0
                while attempts < 3:
                    try:
                        subprocess.run(['wget', url, '-P', folder], check=True)
                        print(f"Finished download of {url} on {threading.current_thread().name}")
                        break
                    except subprocess.CalledProcessError:
                        attempts += 1
                        print(f"Download attempt {attempts} failed for {url}. Retrying...")
                        time.sleep(1)
                else:
                    print(f"Failed to download {url} after {attempts} attempts. Exiting...")
                    sys.exit(1)
            else:
                print(f"File {filename} already exists, skipping download")



def check_nc4_files(folder):
    # Get a list of all .nc4 files in the directory
    files = [folder + '/' + f for f in os.listdir(folder) if f.endswith('.nc4')]
    print('Checking for corrupted files...')

    # Check if each file exists and is not corrupted
    for file in files:
        try:
            # Try to open the file with netCDF4
            ds = nc.Dataset(file)
            ds.close()

        except:
            print(f"File is corrupted: {file}")
            # Delete the corrupted file
            os.remove(file)
            print(f"Corrupted file has been deleted: {file}")


def interpolate_map(dataframe, resolution=5):
    """
    Interpolates a precipitation map using scipy.interpolate.interp2d.

    Parameters:
    dataframe (pandas.DataFrame): The input dataframe containing the precipitation data.
    resolution (int): The resolution factor for the interpolated map. Default is 5.

    Returns:
    numpy.ndarray: The interpolated precipitation map.
    """
    
    try:
        values = dataframe.get('Precipitation')[0][0]

    except:
        values = dataframe[0]

    x = np.arange(values.shape[1])
    y = np.arange(values.shape[0])
    # Create the interpolator function
    interpolator = interp2d(x, y, values)

    # Define the new x and y values with double the resolution
    new_x = np.linspace(x.min(), x.max(), values.shape[1]*resolution)
    new_y = np.linspace(y.min(), y.max(), values.shape[0]*resolution)

    # Perform the interpolation
    new_values = interpolator(new_x, new_y)

    return new_values


def process_file(file, date_list, lon, lat, longitude, latitude):
    # Extract date from file name
    d = re.search('\d{8}', file)
    date = datetime.strptime(d.group(0), "%Y%m%d").date()

    if date not in date_list:
        return None

    # Open the file
    ds = nc.Dataset(file)

    data = ds['precipitationCal'] if 'precipitationCal' in ds.variables else ds['precipitation']

    subset = data[:, np.where(lon == longitude[0])[0][0]:np.where(lon == longitude[1])[0][0]+1, np.where(lat == latitude[0])[0][0]:np.where(lat == latitude[1])[0][0]+1]
    subset = subset.astype(float)

    ds.close()

    return (str(date), subset)
    

def create_map(latitude, longitude, date_list, folder): #parallel
    """
    Creates a map of precipitation data for a given latitude, longitude, and date range.

    Parameters:
    latitude (list): A list containing the minimum and maximum latitude values.
    longitude (list): A list containing the minimum and maximum longitude values.
    date_list (list): A list of dates to include in the map.
    folder (str): The path to the folder containing the data files.

    Returns:
    pandas.DataFrame: A DataFrame containing the precipitation data for the specified location and dates to be plotted.
    """
    finaldf = pd.DataFrame()
    dictionary = {}

    lon, lat = generate_coordinate_array()

    # Get a list of all .nc4 files in the data folder
    files = [folder + '/' + f for f in os.listdir(folder) if f.endswith('.nc4')]

    # Check for duplicate files
    if len(files) != len(set(files)):
        print("There are duplicate files in the list.")
    else:
        print("There are no duplicate files in the list.")

    dictionary = {}

    for file in files:
        result = process_file(file, date_list, lon, lat, longitude, latitude)
        if result is not None:
            dictionary[result[0]] = result[1]


    df1 = pd.DataFrame(dictionary.items(), columns=['Date', 'Precipitation'])
    finaldf = pd.concat([finaldf, df1], ignore_index=True, sort=False)

    finaldf.sort_index()
    finaldf.sort_index(ascending=False)

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

    return dictionary


def generate_date_list(start, end=None):
    """
    Generate a list of dates between the start and end dates.

    Args:
        start (str or date): The start date in the format 'YYYYMMDD' or a date object.
        end (str or date, optional): The end date in the format 'YYYYMMDD' or a date object. 
            If not provided, the end date will be set to the last day of the month of the start date.

    Returns:
        list: A list of dates between the start and end dates.

    """
    if isinstance(start, str):
        sdate = datetime.strptime(start,'%Y%m%d').date()

    elif isinstance(start, date):
        try:
            sdate = start.date()

        except:
            sdate = start

    if isinstance(end, str):
        edate = datetime.strptime(end,'%Y%m%d').date()

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

    # Create a date range with the input dates, from start_date to end_date
    date_list = pd.date_range(start=sdate, end=edate).date

    return date_list


def bar_plot(precipitation, lat, lon, volcano=''):
    """
    Generate a bar plot of precipitation data.

    Parameters:
    - precipitation (dict or DataFrame): Dictionary or DataFrame containing precipitation data.
    - lat (float): Latitude value.
    - lon (float): Longitude value.
    - volcano (str, optional): Name of the volcano. Defaults to an empty string.

    Returns:
    None
    """

    if type(precipitation) == dict:
        precipitation = pd.DataFrame(precipitation.items(), columns=['Date', 'Precipitation'])

    # Convert array into single values
    precipitation['Precipitation'] = precipitation['Precipitation'].apply(lambda x: x[0][0][0])
    precipitation.sort_values(by='Date', ascending=True, inplace=True)
    
    # Convert date strings to decimal years
    #TODO to complete
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

    precipitation.plot(precipitation_field, 'cum', secondary_y=True, ax=ax)

    if volcano == '':
        plt.title(f'Latitude: {lat}, Longitude: {lon}')
    else:
        plt.title(f'{volcano} - Latitude: {lat}, Longitude: {lon}')

    # ax.set_xlabel("Yr")
    ax.right_ax.set_ylabel("Cumulative Precipitation [mm]")
    ax.get_legend().remove()

    plt.xticks(rotation=90)


def weekly_monthly_yearly_precipitation(dictionary, time_period=None):
    """
    Resamples the precipitation data in the given dictionary by the specified time period.

    Args:
        dictionary (dict): A dictionary containing precipitation data.
        time_period (str): The time period to resample the data by (e.g., 'W' for weekly, 'M' for monthly, 'Y' for yearly).

    Returns:
        pandas.DataFrame: The resampled precipitation data.

    Raises:
        KeyError: If the 'Precipitation' field is not found in the dictionary.
    """
    df = pd.DataFrame.from_dict(dictionary)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date_copy'] = df['Date']  # Create a copy of the 'Date' column
    df.set_index('Date_copy', inplace=True)

    if 'Precipitation' in df:
        if time_period is None:
            # Calculate the mean of the 'Precipitation' column
            average_precipitation = df['Precipitation'].mean()

            return average_precipitation
        
        else:
            # Resample the data by the time period and calculate the mean
            precipitation = df.resample(time_period[0]).mean()

            return precipitation
        
    else:
        raise KeyError('Error: Precipitation field not found in the dictionary')


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
    print(monthly_precipitation)
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

    print(yearly_precipitation)
    return yearly_precipitation


def map_precipitation(precipitation_series, lo, la, date, work_dir, colorbar, vlim=None):
    '''
    Maps the precipitation data on a given region.

    Args:
        precipitation_series (pd.DataFrame or dict or ndarray): The precipitation data series.
            If a pd.DataFrame, it should have a column named 'Precipitation' containing the data.
            If a dict, it should have date strings as keys and precipitation data as values.
            If an ndarray, it should contain the precipitation data directly.
        lo (list): The longitude range of the region.
        la (list): The latitude range of the region.
        date (list): The date of the precipitation data.
        work_dir (str): The path to the shapefile for plotting the island boundary.
        vlim (tuple, optional): The minimum and maximum values for the color scale. Defaults to None.

    Returns:
        None
    '''

    if type(precipitation_series) == pd.DataFrame:
        precip = precipitation_series.get('Precipitation')[0][0]

    elif type(precipitation_series) == dict:
        precip = precipitation_series[date[0].strftime('%Y-%m-%d')]

    else:
        precip = precipitation_series

    precip = np.flip(precip.transpose(), axis=0)

    if not vlim:
        vmin = 0
        vmax = precip.max()

    else:
        vmin = vlim[0]
        vmax = vlim[1]

    plt.imshow(precip, vmin=vmin, vmax=vmax, extent=[lo[0],lo[1],la[0],la[1]],cmap=colorbar)
    plt.ylim(la[0], la[1])
    plt.xlim(lo[0], lo[1])

    island_boundary = gpd.read_file(work_dir)
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
    cbar.set_label('mm/day')

    plt.show()
    print('DONE')

###################### TEST AREA ##########################
# lo, la = adapt_coordinates([(-93.680)+1,(-87.4981)-1], [(-3.113)+1, (3.353)-1])
# lo, la = adapt_coordinates([92.05, 92.05], [0.05, 0.05])
# date_list = generate_date_list('2000-06-01', '2000-06-30')
# prova = extract_precipitation(lo, la, date_list, work_dir)

# prova = monthly_precipitation(prova)

# bar_plot(prova, la, lo)
# inps = create_parser_new()
# prompt_subplots(inps)
# print(inps)

import numpy as np
import matplotlib.pyplot as plt
import requests

# Function to fetch altitude data using the Google Maps Elevation API
def get_altitude(lat, lon, api_key):
    url = "https://maps.googleapis.com/maps/api/elevation/json"
    params = {
        "locations": f"{lat},{lon}",
        "key": api_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data['results']:
        return data['results'][0]['elevation']
    else:
        print("No altitude data found for the given coordinates.")
        return None

# Function to create a grid of coordinates within a bounding box
def create_grid(top_left, bottom_right, grid_size):
    latitudes = np.linspace(top_left[0], bottom_right[0], 100)
    longitudes = np.linspace(top_left[1], bottom_right[1], 100)
    return np.array(np.meshgrid(latitudes, longitudes)).T.reshape(-1, 2)

# Function to fetch altitude data for the grid
def fetch_altitude_data(coords, api_key):
    return np.array([get_altitude(lat, lon, api_key) for lat, lon in coords])

# Function to plot isolines
def plot_isolines(coords, altitudes, grid_size):
    altitudes = altitudes.reshape(100, 100)
    plt.contour(altitudes, colors='black')
    plt.title('Altitude Isolines')
    plt.xlabel('Latitude')
    plt.ylabel('Longitude')
    plt.show()

# Example usage
api_key = "AIzaSyD9ZZ_N0lxrIsWa4LNR9l4CL-lkz5Zs0IE" # Replace with your actual API key
top_left = (40.7128, -74.0060) # Example: Top-left corner of the bounding box
bottom_right = (40.7028, -74.0160) # Example: Bottom-right corner of the bounding box
grid_size = 0.1 # Example: 0.1 degrees grid size

coords = create_grid(top_left, bottom_right, grid_size)
altitudes = fetch_altitude_data(coords, api_key)
plot_isolines(coords, altitudes, grid_size)


sys.exit(0)

#################### END TEST AREA ########################

################    NEW MAIN    #######################

def main():
    inps = create_parser_new()

    prompt_subplots(inps)

if __name__ == "__main__":
    main()

sys.exit(0)

################    END NEW MAIN    #######################