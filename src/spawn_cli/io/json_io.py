from __future__ import annotations

import json
from pathlib import Path

from spawn_cli.io.paths import ensure_dir


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def save_json(path: Path, data: dict, indent: int = 2) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
