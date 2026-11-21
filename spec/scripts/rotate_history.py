#!/usr/bin/env python3
"""Rotate done spec task folders into spec/tasks/__history/.

Keeps the newest KEEP done folders (by numeric task code) in spec/tasks/
and moves older ones into spec/tasks/__history/.

Usage:
    py spec/scripts/rotate_history.py            # Windows, apply
    python3 spec/scripts/rotate_history.py       # Linux/macOS, apply
    python3 spec/scripts/rotate_history.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

_KEEP = 10
_DONE_CODE_RE = re.compile(r"^_DONE_(\d+)-")


def _done_code(name: str) -> int | None:
    """Return the numeric task code of a done folder name, or None."""
    match = _DONE_CODE_RE.match(name)
    return int(match.group(1)) if match else None


def plan_rotation(tasks_dir: Path, keep: int = _KEEP) -> list[tuple[Path, Path]]:
    """Return (src, dst) pairs for done folders older than the newest `keep`."""
    if not tasks_dir.is_dir():
        return []
    done = [
        (code, entry)
        for entry in tasks_dir.iterdir()
        if entry.is_dir() and (code := _done_code(entry.name)) is not None
    ]
    done.sort(key=lambda pair: pair[0], reverse=True)
    history = tasks_dir / "__history"
    return [
        (entry, history / entry.name)
        for _, entry in done[keep:]
    ]


def main(argv: list[str] | None = None) -> int:
    """Apply the rotation; return 0 (warnings are non-fatal)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan without moving")
    args = parser.parse_args(argv)
    tasks_dir = Path(__file__).resolve().parents[1] / "tasks"
    moves = plan_rotation(tasks_dir)
    if not moves:
        print("nothing to rotate")
        return 0
    for src, dst in moves:
        if dst.exists():
            print(f"skip (exists): {dst}")
            continue
        print(f"{src} -> {dst}")
        if not args.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
