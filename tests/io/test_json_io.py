from __future__ import annotations

from pathlib import Path

from spawn_cli.io import json_io


def test_load_json_missing_returns_empty(tmp_path) -> None:
    p = tmp_path / "nope.json"
    assert json_io.load_json(p) == {}


def test_json_roundtrip_nested(tmp_path) -> None:
    p = tmp_path / "d.json"
    data = {"a": 1, "nested": {"b": [1, 2, 3]}}
    json_io.save_json(p, data)
    assert json_io.load_json(p) == data


def test_save_json_indent(tmp_path) -> None:
    p = tmp_path / "out.json"
    json_io.save_json(p, {"x": {"y": 1}}, indent=4)
    text = p.read_text(encoding="utf-8")
    assert "    " in text


def test_load_json_empty_file(tmp_path) -> None:
    p = tmp_path / "e.json"
    p.write_text("   \n", encoding="utf-8")
    assert json_io.load_json(p) == {}
