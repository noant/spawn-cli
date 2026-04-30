from __future__ import annotations

from pathlib import Path

from spawn_cli.core.errors import SpawnError


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_path(root: Path, rel: str) -> Path:
    root_resolved = root.resolve()
    candidate = (root_resolved / rel).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError:
        raise SpawnError(f"path escapes repository root: {rel!r}") from None
    return candidate


def spawn_root(target: Path) -> Path:
    return target / "spawn"
