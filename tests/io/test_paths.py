from __future__ import annotations

from pathlib import Path

import pytest

from spawn_cli.core.errors import SpawnError
from spawn_cli.io import paths as path_io


def test_ensure_dir_nested(tmp_path) -> None:
    d = tmp_path / "a" / "b" / "c"
    path_io.ensure_dir(d)
    assert d.is_dir()


def test_safe_path_relative_ok(tmp_path) -> None:
    p = path_io.safe_path(tmp_path, "foo/bar")
    assert p == (tmp_path / "foo" / "bar").resolve()


def test_safe_path_rejects_escape(tmp_path) -> None:
    with pytest.raises(SpawnError, match="escapes"):
        path_io.safe_path(tmp_path, "..")


def test_safe_path_rejects_dotdot_in_middle(tmp_path) -> None:
    with pytest.raises(SpawnError, match="escapes"):
        path_io.safe_path(tmp_path, "x/../../etc/passwd")


def test_spawn_root_returns_child(tmp_path) -> None:
    assert path_io.spawn_root(tmp_path) == Path(tmp_path) / "spawn"
