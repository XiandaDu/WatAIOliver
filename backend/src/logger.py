import logging
import os
from logging.handlers import RotatingFileHandler


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logger() -> logging.Logger:
    """Return a configured logger for the application."""
    logger = logging.getLogger("wataioliver")
    logger.setLevel(LOG_LEVEL)
    
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    log_file = 'app.log'

    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=10)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.propagate = False
    return logger

logger = configure_logger()
