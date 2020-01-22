import json
import logging
from logging.config import dictConfig


def get_logging_dict(settings):
    return {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": settings["LOG_FORMAT"],
            },
            "simple": {"format": settings["LOG_FORMAT"]},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if settings["LOG_JSON"] else "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": "WARNING", "handlers": ["console"], "propagate": False,},
            "gunicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
        "root": {"level": "INFO", "handlers": ["console"]},
    }


def init_logging(settings):
    """
    init the logging for the server
    """
    dictConfig(get_logging_dict(settings))

    levels = settings["LOG_LEVEL_BY_MODULE"]
    for module, lvl in json.loads(levels).items():
        log_level = lvl.upper()
        log_level = logging.getLevelName(log_level)

        logger = logging.getLogger(module)
        logger.setLevel(log_level)
