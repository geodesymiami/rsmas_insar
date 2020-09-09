#!/usr/bin/env python3
# Sara Mirzaee

import os
import sys
import glob
import argparse
import xml.etree.ElementTree as etree
import shutil


class Sensors:
    def __init__(self, input_dir, output_dir, remove_file='False', multiple_raw_frame='False'):
        self.system_path = os.getenv('PATH')
        sys.path.append(os.path.join(os.getenv('ISCE_STACK'), 'stripmapStack'))
        from uncompressFile import uncompressfile
        self.uncompressfile = uncompressfile

        self.input_dir = input_dir
        self.output_dir = output_dir
        self.rmfile = remove_file
        self.sensor = None
        self.sensor_str = None

        if multiple_raw_frame == 'True':
            self.data_type = 'raw'
        else:
            self.data_type = 'slc'

        self.file_list = sorted(glob.glob(os.path.join(self.input_dir, '*.zip')) + \
                                glob.glob(os.path.join(self.input_dir, '*.tar')) + \
                                glob.glob(os.path.join(self.input_dir, '*.gz')))

        return

    def start(self):

        self.get_sensor_type()
        self.unpack()
        self.change_folder_names_to_date()
        unpack_runfile = self.create_run_unpack()

        return unpack_runfile

    def get_sensor_type(self):
        # search criteria for the different sensors
        ENV_str = 'ASA*'            # Envisat
        ERS_CEOS_str = 'ER*CEOS*'   # ERS in CEOS format
        ERS_ENV_str = 'ER*ESA*'     # ERS in Envisat format
        ALOS1_str = 'ALPSRP*'       # ALOS-1 Palsar, zip files and extracted files
        ALOS2_str = '00*ALOS2*'       # ALOS-2, zip files and extracted files
        CSK_str = 'EL*'             # CSK, zip files
        CSK_str2 = 'CSK*'           # CSK, zip files
        TSX_TDX_str = 'dims_op*'    # TSX zip files
        RSAT2_str = 'RS2*SLC*'      # RSAT2 zip files

        sensor_str_list = (ENV_str, ERS_CEOS_str, ERS_ENV_str, ALOS1_str, ALOS2_str, CSK_str, CSK_str2, TSX_TDX_str, RSAT2_str)
        sensor_list = ('Envisat', 'ERS_CEOS', 'ERS_ENV', 'ALOS1', 'ALOS2', 'CSK', 'CSK', 'TSX/TDX', 'RSAT2')

        # print('Supported sensors: ' + sensor_list[:])

        Sensors = dict(zip(sensor_str_list, sensor_list))

        sensor_found = False
        for sensor_str in Sensors:
            for file in glob.iglob(os.path.join(self.input_dir, '**', sensor_str), recursive=True):
                sensor_found = True
                sensor_str_keep = sensor_str
                if 'RAW' in os.path.basename(file):
                    self.data_type = 'raw'
                break

        # report back to user
        if sensor_found:
            print("Looks like " + Sensors[sensor_str_keep])
            self.sensor_str = sensor_str_keep
            self.sensor = Sensors[sensor_str_keep]
        else:
            print("Did not find the sensor automatically, unzip and run unpack routines manual")
            sys.exit(0)

        return

    def unpack(self):

        for in_file in self.file_list:
            workdir = os.path.dirname(in_file)
            out_folder = os.path.basename(in_file).split('.')[0]
            out_folder = os.path.join(workdir, out_folder)

            if os.path.isfile(in_file):
                # unzip the file in the outfolder
                successflag_unzip = self.uncompressfile(in_file, out_folder)

                # put failed files in a seperate directory
                if not successflag_unzip:
                    os.makedirs(os.path.join(workdir, 'FAILED_FILES'), exist_ok=True)
                    os.rename(in_file, os.path.join(workdir, 'FAILED_FILES', '.'))
                else:
                    # check if file needs to be removed or put in archive folder
                    if self.rmfile in [True, 'True']:
                        os.remove(in_file)
                        print('Deleting: ' + in_file)
                    else:
                        os.makedirs(os.path.join(workdir, 'ARCHIVED_FILES'), exist_ok=True)
                        cmd = 'mv ' + in_file + ' ' + os.path.join(workdir, 'ARCHIVED_FILES', '.')
                        os.system(cmd)

        # loop over the different folders and make sure the folder names are consistent.
        # this step is not needed unless the user has manually unzipped data before.
        image_folders = glob.glob(os.path.join(self.input_dir, self.sensor_str))
        for image_folder in image_folders:
            # in case the user has already unzipped some files
            # make sure they are unzipped similar like the uncompressfile code
            temp = os.path.basename(image_folder)
            parts = temp.split(".")
            image_outfolder_temp = parts[0]
            image_outfolder_temp = os.path.join(os.path.dirname(image_folder), image_outfolder_temp)

            # check if the folder (image_folder) has a different filename as generated from uncompressFile
            # (image_outfolder_temp):

            if not (image_outfolder_temp == image_folder):
                # it is different, check if the image_outfolder_temp already exists, if yes, delete the current folder
                if os.path.isdir(image_outfolder_temp):
                    print('Remove ' + image_folder + ' as ' + image_outfolder_temp + ' exists...')
                    # check if this folder already exist, if so overwrite it
                    shutil.rmtree(image_folder)

        return

    def change_folder_names_to_date(self):

        # loop over the different folders and organize in date folders
        image_folders = glob.glob(os.path.join(self.input_dir, self.sensor_str))
        for image_folder in image_folders:
            # get the date
            successflag, imgDate = self.get_date(image_folder)
            workdir = os.path.dirname(image_folder)

            if successflag:
                # move the file into the date folder
                SLC_dir = os.path.join(workdir, imgDate, '')
                os.makedirs(SLC_dir, exist_ok=True)

                # check if the folder already exist in that case overwrite it
                image_folder_out = os.path.join(SLC_dir, os.path.basename(image_folder))
                if os.path.isdir(image_folder_out):
                    shutil.rmtree(image_folder_out)
                # move the image acqusition folder in the date folder
                cmd = 'mv ' + image_folder + '/* ' + SLC_dir + '.'
                os.system(cmd)
                cmd = 'rmdir ' + image_folder
                os.system(cmd)

                print('changing folder name to date Succes: ' + imgDate)
            else:
                print('changing folder name to date Failed: ' + image_folder +
                      '\nSensor is not supported, do it manually')
        return

    def get_date(self, data_folder):

        if 'ALOS' in self.sensor:
            successflag, acquisitionDate = self.get_ALOS_date(data_folder)

        elif 'CSK' in self.sensor:
            successflag, acquisitionDate = self.get_CSK_date(data_folder)

        elif 'RSAT2' in self.sensor:
            successflag, acquisitionDate = self.get_RSAT_date(data_folder)

        elif 'TSX' in self.sensor:
            successflag, acquisitionDate = self.get_TSX_TDX_date(data_folder)

        else:
            successflag = False
            acquisitionDate = 'FAIL'

        return successflag, acquisitionDate

    def get_ALOS_date(self, ALOSfolder):

        # will search for different version of workreport to be compatible with ASf, WInSAR etc
        workreport_files = ('*workreport', 'summary.txt')
        for workreport_file in workreport_files:
            workreports = glob.glob(os.path.join(ALOSfolder, workreport_file))

            # if nothing is found return a failure
            if len(workreports) > 0:
                for workreport in workreports:
                    template_dict = {}
                    with open(workreport) as openfile:
                        for line in openfile:
                            c = line.split("=")
                            template_dict[c[0].strip()] = c[1].strip()
                    acquisitionDate = (str(template_dict['Img_SceneCenterDateTime'][1:9]))
                    if acquisitionDate:
                        successflag = True
                        return successflag, acquisitionDate

        # if it reached here it could not find the acqusiitionDate
        successflag = False
        acquisitionDate = 'FAIL'
        return successflag, acquisitionDate

    def get_CSK_date(self, CSKfolder):

        # will search for different version of workreport to be compatible with ASf, WInSAR etc
        CSKfile = glob.glob(os.path.join(CSKfolder, 'CSK*.h5'))
        # if nothing is found return a failure
        if len(CSKfile) > 0:
            CSKfile = os.path.basename(CSKfile[0])
            parts = CSKfile.split('_')
            if len(parts) > 8:
                if len(parts[8]) > 8:
                    acquisitionDate = parts[8]
                    acquisitionDate = acquisitionDate[0:8]
                    successflag = True
                    return successflag, acquisitionDate

        # if it reached here it could not find the acqusiitionDate
        successflag = False
        acquisitionDate = 'FAIL'
        return successflag, acquisitionDate

    def get_RSAT_date(self, RSAT2folder):

        # will search for different version of workreport to be compatible with ASf, WInSAR etc
        RSAT2file = glob.glob(os.path.join(RSAT2folder, 'product.xml'))
        # if nothing is found return a failure
        if len(RSAT2file) > 0:
            RSAT2file = RSAT2file[0]
            # loading the date information from the product.xml file
            tree = etree.parse(RSAT2file)
            root = tree.getroot()
            for attributes in root.iter('{http://www.rsi.ca/rs2/prod/xml/schemas}sourceAttributes'):
                # attribute_list = attributes.getchildren()
                attribute_list = List(attributes)
            for attribute in attribute_list:
                if attribute.tag == '{http://www.rsi.ca/rs2/prod/xml/schemas}rawDataStartTime':
                    date = attribute.text
                    UTC = date[11:16]
                    acquisitionDate = date[0:4] + date[5:7] + date[8:10]

            if len(acquisitionDate) == 8:
                successflag = True
                return successflag, acquisitionDate

        # if it reached here it could not find the acqusiitionDate
        successflag = False
        acquisitionDate = 'FAIL'
        return successflag, acquisitionDate

    def get_TSX_TDX_date(self, TXfolder):

        # will search for different version of workreport to be compatible with ASf, WInSAR etc
        try:
            TXfile = glob.glob(os.path.join(TXfolder, 'T*X-1.SAR.L1B/T*X*/T*X*.xml'), recursive=True)[0]

            if len(TXfile) > 0:
                acquisitionDate = TXfile.split('.')[-2].split('_')[-1]
                acquisitionDate = acquisitionDate[0:8]
                successflag = True
                return successflag, acquisitionDate
        except:
            # if it reached here it could not find the acqusiitionDate
            successflag = False
            acquisitionDate = 'FAIL'
            return successflag, acquisitionDate

    def create_run_unpack(self):

        script_path = os.path.join(os.getenv('ISCE_STACK'), 'stripmapStack')

        unpack_script = os.path.join(script_path, 'unpackFrame')

        sensor_list_affix = {'Envisat': 'ENV', 'ERS_CEOS': 'ERS', 'ERS_ENV': 'ERS', 'ALOS1': 'ALOS', 'ALOS2': 'ALOS2',
                             'CSK': 'CSK', 'TSX/TDX': 'TSX', 'RSAT2': 'RSAT2'}
        if self.sensor in sensor_list_affix.keys():
            unpack_script = unpack_script + '_{}'.format(sensor_list_affix[self.sensor])

        if self.data_type == 'raw':
            unpack_script = unpack_script + '_raw'

        unpack_script = unpack_script + '.py'

        # filename of the run file
        run_unPack = os.path.join(self.input_dir, 'run_0_unPack_raw')
        dateDirs = glob.glob(os.path.join(self.input_dir, '2*'))

        if self.output_dir is not None:
            f = open(run_unPack, 'w')
            for dateDir in dateDirs:
                acquisitionDate = os.path.basename(dateDir)
                slcDir = os.path.join(self.output_dir, acquisitionDate)
                os.makedirs(slcDir, exist_ok=True)
                cmd = unpack_script + ' -i ' + os.path.abspath(dateDir) + ' -o ' + slcDir
                print(cmd)
                f.write(cmd + '\n')
        return run_unPack
    
    def close(self):
        os.environ['PATH'] = self.system_path
