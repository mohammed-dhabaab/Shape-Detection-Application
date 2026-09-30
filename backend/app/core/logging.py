"""Structured logging on top of the standard library (no extra dependency).

Every record carries the current request ID, taken from a context variable set by the
request middleware, so log lines from the route, the use case and worker threads can
be correlated.
"""

import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Literal

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Attributes present on every LogRecord; anything else was passed via ``extra=``.
_RESERVED_ATTRIBUTES = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
    | {"message", "asctime", "request_id", "taskName"}
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if request_id := getattr(record, "request_id", None):
            payload["request_id"] = request_id
        payload.update(
            {
                key: value
                for key, value in record.__dict__.items()
                if key not in _RESERVED_ATTRIBUTES
            }
        )
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str, log_format: Literal["json", "console"]) -> None:
    formatter = (
        {"()": JsonFormatter}
        if log_format == "json"
        else {"format": "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"}
    )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": RequestIdFilter}},
            "formatters": {"default": formatter},
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                }
            },
            "root": {"handlers": ["default"], "level": level},
            "loggers": {
                # Route uvicorn through the same handler; its access log is replaced by
                # the request middleware's structured access log.
                "uvicorn": {"handlers": ["default"], "level": level, "propagate": False},
                "uvicorn.error": {"level": level},
                "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
            },
        }
    )
