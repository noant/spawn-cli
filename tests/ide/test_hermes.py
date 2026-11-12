"""Tests for the Hermes IDE adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from spawn_cli.errors import SpawnWarning
from spawn_cli.ide.hermes import HermesAdapter
from spawn_cli.ide.registry import SPAWN_BLOCK_START
from spawn_cli.models.mcp import McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> HermesAdapter:
    return HermesAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Execute approved spectasks.",
        content="# body\n",
        hints=["Prefer spectask steps in order."],
    )


def _mcp() -> NormalizedMcp:
    return NormalizedMcp(
        servers=[
            {
                "name": "spectask-search",
                "extension": "spectask",
                "transport": McpTransport(type="stdio", command="uvx"),
            }
        ]
    )


def test_detect_markers(tmp_path: Path, adapter: HermesAdapter) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".hermes").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_entry_file(tmp_path: Path, adapter: HermesAdapter) -> None:
    (tmp_path / ".hermes.md").write_text("x", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_capabilities(tmp_path: Path, adapter: HermesAdapter) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "unsupported"
    assert caps.agent_ignore == "unsupported"
    assert caps.entry_point == "hermes-md"


def test_add_and_remove_skills(tmp_path: Path, adapter: HermesAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill("My Skill")])
    path = tmp_path / ".hermes" / "skills" / "my-skill" / "SKILL.md"
    assert path.is_file()
    assert rendered == [{"skill": "My Skill", "path": ".hermes/skills/my-skill/SKILL.md"}]
    text = path.read_text(encoding="utf-8")
    assert "name: my-skill" in text  # frontmatter name == directory name
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


def test_add_skills_warns_on_overwrite(tmp_path: Path, adapter: HermesAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill()])
    with pytest.warns(UserWarning, match="Overwriting"):
        adapter.add_skills(tmp_path, [_skill()])


def test_add_mcp_unsupported(tmp_path: Path, adapter: HermesAdapter) -> None:
    with pytest.warns(SpawnWarning, match="project-scope MCP"):
        assert adapter.add_mcp(tmp_path, _mcp()) == []
    assert not (tmp_path / ".hermes" / "mcp.json").exists()
    with pytest.warns(SpawnWarning):
        adapter.remove_mcp(tmp_path, ["spectask-search"])


def test_agent_ignore_unsupported_warns(tmp_path: Path, adapter: HermesAdapter) -> None:
    with pytest.warns(SpawnWarning):
        adapter.add_agent_ignore(tmp_path, ["secret/*"])
    with pytest.warns(SpawnWarning):
        adapter.remove_agent_ignore(tmp_path, ["secret/*"])


def test_entry_point_creates_and_replaces(tmp_path: Path, adapter: HermesAdapter) -> None:
    assert adapter.rewrite_entry_point(tmp_path, "first prompt") == ".hermes.md"
    ep = tmp_path / ".hermes.md"
    text = ep.read_text(encoding="utf-8")
    assert "first prompt" in text
    assert SPAWN_BLOCK_START in text
    assert adapter.rewrite_entry_point(tmp_path, "second prompt") == ".hermes.md"
    text = ep.read_text(encoding="utf-8")
    assert "second prompt" in text and "first prompt" not in text


def test_finalize_removes_vacant_hermes(tmp_path: Path, adapter: HermesAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    adapter.remove_skills(tmp_path, rendered)
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".hermes").exists()
