import logging
from enum import Enum


class loglevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class RsmasLogger():

    def __init__(self, file_name=None):
        self.format = "%(asctime)s - %(levelname)s - %(message)s"
        self.console_handler = None
        self.file_handler = None
        self.logger = logging.getLogger()
        self.logfile_name = file_name

        self.logger.setLevel(logging.DEBUG)
        
        if len(self.logger.handlers) >= 0:
            self.set_format(self.format)

    def setup_filehandler(self, formatter):
        file_handler = logging.FileHandler(self.logfile_name, 'a+', encoding=None)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        return file_handler

    def setup_consolehandler(self, formatter):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        return console_handler

    def set_format(self, new_format):
        self.logger.removeHandler(self.console_handler)
        self.logger.removeHandler(self.file_handler)

        self.format = new_format
        formatter = logging.Formatter(self.format)

        self.file_handler = self.setup_filehandler(formatter)
        self.logger.addHandler(self.file_handler)
        
        streamHandlers = [h for h in self.logger.handlers if not isinstance(h, logging.FileHandler)]

        if len(streamHandlers) == 0:
            self.console_handler = self.setup_consolehandler(formatter)
        else:
            self.console_handler = streamHandlers[0]

        self.logger.addHandler(self.console_handler)

    def log(self, level=loglevel.INFO, message="", *args, **kwargs):
        if level is loglevel.DEBUG:
            self.logger.debug(message, *args, **kwargs)
        elif level is loglevel.INFO:
            self.logger.info(message, *args, **kwargs)
        elif level is loglevel.WARNING:
            self.logger.warning(message, *args, **kwargs)
        elif level is loglevel.ERROR:
            self.logger.error(message, *args, **kwargs)
        elif level is loglevel.CRITICAL:
            self.logger.critical(message, *args, **kwargs)
        else:
            raise ValueError("\nLevel should be one of the standard python logging error levels: "
                             "\nDEBUG"
                             "\nINFO"
                             "\nWARNING"
                             "\nERROR"
                             "\nCRITICAL")

# if __name__ == "__main__":
#
#     rsmas_logger = rsmas_logger(file_name="/Users/joshua/Desktop/test.log")
#
#     rsmas_logger.log(level=loglevel.INFO, message="Test")
#     rsmas_logger.log(level=loglevel.CRITICAL, message="Test")
#     rsmas_logger.log(level=loglevel.INFO, message="")
