"""Lightweight logging helpers."""

import logging
from typing import Optional


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_error(logger: logging.Logger, error: Exception, context: Optional[str] = None):
    msg = f"Error in {context}: {error}" if context else str(error)
    logger.error(msg, exc_info=True)
