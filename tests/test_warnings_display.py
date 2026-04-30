from __future__ import annotations

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


def test_spawn_warning_prints_friendly_line(capsys):
    reset_spawn_warning_format()
    install_spawn_warning_format()
    warnings.warn("Replacing existing file from extension (static): spec/x.md", SpawnWarning)
    err = capsys.readouterr().err.strip()
    assert err == "spawn: warning: Replacing existing file from extension (static): spec/x.md"
    assert "SpawnWarning" not in err
    assert ".py" not in err


def test_non_spawn_delegates_to_chain(capsys):
    reset_spawn_warning_format()
    delegated: list[str] = []

    def prior(message, category, filename, lineno, file=None, line=None):
        delegated.append(str(message))

    warnings.showwarning = prior  # type: ignore[assignment]
    try:
        install_spawn_warning_format()
        warnings.warn("legacy", UserWarning)
        assert delegated == ["legacy"]
        warnings.warn("sw", SpawnWarning)
        assert capsys.readouterr().err.strip() == "spawn: warning: sw"
    finally:
        reset_spawn_warning_format()
