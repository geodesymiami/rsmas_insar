#!/usr/bin/env python2

import os
import pandas as pd
import sys
import requests
import argparse
import time
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

std_formatter = logging.Formatter("%(levelname)s - %(message)s")

general = logging.FileHandler(os.getenv('OPERATIONS')+'/LOGS/generate_templates.log', 'a+', encoding=None)
general.setLevel(logging.INFO)
general.setFormatter(std_formatter)
logger.addHandler(general)


inps = None
date_format = "%Y-%m-%dT%H:%M:%S.%f"

def cmdLineParse(argv):
    global inps
    parser = argparse.ArgumentParser(description='Generate Processing Template Files', 
                                     formatter_class=argparse.RawTextHelpFormatter, 
                                     epilog=None)

    ##### Input
    infile = parser.add_argument_group('File to Generate', 'File to Generate')
    infile.add_argument("--dataset", dest='dataset', metavar="DATASET", help='Particular dataset to generate template for')
    infile.add_argument('--csv', dest='csv', metavar='FILE', help='CSV file containing template data')
    infile.add_argument('--output-dir', dest='output', metavar='FILE', help='directory to output template files to')
    infile.add_argument('--testsheet', dest='test_sheet', action='store_true',  help='use test sheet or not')

    inps = parser.parse_args(argv)
    return inps


#########################################################

def get_google_spreadsheet_as_string(url_id, output_type="csv"):
    
    response = requests.get('https://docs.google.com/spreadsheets/d/' + url_id + '/export?format=' + output_type)
    response.raise_for_status()
    return response.content


def write_file(content, output_file_location = None):
    name = "templateRSMAS.csv"
    if output_file_location is not None:
        name = os.path.join(output_file_location, name)
    with open(name, 'wb') as f:
        f.write(content)
    return name


def get_google_spreadsheet_as_dataframe(url_id, output_file_location, output_type = "csv"):
    content = get_google_spreadsheet_as_string(url_id, output_type)
    loc = write_file(content, output_file_location)
    df = pd.read_csv(loc)
    return df


def get_spreadsheet_as_dataframe(file, output_file_location, output_type = "csv"):
    file_end = file[len(file)-4:len(file)]
    if file_end in ['.csv']:
        df = pd.read_csv(file)
    else:
        df = get_google_spreadsheet_as_dataframe(file, output_file_location, output_type)
    return df



##########################################################


def generate_template_file(names, subnames, column_vals, comments):
    line_breaker = "#"*20 + "\n"
    output_file = ""
    last_named_column = ""
    base = ""

    if column_vals[0] == "FALSE":
        return None;

    for i in range(len(names)):

        # Get set base name.
        if type(names[i]) != str:
            base = last_named_column
            if type(subnames[i]) != str:
                output_file += line_breaker
        else:
            # New Column
            base = names[i]
            last_named_column = base

        # Get subname
        if type(subnames[i]) == str:
            subname = "." + subnames[i]
        else:
            subname = ""

        # Get Value
        if type(column_vals[i]) ==  str:
            value = column_vals[i]
        else:
            continue

        comments_string = "";
        # Need to create name in order to format string properly so that the "=" symbol is at the same location
        if type(comments[i]) == str:
            comments_string = comments[i]
        name = base + subname
        output_line = "{0:35} = {1:50}{2:50}\n".format(name, value, comments_string)
        output_file += output_line
    return output_file


def generate_template_files(df):
    names = list(df["Name"])
    subnames = list(df["Subname"])
    columns = list(df.columns)
    output_files = {}

    if inps.dataset is not None:
        file_base = inps.dataset
        output_files[file_base] = generate_template_file(names, subnames, list(df[inps.dataset]), list(df['Comments']))
    else:
        for i, col_name in enumerate(columns[2:]):
            if "Unnamed" in col_name or "Comments" in col_name:
                continue;
            file_base = col_name
            output_files[file_base] = generate_template_file(names, subnames, list(df[col_name]), list(df['Comments']))
    return output_files


def generate_and_save_template_files(df, output_location):
    # Create output directory if it doesn't exist
    if not os.path.isdir(output_location):
        os.mkdir(output_location)

    files_to_save = generate_template_files(df)
    
    logging.info("Template files being generated for: %s", str(files_to_save))

    for key, value in files_to_save.items():
        # Print contents for debugging purposes
        if value == None:
            continue;

        with open(os.path.join(output_location, key + ".template"), "w") as f:
            f.write(value)


def generate_and_save_template_files_from_file(csv_file, output_location):
    df = pd.read_csv(csv_file)
    generate_and_save_template_files(df, output_location)


def generate_and_save_template_files_from_dataframe(df, output_location):
    generate_and_save_template_files(df, output_location)


def main(args):
    
    logger.info("GENERATING TEMPLATES ON %s\n", datetime.fromtimestamp(time.time()).strftime(date_format))
    
    inps = cmdLineParse(args)

    csv_file         = "1zAsa5cykv-WS39ufkCZdvFvaOem3Akol8aqzANnsdhE"
    test_sheet       = "1bDJQEfM_to-7-2N7_0PhKnD1ur484jkydcTFZGMdLcQ" #Old Original
    test_sheet       = "1ILNfg9jJsebxSQUZF2ULCBgAnDJ41NRc1X8j6xsZUUI" #test_templateRSMAS.csv
    test_sheet       = "1Q8isYbGtGLGBoeqIQffg-587K13MtrDoQTYnx_59fFE" #test1_templateRSMAS.csv (test1 4 datasets)
    output_location  = os.getenv('OPERATIONS') + '/TEMPLATES/'

    if inps.csv:
        csv_file = inps.csv
        
    if inps.test_sheet:
        csv_file = test_sheet

    if inps.output:
        output_location = inps.output

    df = get_spreadsheet_as_dataframe(csv_file, output_location)
    generate_and_save_template_files_from_dataframe(df, output_location)

# TODO: Properly name variables
# If output and input directories are declared, use them
if __name__ == "__main__":
    main(sys.argv[1:]);
