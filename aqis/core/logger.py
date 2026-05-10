from __future__ import annotations

import contextvars
import json
import logging
import logging.config
import sys
import time
from typing import Any

from aqis.core.config import ROOT_DIR, get_config


request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
request_path_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_path", default="-")

_LOGGING_CONFIGURED = False


class JsonLogFormatter(logging.Formatter):
    """Structured JSON logging formatter for internal diagnostics."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "request_id": getattr(record, "request_id", request_id_var.get()),
            "module": record.name,
            "message": record.getMessage(),
            "path": getattr(record, "request_path", request_path_var.get()),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = getattr(record, "duration_ms")
        return json.dumps(payload, ensure_ascii=False)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.request_path = request_path_var.get()
        return True


def setup_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    config = get_config()
    logging_conf = ROOT_DIR / "config" / "logging.conf"
    if logging_conf.exists() and config.enable_json_logs:
        logging.config.fileConfig(logging_conf, defaults={"sys": sys}, disable_existing_loggers=False)
    else:
        logging.basicConfig(level=config.log_level)

    root_logger = logging.getLogger()
    root_logger.setLevel(config.log_level)
    request_filter = RequestContextFilter()
    for handler in root_logger.handlers:
        handler.addFilter(request_filter)

    _LOGGING_CONFIGURED = True


def setup_logger(name: str, level: int | None = None) -> logging.Logger:
    setup_logging()
    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger


def set_request_context(request_id: str, path: str) -> tuple[contextvars.Token[str], contextvars.Token[str]]:
    return request_id_var.set(request_id), request_path_var.set(path)


def clear_request_context(tokens: tuple[contextvars.Token[str], contextvars.Token[str]]) -> None:
    request_id_var.reset(tokens[0])
    request_path_var.reset(tokens[1])


def log_timing(logger: logging.Logger, message: str, started_at: float) -> None:
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
    logger.info(message, extra={"duration_ms": elapsed_ms})
