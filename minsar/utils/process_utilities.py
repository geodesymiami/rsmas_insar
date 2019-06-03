#! /usr/bin/env python3
###############################################################################
#
# Project: Utilities for process_rsmas.py
# Author: Falk Amelung and Sara Mirzaee
# Created: 10/2018
#
###############################################################################

from __future__ import print_function
import os
import glob
import subprocess
import configparser
from natsort import natsorted
import xml.etree.ElementTree as ET
import shutil
from mintpy.defaults.auto_path import autoPath
from minsar.objects.rsmas_logging import RsmasLogger, loglevel
from minsar.objects.dataset_template import Template
from minsar.objects.auto_defaults import PathFind

###############################################################################
pathObj = PathFind()
logfile_name = pathObj.logdir + '/process_rsmas.log'
logger = RsmasLogger(file_name=logfile_name)

##########################################################################


def send_logger():
    return logger

##########################################################################


def remove_directories(directories_to_delete):
    """ Removes given existing directories. """

    for directory in directories_to_delete:
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    return None


##########################################################################


def get_project_name(custom_template_file):
    """ Restores project name from custom template file. """

    project_name = None
    if custom_template_file:
        project_name = os.path.splitext(
            os.path.basename(custom_template_file))[0]
    return project_name


##########################################################################


def get_work_directory(work_dir, project_name):
    """ Sets the working directory under project name. """

    if not work_dir:
        if autoPath and 'SCRATCHDIR' in os.environ and project_name:
            work_dir = os.getenv('SCRATCHDIR') + '/' + project_name
        else:
            work_dir = os.getcwd()
    work_dir = os.path.abspath(work_dir)

    return work_dir


##########################################################################


def create_or_update_template(inps_dict):
    """ Creates a default template file and/or updates it.
        returns the values in 'inps'
    """

    inps = inps_dict

    print('\n*************** Template Options ****************')
    # write default template

    print ("Custom Template File: ", inps.customTemplateFile)

    inps.project_name = get_project_name(inps.customTemplateFile)
    print ("Project Name: ", inps.project_name)

    inps.work_dir = get_work_directory(None, inps.project_name)
    print("Work Dir: ", inps.work_dir)

    # Creates default Template
    inps = create_default_template(inps)


    return inps

#########################################################################


def create_default_template(temp_inps):
    """
    :param temp_inps: input parsed arguments
    :return Updated template file added to temp_inps.
    """

    inps = temp_inps

    inps.customTemplateFile = os.path.abspath(inps.customTemplateFile)

    inps.template_file = os.path.join(inps.work_dir, os.path.basename(inps.customTemplateFile))
    
    # read custom template from file
    custom_tempObj = Template(os.path.abspath(inps.customTemplateFile))

    # check for required options
    required_template_keys = pathObj.required_template_options

    for template_key in required_template_keys:
        if not template_key in custom_tempObj.options:
            logger.log(loglevel.ERROR, '{} is required'.format(template_key))
            raise Exception('ERROR: {0} is required'.format(template_key))

    # find default values from template_defaults.cfg to assign to default_tempObj
    default_tempObj = Template(pathObj.auto_template)
    config_template = get_config_defaults(config_file='template_defaults.cfg')
    for each_section in config_template.sections():
        for (each_key, each_val) in config_template.items(each_section):
            default_tempObj.options.update({each_key: os.path.expandvars(each_val.strip("'"))})

    inps.template = default_tempObj.options

    pathObj.set_isce_defaults(inps)

    # update default_temObj with custom_tempObj
    for key, value in custom_tempObj.options.items():
        if not value in [None, 'auto']:
            inps.template.update({key: os.path.expandvars(value.strip("'"))})

    if os.path.exists(inps.template_file):
        if not os.path.samefile(inps.customTemplateFile, inps.template_file):
            print('generate template file: {}'.format(inps.template_file))
            shutil.copyfile(inps.customTemplateFile, inps.template_file)
        else:
            print('template file exists: {}'.format(inps.template_file))
    else:
        print('generate template file: {}'.format(inps.template_file))
        shutil.copyfile(inps.customTemplateFile, inps.template_file)

    # updates tempDefault dictionary with the given templateObj adding new keys
    new_file = update_template_file(inps.template_file, custom_tempObj)
    with open(inps.template_file, 'w') as file:
        file.write(new_file)

    inps.cropbox = pathObj.grab_cropbox(inps)

    # build ssaraopt string from ssara options
    custom_tempObj.options.update(pathObj.correct_for_ssara_date_format(custom_tempObj.options))
    inps.ssaraopt = custom_tempObj.generate_ssaraopt_string()

    return inps

