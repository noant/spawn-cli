from __future__ import annotations

import sys
from pathlib import Path

from spawn_cli.io.paths import ensure_dir

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

import tomli_w


def load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    return data if isinstance(data, dict) else {}


def save_toml(path: Path, data: dict) -> None:
    ensure_dir(path.parent)
    path.write_bytes(tomli_w.dumps(data).encode("utf-8"))
