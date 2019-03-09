#!/usr/bin/env python3

import os
import pandas as pd
import sys
import requests
import argparse
import time
from datetime import datetime
from rsmas_logging import RsmasLogger, loglevel
from io import StringIO

logfile = os.getenv('OPERATIONS')+'/LOGS/generate_templates.log'
logger = RsmasLogger(logfile)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


def cmd_line_parse(argv):

    parser = argparse.ArgumentParser(description='Generate Processing Template Files', 
                                     formatter_class=argparse.RawTextHelpFormatter, 
                                     epilog=None)

    ##### Input
    infile = parser.add_argument_group('File to Generate', 'File to Generate')
    infile.add_argument("--dataset", dest='dataset', metavar="DATASET", help='Particular dataset to generate template for')
    infile.add_argument('--csv', dest='csv', metavar='FILE', help='CSV file containing template data')
    infile.add_argument('--output-dir', dest='output', metavar='FILE', help='directory to output template files to')
    infile.add_argument('--sheet_id', dest='sheet_id', metavar='SHEET ID',  help='sheet id to use')

    inps = parser.parse_args(argv)
    return inps


def get_google_spreadsheet_as_dataframe(url_id, output_file_location, output_type="csv"):
    """ Writes a google spreadsheet to a local csv file and loads it back as a pandas DataFrame object.

        :param url_id : string, the url ID of the spreadsheet to download
        :param output_file_location : string, the location to store the local file
        :param output_type : string, the type of file to download

        :return dataframe : pandas.DataFrame, a dataframe object representation of the file

    """

    if output_type != "csv":
        raise Exception("Unsupported output_type: " + str(output_type))

    url = "https://docs.google.com/spreadsheets/d/{}/export?format={}".format(url_id, output_type)

    response = requests.get(url)
    response.raise_for_status()

    name = "templateRSMAS.csv"
    if output_file_location is not None:
        name = os.path.join(output_file_location, name)
    with open(name, 'wb') as f:
        f.write(response.content)

    return pd.read_csv(name)


def get_spreadsheet_as_dataframe(file, output_file_location, output_type="csv"):
    """ Loads a local csv file as a pandas DataFrame object.

        :param file : string, the filename of the file to load
        :param output_file_location : string, location to store the output file
        :param output_type : string, the type of file `file` is

        :return dataframe: pandas.DataFrame, a dataframe object representation of the file

    """
    file_end = file[-4:]
    if file_end in ['.csv']:
        df = pd.read_csv(file)
    else:
        df = get_google_spreadsheet_as_dataframe(file, output_file_location, output_type)
    return df


def generate_template_file(names, subnames, column_vals, comments):
    """ Generate a single template file from data in the DataFrame object.

        :param names: List(string), list of primary key names provided in the file
        :param subnames: List(string), list of secondary key names provided in the file
        :param column_vals: List(string), list of data for each key for a given dataset
        :param comments: List(string), list of comments to include in the generated template file

        :return: output_file: string, the contentes of the template file as a string

    """

    line_breaker = "#"*20 + "\n"    # Formatted line break. Appears as ==> '####################' in file
    output_file = ""
    last_named_column = ""
    base = ""

    # If process_flag is FALSE, don't generate a template file for that dataset
    if column_vals[0] == "FALSE":
        return None

    for i in range(len(names)):

        # Get/set base name.
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
        if type(column_vals[i]) == str:
            value = column_vals[i]
        else:
            continue

        # Add comments to line if any exist
        comments_string = ""
        if type(comments[i]) == str:
            comments_string = comments[i]

        # Generate line
        name = base + subname
        output_line = "{0:35} = {1:50}{2:50}\n".format(name, value, comments_string)
        output_file += output_line

    return output_file


def generate_template_files(df, dataset):
    """ Generate template files for each dataset included in the spreadsheet.

        :param df: pandas.DataFrame, the DataFrame object representation of the CSV file
        :param dataset: str, The dataset name
        :return: output_files, List(string), list of string representations of the template files

    """

    names = list(df["Name"])
    subnames = list(df["Subname"])
    columns = list(df.columns)
    output_files = {}

    if dataset is not None:
        file_base = dataset
        output_files[file_base] = generate_template_file(names, subnames, list(df[dataset]), list(df['Comments']))
    else:
        for i, col_name in enumerate(columns[2:]):
            if "Unnamed" in col_name or "Comments" in col_name:
                continue
            file_base = col_name
            output_files[file_base] = generate_template_file(names, subnames, list(df[col_name]), list(df['Comments']))
    return output_files


def generate_and_save_template_files(df, output_location, dataset):
    """ Writes template files to disk locations

        :param df: pandas.DataFrame, the DataFrame object representation of the CSV file
        :param output_location: string, the file location of the output files
        :param dataset: str, The dataset name

    """

    # Create output directory if it doesn't exist
    if not os.path.isdir(output_location):
        os.mkdir(output_location)

    files_to_save = generate_template_files(df, dataset)
    
    logger.log(loglevel.INFO, "Template files being generated for: %s", str(files_to_save))

    for key, value in files_to_save.items():
        # Print contents for debugging purposes
        if value is None:
            continue

        filename = os.path.join(output_location, "{}.template".format(key))
        with open(filename, "w") as template_file:
            template_file.write(value)


def generate_and_save_template_files_from_dataframe(df, output_location, dataset):
    """ Generate and saves template files from a local dataframe object

        :param df: pandas.DataFrame, DataFrame object representation of the CSV file
        :param output_location: string, the location to write the output template files to
        :param dataset: str, The dataset name

    """
    generate_and_save_template_files(df, output_location, dataset)


def main(args):
    
    logger.log(loglevel.INFO, "Generating template files on {}\n".format(datetime.fromtimestamp(time.time()).strftime(DATE_FORMAT)))
    
    inps = cmd_line_parse(args)

    default_sheet = "1zAsa5cykv-WS39ufkCZdvFvaOem3Akol8aqzANnsdhE"
    test_sheet = "1Q8isYbGtGLGBoeqIQffg-587K13MtrDoQTYnx_59fFE"     #test1_templateRSMAS.csv (test1 4 datasets)
    output_location = os.getenv('OPERATIONS') + '/TEMPLATES/'

    csv_file = default_sheet

    if inps.csv:
        csv_file = inps.csv
    if inps.sheet_id:
        csv_file = inps.sheet_id
    if inps.output:
        output_location = inps.output

    df = get_spreadsheet_as_dataframe(csv_file, output_location)
    generate_and_save_template_files_from_dataframe(df, output_location, inps.dataset)

    logger.log(loglevel.INFO, "Finished generating template files")

# TODO: Properly name variables
# If output and input directories are declared, use them
if __name__ == "__main__":
    main(sys.argv[1:])
