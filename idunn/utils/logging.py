from .settings import Settings
from pythonjsonlogger import jsonlogger
import logging
import json

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """We define our own sets of key to be more consistent with the other json logs"""

    def _override_field(self, log_record, previous, new):
        if previous in log_record:
            log_record[new] = log_record.pop(previous)

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        self._override_field(log_record, 'message', 'msg')
        self._override_field(log_record, 'levelname', 'level')
        self._override_field(log_record, 'asctime', 'ts')

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
        formatter = CustomJsonFormatter(log_format)
        logHandler.setFormatter(formatter)
    else:
        logHandler.setFormatter(logging.Formatter(log_format))
    
    # we set this handler to the main logger
    logging.getLogger().handlers = [logHandler]
