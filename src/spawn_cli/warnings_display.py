"""CLI-only formatting for SpawnWarning (see task 9 spec)."""

from __future__ import annotations

import sys
import warnings
from collections.abc import Callable

from spawn_cli.errors import SpawnWarning

_prev_showwarning: Callable[..., None] | None = None


def install_spawn_warning_format() -> None:
    global _prev_showwarning
    if _prev_showwarning is not None:
        return
    _prev_showwarning = warnings.showwarning

    def showwarning(message, category, filename, lineno, file=None, line=None) -> None:
        if isinstance(category, type) and issubclass(category, SpawnWarning):
            text = str(message).strip()
            print(f"spawn: warning: {text}", file=sys.stderr)
            return
        if _prev_showwarning is not None:
            _prev_showwarning(message, category, filename, lineno, file=file, line=line)

    warnings.showwarning = showwarning  # type: ignore[method-assign]


def reset_spawn_warning_format() -> None:
    global _prev_showwarning
    if _prev_showwarning is not None:
        warnings.showwarning = _prev_showwarning
        _prev_showwarning = None
