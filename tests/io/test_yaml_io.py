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


def test_save_yaml_navigation_like_nested_files_avoids_flow_collections(tmp_path) -> None:
    p = tmp_path / "nav.yaml"
    data = {
        "read-contextual": [
            {
                "ext": "spectask",
                "files": [{"path": "spec/main.md", "description": "Short line."}],
            }
        ]
    }
    yaml_io.save_yaml(p, data)
    text = p.read_text(encoding="utf-8")
    assert "- {" not in text
    assert "path: spec/main.md" in text
    assert "description: Short line." in text
