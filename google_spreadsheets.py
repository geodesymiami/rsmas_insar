import requests
import pandas as pd
import os

def get_google_spreadsheet_as_string(url_id, output_type="csv"):
    response = requests.get('https://docs.google.com/spreadsheet/ccc?key=' + url_id + '&output=' + output_type)
    response.raise_for_status()
    return response.content

def write_file(content, output_file_location = None):
    name = "templateExample.csv"
    if output_file_location != None:
        name = os.path.join(output_file_location, name)
    with open(name, 'wb') as f:
        f.write(content)
    return name

def get_google_spreadsheet_as_dataframe(url_id, output_file_location, output_type = "csv"):
    content = get_google_spreadsheet_as_string(url_id, output_type)
    loc = write_file(content, output_file_location)
    df = pd.read_csv(loc)
    return df

if __name__ == "__main__":
    url_id = "1Mvxf-O1NV-TJK9Ax7vWTvZ8q9jWx-GQD4y5WGgTOcMc"
    print(get_google_spreadsheet_as_dataframe(url_id, "output"))
