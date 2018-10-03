import logging

class rsmas_logger():

    format = "%(levelname)s - %(message)s"
    console_handler, file_handler = None, None
    logfile_name = None
    logger = logging.getLogger()

    def __init__(self, console=True, file=None):

        self.logfile_name = file

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

    def log(self, level=logging.INFO, message="", *args, **kwargs):
        if level is logging.DEBUG:
            self.logger.debug(message, *args, **kwargs)
        elif level is logging.INFO:
            self.logger.info(message, *args, **kwargs)
        elif level is logging.WARNING:
            self.logger.warning(message, *args, **kwargs)
        elif level is logging.ERROR:
            self.logger.error(message, *args, **kwargs)
        elif level is logging.CRITICAL:
            self.logger.critical(message, *args, **kwargs)
        else:
            raise ValueError("\nLevel should be one of the standard python logging error levels: "
                             "\nDEBUG"
                             "\nINFO"
                             "\nWARNING"
                             "\nERROR"
                             "\nCRITICAL")

if __name__ == "__main__":

    rsmas_logger = rsmas_logger(file="/Users/joshua/Desktop/test.log")

    rsmas_logger.log(level=logging.INFO, message="Test")
    rsmas_logger.log(level=logging.CRITICAL, message="Test")
    rsmas_logger.log(level="", message="")