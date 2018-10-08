class Template:

    options = {}

    def __init__(self, template_file):
        self.options['dataset'] = template_file.split('/')[-1].split(".")[0]

        # Open files for reading
        with open(template_file) as template:

            for line in template:

                if "####################" not in line:
                    parts = line.split(" = ")
                    key = parts[0].rstrip()
                    value = parts[1].rstrip().split("#")[0].strip(" ")
                    self.options[str(key)] = value

    def get_options(self):
        return self.options

    def get_dataset_name(self):
        return self.options['dataset']