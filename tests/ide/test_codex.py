from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import IGNORE_BLOCK_END, IGNORE_BLOCK_START, SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.codex import CodexAdapter
from spawn_cli.io.toml_io import load_toml
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> CodexAdapter:
    return CodexAdapter()


def test_detect_with_codex_dir(adapter: CodexAdapter, tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir()
    r = adapter.detect(tmp_path)
    assert r.used_in_repo is True
    assert r.capabilities.agent_ignore == "unsupported"


def test_detect_with_agents_dir(adapter: CodexAdapter, tmp_path: Path) -> None:
    (tmp_path / ".agents").mkdir()
    r = adapter.detect(tmp_path)
    assert r.used_in_repo is True


def test_detect_neither(adapter: CodexAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_add_skills_creates_under_agents(adapter: CodexAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="My Skill", description="d", content="body")],
    )
    p = tmp_path / ".agents" / "skills" / "my-skill" / "SKILL.md"
    assert p.exists()


def test_add_skills_warns_on_overwrite(adapter: CodexAdapter, tmp_path: Path) -> None:
    s = SkillMetadata(name="s", description="d", content="first")
    adapter.add_skills(tmp_path, [s])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="second")])
        assert len(w) == 1
        assert "Overwriting" in str(w[0].message)


def test_remove_skills_deletes_file(adapter: CodexAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="gone", description="d", content="c")])
    adapter.remove_skills(tmp_path, [{"skill": "gone", "path": ".agents/skills/gone/SKILL.md"}])
    assert not (tmp_path / ".agents" / "skills" / "gone" / "SKILL.md").exists()


def test_add_mcp_creates_toml(adapter: CodexAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="spectask-search",
                extension="e",
                transport=McpTransport(type="stdio", command="uvx", args=["spectask-search-mcp"]),
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    cfg = tmp_path / ".codex" / "config.toml"
    assert cfg.exists()
    text = cfg.read_text(encoding="utf-8")
    assert 'mcp_servers' in text.lower()


def test_add_mcp_merges_existing(adapter: CodexAdapter, tmp_path: Path) -> None:
    (tmp_path / ".codex").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "config.toml").write_text(
        'other = "keep"\n\n[mcp_servers.existing]\ncommand = "old"\nargs = []\n',
        encoding="utf-8",
    )
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="new-srv",
                extension="e",
                transport=McpTransport(type="stdio", command="c", args=["a"]),
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "keep" in text
    assert "existing" in text
    assert "new-srv" in text


def test_add_mcp_hyphenated_key_quoted(adapter: CodexAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="spectask-search",
                extension="e",
                transport=McpTransport(type="stdio", command="uvx", args=["x"]),
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "mcp_servers" in text and "spectask-search" in text and "uvx" in text
    data = load_toml(tmp_path / ".codex" / "config.toml")
    assert data["mcp_servers"]["spectask-search"]["command"] == "uvx"


def test_add_mcp_secret_placeholder(adapter: CodexAdapter, tmp_path: Path) -> None:
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
    text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert "API_KEY" in text
    assert "${API_KEY}" in text or '"${API_KEY}"' in text


def test_remove_mcp_removes_table(adapter: CodexAdapter, tmp_path: Path) -> None:
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
    text = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
    assert '[mcp_servers."a"]' not in text
    assert "b" in text


def test_add_agent_ignore_warns(adapter: CodexAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1
        assert "unsupported" in str(w[0].message).lower()


def test_remove_agent_ignore_warns(adapter: CodexAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.remove_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1


def test_rewrite_entry_point_agents_md(adapter: CodexAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "prompt")
    assert rel == "AGENTS.md"
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text
    assert SPAWN_BLOCK_END in text
    assert "prompt" in text