#########################################################################


def update_template_file(TEMP_FILE, custom_templateObj):
    """
    updates final template file in project directory based on custom template file
    :param TEMP_FILE: file to be updated
    :param custom_templateObj: custom template having extra or new options
    :return: updated file text
    """

    # fileText = TEMP_FILE
    with open(TEMP_FILE, 'r') as file:
        fileText = file.read()

    tempObj = Template(TEMP_FILE)

    for key, value in custom_templateObj.options.items():
        if not key in tempObj.options:
            fileText = fileText + "{:<38}".format(key) + "{:<15}".format("= {}".format(value.strip("'"))) + '\n'

    return fileText

##########################################################################


def get_config_defaults(config_file='job_defaults.cfg'):
    """ Sets an optimized memory value for each job. """

    config_dir = pathObj.defaultdir
    config_file = os.path.join(config_dir, config_file)
    if not os.path.isfile(config_file):
        raise ValueError('job config file NOT found, it should be: {}'.format(config_file))

    config = configparser.ConfigParser(delimiters='=')
    config.optionxform = str
    config.read(config_file)

    return config


##########################################################################


def run_or_skip(custom_template_file):
    """ Checks if the custom template file exists. """

    if os.path.isfile(custom_template_file):
        if os.access(custom_template_file, os.R_OK):
            return 'run'
    else:
        return 'skip'

##########################################################################


def raise_exception_if_job_exited(run_file):
    """Removes files with zero size or zero length (*.e files in run_files)."""
    
    files = glob.glob(run_file + '*.o')

    # need to add for PBS. search_string='Terminated'
    search_string = 'Exited with exit code'
    
    files = natsorted(files)
    for file in files:
        with open(file) as fr:
            if search_string in fr.read(): 
               raise Exception("ERROR: {0}/{1} exited,  contains: {2}".format(run_file, os.path.basename(file), search_string))
        # FA 5/2019: attempt to generate more meaningful exut messages. Did not work
        #with open(file, 'r') as efile:
        #    for line in efile.readlines():
        #        if search_string in line: 
        #           raise Exception("ERROR: {0}/{1} exited,  contains: \n  {2}".format(run_file, os.path.basename(file), line))


##########################################################################


def concatenate_error_files(run_file):
    """
    Concatenate error files to one file (*.e files in run_files).
    :param directory: str
    :param out_name: str
    :return: None
    """

    out_name = os.path.dirname(run_file) + '/out_' + run_file.split('/')[-1] + '.e'
    error_files = glob.glob(run_file + '*.e')
    if not len(error_files) == 0:
        with open(out_name, 'w') as outfile:
            for fname in error_files:
                outfile.write('#########################\n')
                outfile.write('#### ' + fname + ' \n')
                outfile.write('#########################\n')
                with open(fname) as infile:
                    outfile.write(infile.read())
                os.remove(fname)

        out_folder = os.path.dirname(run_file) + '/stderr_' + os.path.basename(run_file)

        if not os.path.exists(out_folder):
            os.mkdir(out_folder)
        else:
            shutil.rmtree(out_folder)
            os.mkdir(out_folder)

        shutil.move(out_name, out_folder)
    return None

###############################################################################


def file_len(fname):
    """Calculate the number of lines in a file."""
    with open(fname, 'r') as file:
        return len(file.readlines())

##########################################################################


