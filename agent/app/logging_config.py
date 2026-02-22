import logging
import logging.config
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONF = os.path.join(os.path.dirname(BASE_DIR), "logging.conf")


def configure_logging():
    if os.path.exists(LOGGING_CONF):
        logging.config.fileConfig(LOGGING_CONF)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
