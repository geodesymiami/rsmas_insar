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

    def update_options(self, default_template_file):
        """ Update default template file with the options from custom template file read initially.
            
            :param default_template_file: file, the template file to be updated
        """
        
        template_file = os.path.abspath(default_template_file)
        default_options = self.read_options(template_file)
        
        tmp_file = template_file+'.tmp'
        with open(tmp_file, 'w') as f_tmp:
            for line in open(template_file, 'r'):
                c = [i.strip() for i in line.strip().split('=', 1)]
                if not line.startswith(('%', '#')) and len(c) > 1:
                    key = c[0]
                    value = str.replace(c[1], '\n', '').split("#")[0].strip()
                    if key in self.options.keys() and self.options[key] != value:
                        line = line.replace(value, self.options[key], 1)
                        default_options[key] = self.options[key]
                        print('    {}: {} --> {}'.format(key, value, self.options[key]))   
                f_tmp.write(line)
        mvCmd = 'mv {} {}'.format(tmp_file, template_file)
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
