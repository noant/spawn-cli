"""Tests for the JetBrains Junie IDE adapter (mirrors test_cursor.py / test_cline.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spawn_cli.ide import (
    CORE_IGNORE_BLOCK_START,
    EXT_IGNORE_BLOCK_START,
    IGNORE_BLOCK_END,
    IGNORE_BLOCK_START,
    SPAWN_BLOCK_END,
    SPAWN_BLOCK_START,
)
from spawn_cli.ide.junie import JunieAdapter
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> JunieAdapter:
    return JunieAdapter()


def _skill(name: str = "demo-skill") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Demo skill.",
        content="Body.",
        hints=["hint one"],
    )


def _srv(name: str, *, proxy: bool = False, transport_type: str = "stdio") -> McpServer:
    return McpServer(
        name=name,
        extension="ext-a",
        spawn_stdio_proxy=proxy,
        transport=McpTransport(
            type=transport_type,
            command="tool-uv-name",
            args=["--flag"],
            cwd=".",
            url="https://example.test/mcp" if transport_type != "stdio" else None,
        ),
    )


def test_detect_junie_dotdir(adapter: JunieAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".junie").mkdir()
    r = adapter.detect(tmp_path)
    assert r.used_in_repo is True
    c = r.capabilities
    assert c.skills == "native"
    assert c.mcp == "project"
    assert c.agent_ignore == "native"
    assert c.entry_point == "agents-md"


def test_add_and_remove_skills_roundtrip(tmp_path: Path, adapter: JunieAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill("demo-skill")])
    assert rendered == [{"skill": "demo-skill", "path": ".junie/skills/demo-skill/SKILL.md"}]
    path = tmp_path / ".junie" / "skills" / "demo-skill" / "SKILL.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "name: demo-skill" in text
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


def test_remove_skills_keeps_extra_user_files(tmp_path: Path, adapter: JunieAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    skill_dir = tmp_path / ".junie" / "skills" / "demo-skill"
    (skill_dir / "extra.md").write_text("resource", encoding="utf-8")
    adapter.remove_skills(tmp_path, rendered)
    assert not (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "extra.md").is_file()  # user resource retained, dir not pruned


def test_add_skills_overwrite_warns(tmp_path: Path, adapter: JunieAdapter) -> None:
    from spawn_cli.errors import SpawnWarning

    adapter.add_skills(tmp_path, [_skill()])
    with pytest.warns(SpawnWarning, match="Overwriting existing rendered skill"):
        adapter.add_skills(tmp_path, [_skill()])


def test_add_skills_frontmatter_name_matches_dir(tmp_path: Path, adapter: JunieAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill("My Skill")])
    path = tmp_path / ".junie" / "skills" / "my-skill" / "SKILL.md"
    assert path.is_file()
    assert "name: my-skill" in path.read_text(encoding="utf-8")


def test_add_mcp_creates_and_merges(tmp_path: Path, adapter: JunieAdapter) -> None:
    names = adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="spectask-search",
                    extension="spectask",
                    transport=McpTransport(type="stdio", command="uvx", args=["spectask-search-mcp"]),
                )
            ]
        ),
    )
    assert names == ["spectask-search"]
    mcp_path = tmp_path / ".junie" / "mcp" / "mcp.json"
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["spectask-search"] == {
        "command": "uvx",
        "args": ["spectask-search-mcp"],
    }

    # merge: existing user server entry preserved
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="spawn-added",
                    extension="ext",
                    transport=McpTransport(type="stdio", command="cmd", args=["a"]),
                )
            ]
        ),
    )
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert data["mcpServers"]["spectask-search"] == {"command": "uvx", "args": ["spectask-search-mcp"]}
    assert "spawn-added" in data["mcpServers"]


def test_add_mcp_proxy_entry_uses_spawn_wrapper(tmp_path: Path, adapter: JunieAdapter) -> None:
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_srv("proxy-srv", proxy=True)]))
    data = json.loads((tmp_path / ".junie" / "mcp" / "mcp.json").read_text(encoding="utf-8"))
    entry = data["mcpServers"]["proxy-srv"]
    assert entry["command"] == "spawn"
    assert entry["args"] == mcp_stdio_argv("ext-a", "proxy-srv")
    assert "tool-uv-name" not in entry["args"]


def test_add_mcp_remote_entry_shape(tmp_path: Path, adapter: JunieAdapter) -> None:
    srv = _srv("remote-srv", transport_type="streamable-http")
    srv = srv.model_copy(
        update={
            "transport": srv.transport.model_copy(
                update={"headers": {"X-Key": "SEC"}, "command": None, "args": None}
            ),
            "env": {"TOKEN": McpEnvVar(source="user", required=True, secret=True)},
        }
    )
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[srv]))
    data = json.loads((tmp_path / ".junie" / "mcp" / "mcp.json").read_text(encoding="utf-8"))
    entry = data["mcpServers"]["remote-srv"]
    assert entry["type"] == "streamable-http"
    assert entry["url"] == "https://example.test/mcp"
    assert entry["headers"] == {"X-Key": "${SEC}"}
    assert entry["env"]["TOKEN"] == "${TOKEN}"


def test_remove_mcp_prunes_entries(tmp_path: Path, adapter: JunieAdapter) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(name="a", extension="e", transport=McpTransport(type="stdio", command="c", args=[])),
                McpServer(name="b", extension="e", transport=McpTransport(type="stdio", command="c2", args=[])),
            ]
        ),
    )
    mcp_path = tmp_path / ".junie" / "mcp" / "mcp.json"
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "a" not in data["mcpServers"]
    assert "b" in data["mcpServers"]
    # removing the last server leaves an empty mcpServers map; file kept
    adapter.remove_mcp(tmp_path, ["b"])
    data = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert data["mcpServers"] == {}


def test_agent_ignore_roundtrip_and_clear(tmp_path: Path, adapter: JunieAdapter) -> None:
    ignore = tmp_path / ".aiignore"
    ignore.write_text("user-secret/**\n", encoding="utf-8")
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**", "spawn/.ext/**"])
    text = ignore.read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START in text
    assert IGNORE_BLOCK_END in text
    assert "user-secret/**" in text
    # idempotent re-add (same globs)
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**", "spawn/.ext/**"])
    assert ignore.read_text(encoding="utf-8").count("spawn/.core/**") == 1
    adapter.remove_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "spawn/.core/**" not in text
    assert "spawn/.ext/**" in text
    # split-region methods
    adapter.rewrite_core_agent_ignore(tmp_path, ["core-only/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["ext-only/**"])
    text = ignore.read_text(encoding="utf-8")
    assert CORE_IGNORE_BLOCK_START in text
    assert EXT_IGNORE_BLOCK_START in text
    assert "core-only/**" in text
    assert "ext-only/**" in text
    adapter.clear_spawn_agent_ignore(tmp_path)
    text = ignore.read_text(encoding="utf-8")
    assert "core-only/**" not in text
    assert "ext-only/**" not in text
    assert "user-secret/**" in text


def test_rewrite_entry_point_agents_md(tmp_path: Path, adapter: JunieAdapter) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "hello prompt")
    assert rel == "AGENTS.md"
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text
    assert "hello prompt" in text
    assert SPAWN_BLOCK_END in text
    # second call replaces the block
    adapter.rewrite_entry_point(tmp_path, "new body")
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "new body" in text
    assert "hello prompt" not in text


def _setup_spawn_only(tmp_path: Path, adapter: JunieAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[McpServer(name="s", extension="e", transport=McpTransport(type="stdio", command="c", args=[]))]
        ),
    )
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.rewrite_entry_point(tmp_path, "p")
    adapter.remove_skills(tmp_path, rendered)
    adapter.remove_mcp(tmp_path, ["s"])


@pytest.mark.parametrize(
    "user_files,expect_junie,expect_ignore",
    [
        pytest.param([], False, False, id="spawn-only"),
        pytest.param(
            [".junie/rules/r.md", ".junie/memory/x.md"],
            True,
            True,
            id="user-content",
        ),
    ],
)
def test_finalize_repo_after_ide_removed(
    tmp_path: Path,
    adapter: JunieAdapter,
    user_files: list[str],
    expect_junie: bool,
    expect_ignore: bool,
) -> None:
    _setup_spawn_only(tmp_path, adapter)
    for rel in user_files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("user", encoding="utf-8")
    if expect_ignore:
        # user lines alongside the spawn block keep the file alive
        with (tmp_path / ".aiignore").open("a", encoding="utf-8") as fh:
            fh.write("user-rule/**\n")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert (tmp_path / ".junie").is_dir() == expect_junie
    if expect_junie:
        # spawn-owned parts still pruned
        assert not (tmp_path / ".junie" / "skills").exists()
        assert not (tmp_path / ".junie" / "mcp").exists()
        assert (tmp_path / ".junie" / "rules" / "r.md").is_file()
        assert (tmp_path / ".junie" / "memory" / "x.md").is_file()
    ignore = tmp_path / ".aiignore"
    assert ignore.is_file() == expect_ignore
    if expect_ignore:
        text = ignore.read_text(encoding="utf-8")
        assert "spawn/.core/**" not in text  # spawn block cleared
        assert "user-rule/**" in text
