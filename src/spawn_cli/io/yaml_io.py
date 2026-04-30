from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML


def configure_yaml_dump(yaml: YAML) -> None:
    """Force block-style collections for dumps (avoid flow `{ ... }` / `[ ... ]` on nested nodes)."""

    yaml.default_flow_style = False
    yaml.width = 4096
    yaml.sort_base_mapping_type_on_output = False


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh)
    return data if isinstance(data, dict) else {}


def save_yaml(path: Path, data: dict) -> None:
    from spawn_cli.io.paths import ensure_dir

    ensure_dir(path.parent)
    yaml = YAML(typ="safe")
    configure_yaml_dump(yaml)
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh)
