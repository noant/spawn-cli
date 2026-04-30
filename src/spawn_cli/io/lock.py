from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout

from spawn_cli.errors import SpawnError
from spawn_cli.io.paths import ensure_dir


@contextmanager
def spawn_lock(target_root: Path):
    lock_path = target_root / "spawn" / ".metadata" / ".spawn.lock"
    ensure_dir(lock_path.parent)
    lock = FileLock(str(lock_path))
    try:
        lock.acquire(timeout=0)
    except Timeout:
        raise SpawnError("Операция в процессе (файл lock detected)") from None
    try:
        yield
    finally:
        lock.release()
