"""All settings."""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "pytest_pyppeteer": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "pytest_pyppeteer.models": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
