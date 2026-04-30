from __future__ import annotations

from spawn_cli.io import toml_io


def test_load_toml_missing_returns_empty(tmp_path) -> None:
    assert toml_io.load_toml(tmp_path / "nope.toml") == {}


def test_toml_roundtrip(tmp_path) -> None:
    p = tmp_path / "c.toml"
    data = {"tool": {"pytest": {"addopts": "-v"}}}
    toml_io.save_toml(p, data)
    assert toml_io.load_toml(p) == data
