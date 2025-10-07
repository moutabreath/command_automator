import logging
import logging.handlers
import os

def setup_logging():
    """
    Configures the root logger for the application.

    It sets up a file handler that watches for external log rotation and uses environment variables
    for the log file path and log level, with sensible defaults.
    """   

    log_file = os.environ.get("LOGFILE", "commands_automator.log")
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_level_str = os.environ.get("LOGLEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_str, logging.DEBUG)
    handler = logging.handlers.WatchedFileHandler(log_file)
    formatter = logging.Formatter("%(asctime)s: %(name)s: %(levelname)s {%(module)s.%(funcName)s}: %(message)s")
    handler.setFormatter(formatter)
    root = logging.getLogger()
    # Clear existing handlers to prevent duplicates
    if root.handlers:
        root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(handler)