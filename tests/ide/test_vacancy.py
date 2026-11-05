from __future__ import annotations

import json
from pathlib import Path

from spawn_cli.ide._vacancy import finalize_codex_repo, finalize_opencode_repo


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


def test_finalize_opencode_repo_removes_vacant_config_and_dotdir(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / ".opencode" / "skills" / "s").mkdir(parents=True)
    finalize_opencode_repo(tmp_path)
    assert not (tmp_path / "opencode.json").exists()
    assert not (tmp_path / ".opencode").exists()


def test_finalize_opencode_repo_keeps_user_only_keys(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"model": "x", "theme": "dark"}), encoding="utf-8"
    )
    finalize_opencode_repo(tmp_path)
    assert (tmp_path / "opencode.json").exists()


def test_finalize_opencode_repo_keeps_user_content(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"model": "x", "mcp": {}, "permission": {"read": {"user/**": "ask"}}}),
        encoding="utf-8",
    )
    (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").parent.mkdir(parents=True)
    (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").write_text("x", encoding="utf-8")
    finalize_opencode_repo(tmp_path)
    assert (tmp_path / "opencode.json").exists()
    assert (tmp_path / ".opencode" / "skills" / "s" / "SKILL.md").exists()