def remove_zero_size_or_length_error_files(run_file):
    """Removes files with zero size or zero length (*.e files in run_files)."""

    error_files = glob.glob(run_file + '*.e')
    error_files = natsorted(error_files)
    for item in error_files:
        if os.path.getsize(item) == 0:       # remove zero-size files
            os.remove(item)
        elif file_len(item) == 0:
            os.remove(item)                  # remove zero-line files
    return None

##########################################################################


def remove_last_job_running_products(run_file):
    error_files = glob.glob(run_file + '*.e')
    job_files = glob.glob(run_file + '*.job')
    out_file = glob.glob(run_file + '*.o')
    list_files = error_files + out_file + job_files
    if not len(list_files) == 0:
        for item in list_files:
            os.remove(item)
    return

##########################################################################


def move_out_job_files_to_stdout(run_file):
    """move the error file into stdout_files directory"""

    job_files = glob.glob(run_file + '*.job')
    stdout_files = glob.glob(run_file + '*.o')
    dir_name = os.path.dirname(stdout_files[0])
    out_folder = dir_name + '/stdout_' + os.path.basename(run_file)
    if not os.path.isdir(out_folder):
        os.mkdir(out_folder)
    else:
        shutil.rmtree(out_folder)
        os.mkdir(out_folder)

    for item in stdout_files:
        shutil.move(item, out_folder)
    for item in job_files:
        shutil.move(item, out_folder)

    return None

############################################################################


def make_run_list(work_dir):
    """ exports run files to a list: run_file_list. """

    run_list = glob.glob(os.path.join(work_dir, pathObj.rundir) + '/run_*')
    run_test = glob.glob(os.path.join(work_dir, pathObj.rundir) + '/run_*')
    for item in run_test:
        test = item.split('/')[-1]
        if test.endswith('.e') or test.endswith('.o') or test.endswith('.job'):
            run_list.remove(item)
    run_list = natsorted(run_list)
    return run_list

############################################################################


def read_run_list(work_dir):
    """ reads from run_file_list. """

    runfiles = os.path.join(work_dir, 'run_files_list')
    run_file_list = []
    with open(runfiles, 'r') as f:
        new_f = f.readlines()
    for line in new_f:
        run_file_list.append(work_dir + '/run_files/' + line.split('/')[-1][:-1])

    return run_file_list

############################################################################


def xmlread(filename):
    """ Reads attributes from isce xml file """

    tree = ET.parse(filename)
    root = tree.getroot()
    value_node_spacecraft = None
    value_node_passdir = None
    node_component = root.find('component')
    for node in node_component:
        if node.get('name') == 'mission':              # mission=S1 or spacecraftname=Sentinel-1
            value_node_spacecraft = node.find('value')

    node_bursts = node_component.find('component')
    for node in node_bursts:
        if node.get('name') in ['burst1', 'burst2', 'burst3']:
            for property in node:
                if property.get('name') == 'passdirection':
                    value_node_passdir = property.find('value')

    if value_node_passdir.text == 'DESCENDING':
        passdirection = 'Desc'
    else:
        passdirection = 'Asc'

    attrdict = {'missionname': value_node_spacecraft.text, 'passdirection': passdirection}

    return attrdict

############################################################################


def walltime_adjust(inps, default_time):
    """ calculates the number of bursts based on boundingBox and returns an adjusting factor for walltimes """

    from minsar.objects.sentinel1_override import Sentinel1_burst_count

    inps_dict = inps
    pathObj.correct_for_isce_naming_convention(inps_dict)

    if inps_dict.swath_num is None:
        swaths = [1, 2, 3]
    else:
        swaths = [int(i) for i in inps_dict.swath_num.split()]

    number_of_bursts = 0

    for swath in swaths:
        obj = Sentinel1_burst_count()
        obj.configure()
        number_of_bursts = number_of_bursts + obj.get_burst_num(inps_dict, swath)

    default_time_hour = default_time.split(':')[0] + default_time.split(':')[1] / 60
    hour = (default_time_hour * number_of_bursts)/60
    minutes = np.remainder((default_time_hour * number_of_bursts), 60)
    adjusted_time = '{:02d}:{:02d}'.format(hour, minutes)

    return adjusted_time


############################################################################


