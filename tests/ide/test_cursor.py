from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import IGNORE_BLOCK_END, IGNORE_BLOCK_START, SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.cursor import CursorAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillFileRef, SkillMetadata


@pytest.fixture
def adapter() -> CursorAdapter:
    return CursorAdapter()


def test_detect_with_cursor_dir(adapter: CursorAdapter, tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    r = adapter.detect(tmp_path)
    assert r.used_in_repo is True
    c = r.capabilities
    assert c.skills == "native"
    assert c.mcp == "project"
    assert c.agent_ignore == "native"
    assert c.entry_point == "agents-md"


def test_detect_without_cursor_dir(adapter: CursorAdapter, tmp_path: Path) -> None:
    r = adapter.detect(tmp_path)
    assert r.used_in_repo is False


def test_add_skills_creates_file(adapter: CursorAdapter, tmp_path: Path) -> None:
    skills = [
        SkillMetadata(
            name="My Skill",
            description="Do a thing.",
            content="Body.",
            required_read=[SkillFileRef(file="spec/main.md", description="Main")],
        )
    ]
    adapter.add_skills(tmp_path, skills)
    p = tmp_path / ".cursor" / "skills" / "my-skill" / "SKILL.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert "---\n" in text and "name: My Skill" in text
    assert "Read `spawn/navigation.yaml` first." in text
    assert "Mandatory reads:" in text
    assert "- `spec/main.md` - Main" in text


def test_add_skills_warns_on_overwrite(adapter: CursorAdapter, tmp_path: Path) -> None:
    skill = SkillMetadata(name="s", description="d", content="first")
    adapter.add_skills(tmp_path, [skill])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="second")])
        assert len(w) == 1
        assert "Overwriting" in str(w[0].message)


def test_add_skills_returns_tracking_list(adapter: CursorAdapter, tmp_path: Path) -> None:
    a = SkillMetadata(name="a", description="da", content="a")
    b = SkillMetadata(name="b", description="db", content="b")
    out = adapter.add_skills(tmp_path, [a, b])
    assert out == [
        {"skill": "a", "path": ".cursor/skills/a/SKILL.md"},
        {"skill": "b", "path": ".cursor/skills/b/SKILL.md"},
    ]


def test_remove_skills_deletes_file(adapter: CursorAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="gone", description="d", content="c")],
    )
    rendered = [{"skill": "gone", "path": ".cursor/skills/gone/SKILL.md"}]
    adapter.remove_skills(tmp_path, rendered)
    skill_md = tmp_path / ".cursor" / "skills" / "gone" / "SKILL.md"
    assert not skill_md.exists()
    skill_dir = skill_md.parent
    assert not skill_dir.exists()


def test_remove_skills_keeps_non_empty_dir(adapter: CursorAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="x", description="d", content="c")])
    extra = tmp_path / ".cursor" / "skills" / "x" / "extra.txt"
    extra.write_text("keep dir", encoding="utf-8")
    adapter.remove_skills(tmp_path, [{"skill": "x", "path": ".cursor/skills/x/SKILL.md"}])
    assert not (tmp_path / ".cursor" / "skills" / "x" / "SKILL.md").exists()
    assert extra.exists()


def test_add_mcp_creates_file(adapter: CursorAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="spectask-search",
                extension="spectask",
                transport=McpTransport(type="stdio", command="uvx", args=["spectask-search-mcp"]),
            )
        ]
    )
    names = adapter.add_mcp(tmp_path, nm)
    assert names == ["spectask-search"]
    mcp_path = tmp_path / ".cursor" / "mcp.json"
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["spectask-search"] == {
        "command": "uvx",
        "args": ["spectask-search-mcp"],
    }


def test_add_mcp_merges_existing(adapter: CursorAdapter, tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir(parents=True, exist_ok=True)
    existing = {
        "note": "user",
        "mcpServers": {"existing": {"command": "old", "args": []}},
    }
    (tmp_path / ".cursor" / "mcp.json").write_text(
        json.dumps(existing),
        encoding="utf-8",
    )
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="spawn-added",
                extension="ext",
                transport=McpTransport(type="stdio", command="cmd", args=["a"]),
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert data["note"] == "user"
    assert "existing" in data["mcpServers"]
    assert "spawn-added" in data["mcpServers"]


def test_add_mcp_secret_placeholder(adapter: CursorAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="srv",
                extension="e",
                transport=McpTransport(type="stdio", command="c", args=[]),
                env={"API_KEY": McpEnvVar(secret=True)},
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert data["mcpServers"]["srv"]["env"]["API_KEY"] == "${API_KEY}"


def test_remove_mcp_removes_entry(adapter: CursorAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="a",
                extension="e",
                transport=McpTransport(type="stdio", command="c", args=[]),
            ),
            McpServer(
                name="b",
                extension="e",
                transport=McpTransport(type="stdio", command="c2", args=[]),
            ),
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert "a" not in data["mcpServers"]
    assert "b" in data["mcpServers"]


def test_remove_mcp_missing_file_noop(adapter: CursorAdapter, tmp_path: Path) -> None:
    adapter.remove_mcp(tmp_path, ["nope"])  # no crash


def test_add_agent_ignore(adapter: CursorAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["logs/**", "*.tmp"])
    text = (tmp_path / ".cursorignore").read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START in text
    assert IGNORE_BLOCK_END in text
    assert "logs/**" in text
    assert "*.tmp" in text


def test_remove_agent_ignore(adapter: CursorAdapter, tmp_path: Path) -> None:
    path = tmp_path / ".cursorignore"
    path.write_text(
        "user/preserve/**\n"
        f"{IGNORE_BLOCK_START}\n"
        "spawn-a\n"
        "spawn-b\n"
        f"{IGNORE_BLOCK_END}\n",
        encoding="utf-8",
    )
    adapter.remove_agent_ignore(tmp_path, ["spawn-a"])
    text = path.read_text(encoding="utf-8")
    assert "user/preserve/**" in text
    assert IGNORE_BLOCK_START in text
    assert "spawn-b" in text
    assert "spawn-a" not in text


def test_rewrite_entry_point_creates(adapter: CursorAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "hello prompt")
    assert rel == "AGENTS.md"
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text
    assert "hello prompt" in text
    assert SPAWN_BLOCK_END in text


def test_rewrite_entry_point_replaces(adapter: CursorAdapter, tmp_path: Path) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text(
        f"intro\n{SPAWN_BLOCK_START}\nold\n{SPAWN_BLOCK_END}\ntrailer\n",
        encoding="utf-8",
    )
    adapter.rewrite_entry_point(tmp_path, "new body")
    text = agents.read_text(encoding="utf-8")
    assert "intro\n" in text
    assert "trailer\n" in text
    assert "new body" in text
    assert "old" not in text


def test_rewrite_entry_point_returns_path(adapter: CursorAdapter, tmp_path: Path) -> None:
    assert adapter.rewrite_entry_point(tmp_path, "p") == "AGENTS.md"
