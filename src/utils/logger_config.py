import logging
import logging.handlers
import os
import sys

def setup_logging():
    """
    Configures the root logger for the application with UTF-8 encoding.

    Sets up a file handler that watches for external log rotation and uses environment variables
    for the log file path and log level. Ensures UTF-8 encoding for log files and console output.
    """   
    # Force UTF-8 encoding for stdout/stderr on Windows
    if sys.platform.startswith('win'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except (AttributeError, ValueError):
            # stdout/stderr may not support reconfigure in some environments
            pass
    log_file = os.environ.get("LOGFILE", "commands_automator.log")
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_level_str = os.environ.get("LOGLEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_str, logging.DEBUG)

    # Create file handler with UTF-8 encoding
    handler = logging.handlers.WatchedFileHandler(
        filename=log_file,
        encoding='utf-8',
        errors='replace'  # Handle any invalid UTF-8 characters
    )

    # Create console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter for both handlers
    formatter = logging.Formatter(
        "%(asctime)s: %(name)s: %(levelname)s {%(module)s.%(funcName)s}: %(message)s"
    )
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root = logging.getLogger()
    # Clear existing handlers to prevent duplicates
    if root.handlers:
        root.handlers.clear()
    root.setLevel(log_level)
    root.addHandler(handler)
    root.addHandler(console_handler)