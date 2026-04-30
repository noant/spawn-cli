from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import IGNORE_BLOCK_END, IGNORE_BLOCK_START, SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.windsurf import WindsurfAdapter
from spawn_cli.models.mcp import McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> WindsurfAdapter:
    return WindsurfAdapter()


def test_detect_with_windsurf_dir(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    (tmp_path / ".windsurf").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_with_codeiumignore(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    (tmp_path / ".codeiumignore").write_text("", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_neither(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_capabilities_mcp_unsupported(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).capabilities.mcp == "unsupported"


def test_add_skills_creates_under_windsurf(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="W", description="d", content="b")],
    )
    assert (tmp_path / ".windsurf" / "skills" / "w" / "SKILL.md").exists()


def test_add_skills_warns_on_overwrite(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="1")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="2")])
        assert len(w) == 1


def test_remove_skills_deletes_file(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="r", description="d", content="c")])
    adapter.remove_skills(tmp_path, [{"skill": "r", "path": ".windsurf/skills/r/SKILL.md"}])
    assert not (tmp_path / ".windsurf" / "skills" / "r" / "SKILL.md").exists()


def test_add_mcp_warns_and_returns_empty(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="x",
                extension="e",
                transport=McpTransport(type="stdio", command="c", args=[]),
            )
        ]
    )
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        out = adapter.add_mcp(tmp_path, nm)
    assert out == []
    assert len(w) == 1


def test_remove_mcp_warns(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.remove_mcp(tmp_path, ["name"])
        assert len(w) == 1


def test_add_agent_ignore_creates_codeiumignore(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["tmp/**"])
    text = (tmp_path / ".codeiumignore").read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START in text
    assert "tmp/**" in text


def test_remove_agent_ignore_removes_block(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["g"])
    adapter.remove_agent_ignore(tmp_path, [])
    text = (tmp_path / ".codeiumignore").read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START not in text


def test_rewrite_entry_point_agents_md(adapter: WindsurfAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "agents")
    assert rel == "AGENTS.md"
    t = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in t and "agents" in t
