#!/usr/bin/env python3
# Authors:  Falk Amelung
# This script creates an index.html file o display mintpy results.
############################################################
import os  
import sys
import argparse
import re
import fnmatch
from pdf2image import convert_from_path
from minsar.objects import message_rsmas
import minsar.utils.process_utilities as putils

EXAMPLE = """examples:
    create_html.py MaunaLoaSenDT87/mintpy_5_20/pic
    create_html.py unittestGalapagosSenDT128/miaplpy_SN_201606_201608/network_single_reference/pic
"""

DESCRIPTION = (
    "Creates index.html file to display images in the mintpy/pic folder."
)

def create_parser():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION, epilog=EXAMPLE,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "dir", type=str, help="mintpy/pic directory path"
    )
    inps = parser.parse_args()
    return inps
    
class Inps:
    def __init__(self, template_file):
        self.custom_template_file = template_file

def build_html(directory_path):
    print('DIRECTORY_PATH:', directory_path )    
    file_list = [file for file in os.listdir(directory_path) if file.lower().endswith(('.png', '.pdf','.template'))]
    png_files = [file for file in file_list if file.lower().endswith('.png')]
    pdf_files = [file for file in file_list if file.lower().endswith('.pdf')]
    template_files = [file for file in file_list if file.lower().endswith('.template')]

    os.chdir(directory_path)

    # Convert each PDF file to PNG
    for pdf_file in pdf_files:
        images = convert_from_path(pdf_file)
        for i, image in enumerate(images):
            # Get the base name of the PDF file without the extension
            base_name = os.path.splitext(os.path.basename(pdf_file))[0]
            # Add the .png extension
            png_file = f'{base_name}.png'
            image.save(png_file, 'PNG')

    # Check if there are any PNG files in the directory
    if not png_files:
        print("No PNG files found in the specified directory.")
        exit()

    # Define the preferred order of images
    preferred_order = ['geo_velocity.png', 'geo_temporalCoherence.png', 'geo_maskTempCoh.png', 'geo_avgSpatialCoh.png',
                    'network.png','coherenceHistory.png','coherenceMatrix.png','rms_timeseries*.png',
                    'temporalCoherence.png', 'maskTempCoh.png', 'avgSpatialCoh.png', 'maskConnComp.png',
                    'numTriNonzeroIntAmbiguity.png','numInvIfgram.png',
                    'velocity.png','geometryRadar.png',
                    'coherence_?.png', 'coherence_??.png',
                    'unwrapPhase_wrap_?.png','unwrapPhase_wrap_??.png',
                    'unwrapPhase_?.png', 'unwrapPhase_??.png',
                    'connectComponent_?.png', 'connectComponent_??.png',
                    'timeseries_*_wrap10_?.png', 'geo_timeseries_*_wrap10_?.png']
                    

    def sort_key(filename):
        for i, pattern in enumerate(preferred_order):
            if fnmatch.fnmatch(filename, pattern):
                # Extract the number from the filename
                match = re.search(r'\d+', filename)
                number = int(match.group()) if match else 0
                # Return a tuple with the index of the pattern and the number
                return (i, number)
        return (len(preferred_order), 0)

    png_files.sort(key=sort_key)

    # get project_name and network_type for header
    inps = Inps(directory_path + '/' + template_files[0])
    inps = putils.create_or_update_template(inps)
    try:
       network_type = inps.template['miaplpy.interferograms.networkType']
    except:
       network_type = 'single_reference'
    project_name = template_files[0].split('.')[0]

    # Create the HTML file with headers and image tags
    html_content = "<html><body>"
    html_content += f'  <h1>{project_name}</h1>\n'
    if 'miaplpy' in directory_path:
       html_content += f'  <h2>network: {network_type}</h2>\n'

    for png_file in png_files:
        header_tag = f'  <h2>{png_file}</h2>\n'
        img_tag = f'<a href="{png_file}"><img src="{png_file}" alt="{png_file}" width="500"></a><br>'
        html_content += header_tag + img_tag

    txt_file = 'reference_date.txt'
    header_tag = f'  <h2>{txt_file}</h2>\n'
    print('QQ cwd:', os.getcwd())
    with open(txt_file, 'r') as file:
        html_content += header_tag + '<pre>\n' + file.read() + '</pre>\n'

    for template_file in template_files:
        header_tag = f'  <h2>{template_file}</h2>\n'
        with open(template_file, 'r') as file:
            html_content += header_tag + '<pre>\n' + file.read() + '</pre>\n'

    # Close the HTML tags
    html_content += "</body></html>" + "\n"

    # Write the HTML content to a file without spaces
    html_file_path = os.path.join(directory_path, 'index.html')
    with open(html_file_path, 'w') as html_file:
        html_file.write(html_content)

    html_file_path = message_rsmas.insert_environment_variables_into_path( html_file_path )
    print(f"HTML file created: \n{html_file_path}")
    return None

def create_html(inps):
    
    if not os.path.isabs(inps.dir):
         inps.dir = os.getcwd() + '/' + inps.dir

    build_html(inps.dir)

    return None

