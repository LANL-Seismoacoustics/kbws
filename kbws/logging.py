""" Manage logging

Configure logging here, but use get_logger in other modules so that you can use their __name__
in the logs.

"""
import logging

from .config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(levelname)s - %(asctime)s - %(name)s - %(message)s",
    # format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name):
    """ Allows me to configure logging in one place, get __name__ in other other modules. """
    return logging.getLogger(name)
