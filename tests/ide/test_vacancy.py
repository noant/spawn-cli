from __future__ import annotations

from pathlib import Path

from spawn_cli.ide._vacancy import finalize_codex_repo


def test_finalize_codex_removes_config_with_empty_spawn_profile(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        '[permissions.spawn.filesystem.":workspace_roots"]\n', encoding="utf-8"
    )
    finalize_codex_repo(tmp_path)
    assert not (tmp_path / ".codex" / "config.toml").exists()


def test_finalize_codex_keeps_real_permissions(tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        '[permissions.user.filesystem.":workspace_roots"]\n"x/**" = "deny"\n',
        encoding="utf-8",
    )
    finalize_codex_repo(tmp_path)
    assert (tmp_path / ".codex" / "config.toml").exists()
