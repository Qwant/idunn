import json
import logging

from apistar import http
from .settings import Settings
from idunn.utils import prometheus
from pythonjsonlogger import jsonlogger

def init_logging(settings: Settings):
    """
    init the logging for the server
    """
    log_format = settings['LOG_FORMAT']
    as_json = settings['LOG_JSON']

    levels = settings['LOG_LEVEL_BY_MODULE']
    for module, lvl in json.loads(levels).items():
        log_level = lvl.upper()
        log_level = logging.getLevelName(log_level)

        logger = logging.getLogger(module)
        logger.setLevel(log_level)

    logHandler = logging.StreamHandler()
    if as_json:
        formatter = jsonlogger.JsonFormatter(log_format)
        logHandler.setFormatter(formatter)
    else:
        logHandler.setFormatter(logging.Formatter(log_format))

    # we set this handler to the main logger
    logging.getLogger().handlers = [logHandler]

class LogErrorHook:
    def on_error(self, response: http.Response):
        prometheus.exception("unhandled_error")
        logging.getLogger('idunn.error').exception("An unhandled error was raised")
