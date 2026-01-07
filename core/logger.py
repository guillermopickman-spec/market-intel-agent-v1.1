import logging
import sys
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """
    Professional color-coded formatting for local development 
    and structured text for production.
    """
    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: blue + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        if log_fmt is None:
            log_fmt = self.format_str
        formatter = logging.Formatter(log_fmt, self.date_format)
        return formatter.format(record)

def get_logger(name: str):
    """
    Standardized logger factory.
    Ensures single-handler attachment to prevent duplicate logs.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(CustomFormatter())
        logger.addHandler(console_handler)
        logger.propagate = False

    return logger