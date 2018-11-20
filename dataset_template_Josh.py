class Template:
    """ Template object encapsulates a dictionary of template options.
        Given a dataset.template file, this object creates a dictionary of options keyed on the option name. This
        will allow for accessing of various template parameters in constant time (as opposed to O(n) time) and includes
        a simple, user friendly syntax.
        Use as follows:
            template = Template(file_name)          # create a template object
            options = template.get_options()        # access the options dictionary
            dataset = options['dataset']            # access a specific option
    """

    def __init__(self, template_file):
        """ Initializes Template object with a template file.
            The provided template file is parsed line by line, and each option is added to the options dictionary.
            :param template_file: file, the template file to be accessed
        """

        # Crates the options dictionary and adds the dataset name as parsed from the filename
        # to the dictionary for easy lookup
        self.options = {'dataset': template_file.split('/')[-1].split(".")[0]}

        # Open files for reading
        with open(template_file) as template:

            for line in template:

                if  "=" in line:

                    # Splits each line on the ' = ' character string
                    # Note that the padding spaces are necessary in case of values having = in them
                    parts = line.split(" = ")
                    # The key should be the first portion of the split (stripped to remove whitespace padding)
                    key = parts[0].rstrip()

                    # The value should be the second portion (stripped to remove whitespace and ending comments)
                    value = parts[1].rstrip().split("#")[0].strip(" ")

                    # Add key and value to the dictionary
                    self.options[str(key)] = value

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
