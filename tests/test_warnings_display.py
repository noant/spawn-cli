from __future__ import annotations

import logging
import warnings

import pytest

from spawn_cli.errors import SpawnWarning
from spawn_cli.warnings_display import (
    install_spawn_warning_format,
    reset_spawn_warning_format,
)

_builtin_showwarning = warnings.showwarning


@pytest.fixture(autouse=True)
def _reset_warning_hook():
    yield
    reset_spawn_warning_format()
    warnings.showwarning = _builtin_showwarning


def test_spawn_warning_prints_friendly_line(caplog):
    reset_spawn_warning_format()
    install_spawn_warning_format()
    with caplog.at_level(logging.WARNING, logger="spawn"):
        warnings.warn("Replacing existing file from extension (static): spec/x.md", SpawnWarning)
    assert "spawn: warning: Replacing existing file from extension (static): spec/x.md" in caplog.text
    assert "SpawnWarning" not in caplog.text
    assert ".py" not in caplog.text.split("spawn: warning:")[-1]


def test_non_spawn_delegates_to_chain(caplog):
    reset_spawn_warning_format()
    delegated: list[str] = []

    def prior(message, category, filename, lineno, file=None, line=None):
        delegated.append(str(message))

    warnings.showwarning = prior
    try:
        install_spawn_warning_format()
        warnings.warn("legacy", UserWarning)
        assert delegated == ["legacy"]
        with caplog.at_level(logging.WARNING, logger="spawn"):
            warnings.warn("sw", SpawnWarning)
        assert "spawn: warning: sw" in caplog.text
    finally:
        reset_spawn_warning_format()
