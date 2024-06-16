import logging
import json
from typing import Dict, Union, Optional


class JSONFormatter(logging.Formatter):
    """Custom formatter to output log records as JSON strings"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }

        # Check for extra attributes and merge them
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry.update(record.extra)

        log_entry.update({"timestamp": self.formatTime(record, self.datefmt)})
        serialized = json.dumps(log_entry)
        return serialized
    

class CustomLogger:
    """Custom logger class to handle logging in the application"""

    def __init__(self, name: str, level: int = logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        stream_handler = logging.StreamHandler()
        self.formatter = JSONFormatter()
        stream_handler.setFormatter(self.formatter)

        for handler in logger.handlers:
            logger.removeHandler(handler)

        logger.addHandler(stream_handler)
        logger.propagate = False
        self.logger = logger

    def debug(self, message: str, fields: Dict[str, object] = None):
        self.logger.debug(message, extra=self._get_extras(fields))

    def info(self, message: str, fields: Dict[str, Union[str, int]] = None):
        self.logger.info(message, extra=self._get_extras(fields))

    def warning(self, message: str, fields: Dict[str, Union[str, int]] = None):
        self.logger.warning(message, extra=self._get_extras(fields))

    def exception(self, message: str, fields: Dict[str, Union[str, int]] = None):
        self.logger.exception(message, extra=self._get_extras(fields))

    def error(self, message: str, fields: Dict[str, Union[str, int]] = None):
        self.logger.error(message, extra=self._get_extras(fields))

    def critical(self, message: str, fields: Dict[str, Union[str, int]] = None):
        self.logger.critical(message, extra=self._get_extras(fields))

    def _get_extras(self, fields: Dict[str, object]) -> Optional[Dict[str, object]]:
        extras = None
        if fields is not None:
            extras = {"extra": fields}

        return extras
    
