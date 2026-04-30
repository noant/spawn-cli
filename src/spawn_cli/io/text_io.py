from __future__ import annotations

from pathlib import Path

from spawn_cli.io.paths import ensure_dir


def read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
