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
import geopandas as gpd
from matplotlib.path import Path


EXAMPLE = """example:
  
  date = yyyy-mm-dd
  get_precipitation_lalo.py --plot-daily 19.5 -156.5 2019-01-01 2021-09-29

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

    group.add_argument('--plot-weekly', nargs=4, metavar=( 'latitude', 'longitude', 'start_date', 'end_date'))

    group.add_argument('--plot-monthly', nargs=4, metavar=( 'latitude', 'longitude', 'start_date', 'end_date'))

    group.add_argument('-vd', '--volcano-daily', nargs=1, metavar=( 'NAME'), help='plot eruption dates and precipitation levels')

    group.add_argument('-ls', '--list', action='store_true', help='list volcanoes')

    group.add_argument('--map', nargs=1, metavar=('date'),help='Heat map of precipitation')

    return parser


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


def adapt_coordinates(longitude, latitude):
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
        
    return longitude, latitude


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


def create_map(longitude, latitude, date_list, folder):
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


#TODO default for dictionary
def extract_precipitation(longitude, latitude, date_list, folder):
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


def generate_date_list(start, end):
        if (type(start) and type (end)) == str:
            sdate = datetime.strptime(start,'%Y-%m-%d').date()
            edate = datetime.strptime(end,'%Y-%m-%d').date()
        
        else:
            sdate = start
            edate = end

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

    print(weekly_dict)
    return weekly_dict


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


def monthly_precipitation(dictionary):
    df = pd.DataFrame(list(dictionary.items()), columns=['Date', 'Precipitation'])
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
    dictionary['Date'] = pd.to_datetime(dictionary['Date'])
    dictionary.set_index('Date', inplace=True)

    if 'Precipitation' in dictionary:
        # Resample the data by year and calculate the mean
        yearly_precipitation = dictionary['Precipitation'].resample('Y').mean()

    else: 
        print('Error: Precipitation field not found in the dictionary')
        sys.exit(1)

    return yearly_precipitation


def map_precipitation(precipitation_series, lo, la, date):
    '''
    Example of global precipitations given by Nasa at: https://gpm.nasa.gov/data/tutorials
    '''  
    if type(precipitation_series) == pd.DataFrame:
        precip = precipitation_series.get('Precipitation')[0][0]

    elif type(precipitation_series) == dict:
        precip = precipitation_series[date[0].strftime('%Y-%m-%d')]
        
    precip = np.flip(precip.transpose(), axis=0)

    plt.imshow(precip, vmin=0, vmax=precip.max(), extent=[lo[0],lo[1],la[0],la[1]])
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


if workDir in os.environ:
    work_dir = os.getenv(workDir) + '/' + 'gpm_data'

else:
    work_dir = os.getenv('HOME') + '/gpm_data'

###################### TEST ##########################
# lo, la = adapt_coordinates([(-93.680)+1,(-87.4981)-1], [(-3.113)+1, (3.353)-1])
lo, la = adapt_coordinates([92.05, 92.05], [0.05, 0.05])
date_list = generate_date_list('2000-06-01', '2000-06-30')
prova = extract_precipitation(lo, la, date_list, work_dir)

prova = monthly_precipitation(prova)

bar_plot(prova, la, lo)


sys.exit(1)

#################### END TEST ########################

if __name__ == "__main__":
    parser = create_parser()
    inps = parser.parse_args()

    if inps.download:
        dload_site_list(work_dir, generate_date_list(inps.download[0], inps.download[1]))
        crontab_volcano_json(work_dir + '/' + jsonVolcano)  # TODO modify path

    else:
        if inps.plot_daily:
            lo, la = adapt_coordinates(inps.plot_daily[1], inps.plot_daily[0])
            start_date = inps.plot_daily[2]
            end_date = inps.plot_daily[3]

        elif inps.plot_weekly:
            lo , la = adapt_coordinates(inps.plot_weekly[1], inps.plot_weekly[0])
            start_date = inps.plot_weekly[2]
            end_date = inps.plot_weekly[3]

        elif inps.plot_monthly:
            lo, la = adapt_coordinates(inps.plot_monthly[1], inps.plot_monthly[0])
            start_date = inps.plot_monthly[2]
            end_date = inps.plot_monthly[3]

        elif inps.volcano_daily:
            eruption_dates, date_list, lon_lat = extract_volcanoes_info(work_dir + '/' + jsonVolcano, inps.volcano_daily[0])
            lo,la = adapt_coordinates(lon_lat[0], lon_lat[1])

            dload_site_list(work_dir, date_list)
            prec = plot_precipitaion_nc4(lo, la, date_list, work_dir)
            plt = daily_precipitation(prec, la, lo, volcano=inps.volcano_daily[0])
            plot_eruptions(eruption_dates)
            plt.show()
            sys.exit(0)

        elif inps.list:
            volcanoes_list(work_dir + '/' + jsonVolcano)
            sys.exit(0)
        #TODO restructure the code
        elif inps.map:
            map_precipitation(work_dir, inps.map[0])
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