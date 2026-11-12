"""Centralized logging setup for spawn-cli."""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "spawn"


def get_logger() -> logging.Logger:
    return logging.getLogger(LOGGER_NAME)


def setup_logging(*, verbose: bool = False) -> None:
    """Configure the spawn logger.

    *verbose* enables DEBUG-level messages; the default level is WARNING.
    All diagnostic output goes to stderr so stdout stays clean for
    machine-readable list output.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = get_logger()
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
