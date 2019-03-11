import os
import shutil

class Template:
    """ Template object encapsulates a dictionary of template options.

        Given a dataset.template file, this object creates a dictionary of options keyed on the option name. This
        will allow for accessing of various template parameters in constant time (as opposed to O(n) time) and includes
        a simple, user friendly syntax.

        Use as follows:

            template = Template(file_name)                                  # create a template object
            options = template.get_options()                                # access the options dictionary
            dataset = options['dataset']                                    # access a specific option
            options = template.update_options(default_template_file)        # access a specific option

    """
    
    def __init__(self, custom_template_file):
        """ Initializes Template object with a custom template file.

            The provided template file is parsed line by line, and each option is added to the options dictionary.

            :param custom_template_file: file, the template file to be accessed
        """
        # Joshua Zahner - 02/2019
        # What the hell are the following 6 lines even doing? This object should only be responsible for creating a
        # dictionary of options from a template not working with any types of file or moving files around.
        custom_template_file = os.path.abspath(custom_template_file)
        project_name = os.path.splitext(os.path.basename(custom_template_file))[0] # see `get_dataset_name`
        self.work_dir = os.getenv('SCRATCHDIR') + '/' + project_name
        template_file = os.path.join(self.work_dir, os.path.basename(custom_template_file))
        
        #if not self.os.path.isfile(template_file):       # FA 12/18: It should use custom_template_file as this is what will be updated
        #    self.shutil.copy2(custom_template_file, self.work_dir)
        shutil.copy2(custom_template_file, self.work_dir)
        self.options = self.read_options(template_file)
        
  
    def read_options(self,template_file):
        """ Read template options.
        
            :param template_file: file, the template file to be read and stored in a dictionary
            :return options     : dict, a dictionary of options as read from the template file
        """
        # Creates the options dictionary and adds the dataset name as parsed from the filename
        # to the dictionary for easy lookup
        options = {'dataset': template_file.split('/')[-1].split(".")[0]}
        with open(template_file) as template:
            for line in template:
                if "=" in line:
                    # Splits each line on the ' = ' character string
                    # Note that the padding spaces are necessary in case of values having = in them
                    parts = line.split(" = ")
                    print(parts)
                    # The key should be the first portion of the split (stripped to remove whitespace padding)
                    key = parts[0].rstrip()
                    
                    # The value should be the second portion (stripped to remove whitespace and ending comments)
                    value = parts[1].rstrip().split("#")[0].strip(" ")

                    # Add key and value to the dictionary
                    options[str(key)] = value
        return options

    def update_options_from_file(self, template_file):
        """ Updates the options dictionary with the contents of a new template file.

            :param template_file: file, the new template file to update self.options with
            :return options     : dict, updated options dictionary
        """
        with open(template_file) as template:
            for line in template:
                if "=" in line and line[0] != "#":
                    # Splits each line on the ' = ' character string
                    # Note that the padding spaces are necessary in case of values having = in them
                    parts = line.split(" = ")
                    print(parts)
                    # The key should be the first portion of the split (stripped to remove whitespace padding)
                    key = parts[0].rstrip()

                    # The value should be the second portion (stripped to remove whitespace and ending comments)
                    value = parts[1].rstrip().split("#")[0].strip(" ")
                    if key in self.options and self.options[key] != value:
                        self.update_option(key, value)

        return self.options

    def update_option(self, key, value):
        """ Updates a single option in the options dictionary.

            :param key      : string, the key to update
            :param value    : string, the value to update the key to
            :return options : dict, the updated options dictionary
        """
        options = self.get_options()
        options[key] = value

        return options
    
    def get_options(self):
        """ Provides direct access to the options dictionary.
            This should be used in lieu of directly accessing the options dictionary via Template().options
        """
        return self.options

    def get_dataset_name(self):
        """ Provides quick access to the dataset property of the options dictionary.
            Should be used to quickly access the dataset name when directories require the dataset name
        """
        return self.options['dataset']
    
    def generate_ssaraopt_string(self):
        """ Generates the ssaraopt string for ssara_federated_query.py command line calls from the options
            dictionary values.

        """

        # Determines if any of the ssaraopt keys are not present in the template files and either
        # utilizes the general ssaraopt option or throws an exception if that is also not present
        # (likely an invalid template file in that case).

        ssaraopt_keys = ['ssaraopt.platform', 'ssaraopt.relativeOrbit', 'ssaraopt.frame']

        bad_key = False
        for key in ssaraopt_keys:
            if key not in self.options:
                bad_key = True
                if 'ssaraopt' in self.options:
                    ssaraopt = self.options['ssaraopt']
                else:
                    raise Exception('no ssaraopt or ssaraopt.platform, relativeOrbit, frame found')

        # If all of the keys are present go ahead and generate the ssaraopt string as normal.
        if not bad_key:
            platform = self.options['ssaraopt.platform']
            relativeOrbit = self.options['ssaraopt.relativeOrbit']
            frame = self.options['ssaraopt.frame']
            ssaraopt = '--platform={} --relativeOrbit={} --frame={}'.format(platform, relativeOrbit, frame)
            if 'ssaraopt.startDate' in self.options:
                startDate = self.options['ssaraopt.startDate']
                ssaraopt += ' -s={}'.format(startDate)
            if 'ssaraopt.endDate' in self.options:
                endDate = self.options['ssaraopt.endDate']
                ssaraopt += ' -e={}'.format(endDate)

        parallel_download = self.options.get("ssaraopt.parallelDownload", '30')

        ssaraopt += ' --parallel={}'.format(parallel_download)

        return ssaraopt
