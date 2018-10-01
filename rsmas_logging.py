import logging

class rsmas_logger():

    format = "%(levelname)s - %(message)s"
    console_handler, file_handler = None, None
    logfile_name = None
    logger = logging.getLogger()

    def __init__(self, console=True, file=None):

        self.logger.setLevel(logging.DEBUG)
        self.set_format(self.format)


    def setup_filehandler(self, formatter):
        file_handler = logging.FileHandler(self.logfile_name, 'a+', encoding=None)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        return file_handler

    def setup_consolehandler(self, formatter):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        return console_handler

    def set_format(self, new_format):

        if self.console_handler is not None:
            self.logger.removeHandler(self.console_handler)
        if self.file_handler is not None:
            self.logger.removeHandler(self.file_handler)

        self.format = new_format
        formatter = logging.Formatter(self.format)

        self.file_handler = self.setup_filehandler(formatter)
        self.console_handler = self.setup_consolehandler(formatter)

        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)