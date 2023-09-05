from datetime import datetime
import logging
import logging.handlers
import os


class Logger:
    @staticmethod
    def init_logger():
        handler = logging.handlers.WatchedFileHandler(
        os.environ.get("LOGFILE", "command_automator.log"))
        formatter =logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)

    @staticmethod
    def print_log(message_to_print):
        logging.log(logging.DEBUG, message_to_print)

    @staticmethod
    def print_error_message(message_to_print, err):
        logging.log(logging.ERROR, message_to_print, err)