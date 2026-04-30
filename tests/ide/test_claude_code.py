from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.claude_code import ClaudeCodeAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> ClaudeCodeAdapter:
    return ClaudeCodeAdapter()


def test_detect_with_claude_dir(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_with_claude_md(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    (tmp_path / "CLAUDE.md").write_text("hi", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_neither(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_add_skills_creates_under_claude(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="S", description="d", content="b")],
    )
    assert (tmp_path / ".claude" / "skills" / "s" / "SKILL.md").exists()


def test_add_skills_warns_on_overwrite(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="1")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="2")])
        assert len(w) == 1


def test_remove_skills_deletes_file(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="x", description="d", content="c")])
    adapter.remove_skills(tmp_path, [{"skill": "x", "path": ".claude/skills/x/SKILL.md"}])
    assert not (tmp_path / ".claude" / "skills" / "x" / "SKILL.md").exists()


def test_add_mcp_creates_root_mcp_json(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="srv",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=["a"]),
                )
            ]
        ),
    )
    p = tmp_path / ".mcp.json"
    assert p.exists()
    assert not (tmp_path / ".claude" / "mcp.json").exists()


def test_add_mcp_merges_existing(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"keep": 1, "mcpServers": {"old": {"command": "x", "args": []}}}),
        encoding="utf-8",
    )
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="new",
                    extension="e",
                    transport=McpTransport(type="stdio", command="y", args=[]),
                )
            ]
        ),
    )
    data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert data["keep"] == 1
    assert "old" in data["mcpServers"]
    assert "new" in data["mcpServers"]


def test_add_mcp_secret_placeholder(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="srv",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"K": McpEnvVar(secret=True)},
                )
            ]
        ),
    )
    data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert data["mcpServers"]["srv"]["env"]["K"] == "${K}"


def test_remove_mcp_removes_entry(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="a",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                ),
                McpServer(
                    name="b",
                    extension="e",
                    transport=McpTransport(type="stdio", command="d", args=[]),
                ),
            ]
        ),
    )
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert "a" not in data["mcpServers"]
    assert "b" in data["mcpServers"]


def test_add_agent_ignore_updates_settings_deny(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["Read(spawn/**)"])
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "Read(spawn/**)" in data["permissions"]["deny"]


def test_add_agent_ignore_no_duplicates(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["g"])
    adapter.add_agent_ignore(tmp_path, ["g"])
    data = json.loads((tmp_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert data["permissions"]["deny"].count("g") == 1


def test_remove_agent_ignore_removes_only_spawn_globs(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn-only"])
    path = tmp_path / ".claude" / "settings.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["permissions"]["deny"].append("user-keep")
    path.write_text(json.dumps(data), encoding="utf-8")
    adapter.remove_agent_ignore(tmp_path, ["spawn-only"])
    data2 = json.loads(path.read_text(encoding="utf-8"))
    assert "spawn-only" not in data2["permissions"]["deny"]
    assert "user-keep" in data2["permissions"]["deny"]


def test_remove_agent_ignore_missing_file_noop(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    adapter.remove_agent_ignore(tmp_path, ["x"])


def test_rewrite_entry_point_claude_md(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "body")
    assert rel == "CLAUDE.md"
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text and "body" in text


def test_rewrite_entry_point_warns_alt_location(adapter: ClaudeCodeAdapter, tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "CLAUDE.md").write_text("alt", encoding="utf-8")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.rewrite_entry_point(tmp_path, "p")
        assert any(".claude/CLAUDE.md" in str(x.message) for x in w)
