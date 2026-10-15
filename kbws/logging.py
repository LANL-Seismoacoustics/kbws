"""Configure application logging and return named loggers."""
import logging
import logging.config

from .config import settings

logging.config.fileConfig(settings.logging_config, disable_existing_loggers=False)


def get_logger(name):
    """Return a logger configured by the selected logging profile."""
    return logging.getLogger(name)
