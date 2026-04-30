from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from spawn_cli.io.paths import ensure_dir


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh)
    return data if isinstance(data, dict) else {}


def save_yaml(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    yaml = YAML(typ="safe")
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh)
