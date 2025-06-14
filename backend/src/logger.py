import logging
from logging.handlers import RotatingFileHandler


def configure_logger():
    # Set up a rotating file logger to record application logs
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    log_file = 'app.log'

    handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024,
                                  backupCount=10)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = configure_logger()
