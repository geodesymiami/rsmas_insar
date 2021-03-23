#!/usr/bin/env python3

import argparse
import os
import subprocess

def add_common_parser(parser):
    p = parser.add_argument_group('General options:')
    p.add_argument('--all',             dest='all_services',     action='store_true', help='Check all services.')
    p.add_argument('--demServer',       dest='dem_server',       action='store_true', help='Check DEM server.')
    p.add_argument('--downloadASF',     dest='download_asf',     action='store_true', help='Check ASF download server.')
    p.add_argument('--jetstreamServer', dest='jetstream_server', action='store_true', help='Check jetstream server.')
    p.add_argument('--workdir',         dest='work_dir',         action='store_true', help='Check $WORK directory.')
    p.add_argument('--insarmaps',       dest='insarmaps',        action='store_true', help='Check insarmaps server.')
    return parser

def check_server_status(server_url, timeout=0.1, extra_options=[]):
    option_str = ' '.join(extra_options)
    command = "wget --spider {} --connect-timeout={} --tries=3 {} ".format(server_url, timeout, option_str)
    process = subprocess.run(command.split(), capture_output=True)
    output = str(process.stderr)

    online_string="200 OK"
    offline_string="failed"
    if online_string in str(output):
        return True
    elif offline_string in str(output):
        return False
    else:
        return "Unknown"

def is_service_online(command, extra_options=[]):

    timeout_vals=[0.1, 1, 5]
    speed=["(fast)", "(slow)", ""]

    online=False
    tries=0
    while online!=True and tries < 3:
        if "http" in command:
            online = check_server_status(command, timeout=timeout_vals[tries], extra_options=extra_options)
        else:
            command = command.format(timeout_vals[tries])
            process = subprocess.run(command.split(), capture_output=True)
            online = True if process.returncode == 0 else False
        tries += 1

    tries -=1
    return online, speed[tries]
        

def main(iargs=None):
    parser = argparse.ArgumentParser(description='check_services Parser')
    parser = add_common_parser(parser)
    inps = parser.parse_args(args=iargs)

    if inps.all_services:
        inps.dem_server = True
        inps.download_asf = True
        inps.jetstream_server = True
        inps.work_dir = True
        inps.insarmaps = True

    if inps.dem_server:
        online, speed = is_service_online("https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11") 
        #print("demServer is {} {}".format("ONLINE" if online else "OFFLINE", speed))
        print("{:31s} {:6s} {:4s}".format("demServer is", "ONLINE" if online else "OFFLINE", speed))

    if inps.download_asf:
        online, speed = is_service_online("https://web-services.unavco.org")
        print("{:31s} {:6s} {:4s}".format("downloadASF list service is", "ONLINE" if online else "OFFLINE", speed))
        online, speed = is_service_online("https://datapool.asf.alaska.edu/SLC/SA/S1A_IW_SLC__1SSV_20160605T114943_20160605T115018_011575_011AEF_98EA.zip") 
        print("{:31s} {:6s} {:4s}".format("downloadASF download service is", "ONLINE" if online else "OFFLINE", speed))

    if inps.jetstream_server:
        online, speed = is_service_online("http://centos@129.114.104.223", extra_options=["--no-check-certificate"])
        print("{:31s} {:6s} {:4s}".format("jetstream server is", "ONLINE" if online else "OFFLINE", speed))

    if inps.insarmaps:
        online, speed = is_service_online("http://insarmaps.miami.edu", extra_options=["--no-check-certificate"])
        print("{:31s} {:6s} {:4s}".format("insarmaps server is", "ONLINE" if online else "OFFLINE", speed))

    if inps.work_dir:
        workdir = os.environ['WORK']
        command = "timeout {} ls {}".format("{}", workdir)
        online, speed = is_service_online(command)
        print("{:31s} {:6s} {:4s}".format("$WORK is", "ONLINE" if online else "OFFLINE", speed))

    

if __name__ == "__main__":
    main()

