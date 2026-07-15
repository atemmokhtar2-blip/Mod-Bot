"""
Logging setup — RC1.

Supports two output formats controlled by the LOG_FORMAT environment variable:
  LOG_FORMAT=text  (default) — human-readable timestamped lines for Replit / local dev
  LOG_FORMAT=json            — structured JSON per line for Vercel / log aggregators

Usage
-----
  from utils.logger import get_logger, setup_logging
  setup_logging("INFO")          # uses LOG_FORMAT env var
  log = get_logger(__name__)
  log.info("started")
"""

from __future__ import annotations

import json
import logging
import os
import sys


class _JsonFormatter(logging.Formatter):
    """Compact single-line JSON record for production log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


_TEXT_FMT  = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_TEXT_DATE = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger.

    Reads LOG_FORMAT from the environment:
      "json"  → structured JSON (Vercel, Datadog, etc.)
      "text"  → human-readable text (default for Replit / local dev)
    """
    log_format = os.environ.get("LOG_FORMAT", "text").strip().lower()

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Only add handler once (idempotent — safe to call multiple times)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if log_format == "json":
            handler.setFormatter(_JsonFormatter())
        else:
            handler.setFormatter(logging.Formatter(_TEXT_FMT, datefmt=_TEXT_DATE))
        root.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named child logger."""
    return logging.getLogger(name)
