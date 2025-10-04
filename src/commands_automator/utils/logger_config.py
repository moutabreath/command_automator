import logging
import logging.handlers
import os

def setup_logging():
    """
    Configures the root logger for the application.

    It sets up a file handler that rotates logs and uses environment variables
    for the log file path and log level, with sensible defaults.
    """
    log_file = os.environ.get("LOGFILE", "commands_automator.log")
    log_level = os.environ.get("LOGLEVEL", "DEBUG")

    handler = logging.handlers.WatchedFileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s: %(name)s: %(levelname)s {%(module)s.%(funcName)s}: %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)