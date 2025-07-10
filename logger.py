from datetime import datetime
import logging
import logging.handlers
import os


class Logger:
    @staticmethod
    def init_logger():
        handler = logging.handlers.WatchedFileHandler(
        os.environ.get("LOGFILE", "commands_automator.log"))
        formatter =logging.Formatter("%(asctime)s:%(name)s:%(levelname)s {%(module)s %(funcName)s}:%(message)s")
        handler.setFormatter(formatter)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", "DEBUG"))
        root.addHandler(handler)
