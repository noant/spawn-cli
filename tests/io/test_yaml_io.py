from __future__ import annotations

from spawn_cli.io import yaml_io


def test_load_yaml_missing_returns_empty(tmp_path) -> None:
    assert yaml_io.load_yaml(tmp_path / "missing.yaml") == {}


def test_yaml_roundtrip_nested(tmp_path) -> None:
    p = tmp_path / "data.yaml"
    data = {"top": {"inner": [1, 2]}, "flag": True}
    yaml_io.save_yaml(p, data)
    assert yaml_io.load_yaml(p) == data


def test_yaml_roundtrip_empty_mapping(tmp_path) -> None:
    p = tmp_path / "e.yaml"
    yaml_io.save_yaml(p, {})
    assert yaml_io.load_yaml(p) == {}
