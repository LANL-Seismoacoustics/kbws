"""Tests for checked-in logging configuration profiles."""
import logging
import logging.config
from pathlib import Path


def test_development_logging_profile_loads():
    """The development profile provides terminal logging without extra dependencies."""
    config_path = Path(__file__).parent / "data" / "logging.dev.ini"
    logging.config.fileConfig(config_path, disable_existing_loggers=False)

    assert any(isinstance(handler, logging.StreamHandler) for handler in logging.getLogger().handlers)
