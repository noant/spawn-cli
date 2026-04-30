from __future__ import annotations

from spawn_cli.io.lock import spawn_lock


def test_spawn_lock_creates_file_and_releases(tmp_path) -> None:
    (tmp_path / "spawn" / ".metadata").mkdir(parents=True)
    lock_path = tmp_path / "spawn" / ".metadata" / ".spawn.lock"

    with spawn_lock(tmp_path):
        assert lock_path.is_file()

    with spawn_lock(tmp_path):
        assert lock_path.is_file()
