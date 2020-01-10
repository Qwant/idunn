import json
import logging
from logging.config import dictConfig

from starlette.requests import Request
from starlette.responses import PlainTextResponse
from .settings import Settings
from idunn.utils import prometheus


def get_logging_dict(settings: Settings):
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


def init_logging(settings: Settings):
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


async def handle_errors(request: Request, exception):
    """
    overrides the default error handler defined in ServerErrorMiddleware
    """
    prometheus.exception("unhandled_error")
    return PlainTextResponse("Internal Server Error", status_code=500)
