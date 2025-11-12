import logging
import sys
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class RequestJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("level"):
            log_record["level"] = record.levelname
        log_record.setdefault("logger", record.name)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = RequestJsonFormatter("%(asctime)s %(level)s %(name)s %(message)s")
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=[handler])
