import os
import sys


class Template:
    """ Template object encapsulates a dictionary of template options.
        Given a dataset.template file, this object creates a dictionary of options keyed on the option name. This
        will allow for accessing of various template parameters in constant time (as opposed to O(n) time) and includes
        a simple, user friendly syntax.
        Use as follows:
            template = Template(file_name)                                  # create a template object
            options = template.get_options()                                # access the options dictionary
            dataset = options['dataset']                                    # access a specific option
            options = template.update_options_from_file(default_template_file)        # access a specific option
    """

    def __init__(self, custom_template_file):
        """ Initializes Template object with a custom template file.
            The provided template file is parsed line by line, and each option is added to the options dictionary.
            :param custom_template_file: file, the template file to be accessed
        """

        self.options = self.read_options(custom_template_file)
        self.options = correct_keyvalue_quotes(self.options.copy())

    def read_options(self, template_file):
        """ Read template options.

            :param template_file: file, the template file to be read and stored in a dictionary
        """
        # Creates the options dictionary and adds the dataset name as parsed from the filename
        # to the dictionary for easy lookup

        options = {'dataset': template_file.split('/')[-1].split(".")[0]}
        with open(template_file) as template:
            for line in template:
                if "=" in line and not line.startswith(('%', '#')):
                    # Splits each line on the ' = ' character string
                    # Note that the padding spaces are necessary in case of values having = in them
                    parts = line.split(" = ")

                    # The key should be the first portion of the split (stripped to remove whitespace padding)
                    key = parts[0].rstrip()

                    # The value should be the second portion (stripped to remove whitespace and ending comments)
                    value = parts[1].rstrip().split("#")[0].strip(" ")

                    # Add key and value to the dictionary
                    options[str(key)] = value

        return options

    def update_options(self, default_template_file_tmp):
        """ Update default template file with the options from custom template file read initially.

            :param default_template_file: file, the template file to be updated
        """

        default_template_file = os.path.abspath(default_template_file_tmp)
        default_options = self.read_options(default_template_file)

        tmp_file = default_template_file+'.tmp'
        with open(tmp_file, 'w') as f_tmp:
            for line in open(default_template_file, 'r'):
                c = [i.strip() for i in line.strip().split('=', 1)]
                if not line.startswith(('%', '#')) and len(c) > 1:
                    key = c[0]
                    #print('Checking from default_template: '+ key)
                    value = str.replace(c[1], '\n', '').split("#")[0].strip()
                    if key in self.options.keys() and self.options[key] != value:
                        line = line.replace(value, self.options[key], 1)
                        default_options[key] = self.options[key]
                        print('From custom_template {}: {} --> {}'.format(key, value, self.options[key]))

                f_tmp.write(line)
        mvCmd = 'mv {} {}'.format(tmp_file, default_template_file)
        os.system(mvCmd)
        self.options = default_options
        return self.options

    def update_option(self, key, value):
        """ Updates the options dictionary key with the specified value.
            :param key   : the dictionary key to update
            :param value : the value to replace the key with
        """
        options = self.get_options()
        options[key] = value

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

        # Determines if the required ssaraopt keys are present in the template files and either
        # utilizes the general ssaraopt option or throws an exception
        # (likely an invalid template file in that case).

        ssaraopt_keys = ['ssaraopt.platform', 'ssaraopt.relativeOrbit']

        bad_key = False
        for key in ssaraopt_keys:
            if key not in self.options:
                bad_key = True
                if 'ssaraopt' in self.options:
                    ssaraopt = self.options['ssaraopt']
                else:
                    raise Exception('no ssaraopt or ssaraopt.platform, relativeOrbit found')

        # If all of the keys are present go ahead and generate the ssaraopt string as normal.
        if not bad_key:
            platform = self.options['ssaraopt.platform']
            relativeOrbit = self.options['ssaraopt.relativeOrbit']
            ssaraopt = '--platform={} --relativeOrbit={}'.format(platform, relativeOrbit)
            if 'ssaraopt.frame' in self.options.keys():
                frame = self.options['ssaraopt.frame']
                ssaraopt += ' --frame={}'.format(frame)
            if 'ssaraopt.startDate' in self.options:
                startDate = self.options['ssaraopt.startDate']
                ssaraopt += ' -s={}'.format(startDate)
            if 'ssaraopt.endDate' in self.options:
                endDate = self.options['ssaraopt.endDate']
                ssaraopt += ' -e={}'.format(endDate)
            if 'ssaraopt.parallel' in self.options:
                parallel = self.options['ssaraopt.parallel']
            else:
                 parallel = 30
            ssaraopt += ' --parallel={}'.format(parallel)

            #this was in Josh's code (above yje ssaraopt assignment) but unclear  what it does
            #parallel_download = self.options.get("ssaraopt.parallelDownload", '30')

        return ssaraopt

def correct_keyvalue_quotes(options_in):
         """ quote-independent reformatting of sentinel.subswath key-value:
                 1 2 ---> '1 2'
                 1  ---> 1
                '1' ---> 1
                -1 0.15 -91.6 -90.9 ---> '-1 0.15 -91.6 -90.9'
         """
         for item in ['topsStack.subswath', 'topsStack.boundingBox']:
             if item in options_in.keys():
                 value_orig = options_in[item]
                 value_new = check_correct_quotes(value_orig)
                 options_in[item] = value_new
                 print(value_orig + '-->' + value_new)
         return options_in


def check_correct_quotes(string):
         """ checks weather quotes are as required and corrects/replaces if needed
         """

         if string[0:1] == '\'':
            num_item = string.split(' ')
            if len(num_item) == 1:
                out_string = string[1:2]
            else:
                out_string = string
         else:
            num_item = string.split(' ')
            if len(num_item) >= 2:
                out_string = '\'' + string + '\''
            else:
                out_string = string
         return out_string
