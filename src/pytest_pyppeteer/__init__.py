"""The entrypoint."""
import logging.config

from pytest_pyppeteer.settings import LOGGING

__version__ = "1.0.0"

logging.config.dictConfig(LOGGING)
