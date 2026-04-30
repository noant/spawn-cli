from __future__ import annotations


class SpawnError(Exception):
    """Raised on errors that stop the command before mutation."""


class SpawnWarning(UserWarning):
    """Raised (or printed) for recoverable inconsistencies."""
