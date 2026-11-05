"""Tests for the Cline IDE adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from spawn_cli.ide.cline import ClineAdapter
from spawn_cli.models.mcp import McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> ClineAdapter:
    return ClineAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Execute approved spectasks.",
        content="# body\n",
        hints=["Prefer spectask steps in order."],
    )


def test_detect_markers(tmp_path: Path, adapter: ClineAdapter) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".cline").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True
    for marker in (".clinerules", ".clineignore"):
        d = tmp_path / f"m-{marker}"
        d.mkdir()
        (d / marker).touch()
        assert adapter.detect(d).used_in_repo is True


def test_capabilities(tmp_path: Path, adapter: ClineAdapter) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "unsupported"
    assert caps.agent_ignore == "native"
    assert caps.entry_point == "agents-md"


def test_add_and_remove_skills(tmp_path: Path, adapter: ClineAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill("My Skill")])
    path = tmp_path / ".cline" / "skills" / "my-skill" / "SKILL.md"
    assert path.is_file()
    assert rendered == [{"skill": "My Skill", "path": ".cline/skills/my-skill/SKILL.md"}]
    text = path.read_text(encoding="utf-8")
    assert "name: my-skill" in text  # frontmatter name == directory name (Cline rule)
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


def test_remove_skills_keeps_extra_files(tmp_path: Path, adapter: ClineAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    skill_dir = tmp_path / ".cline" / "skills" / "spectask-execute"
    (skill_dir / "extra.md").write_text("resource", encoding="utf-8")
    adapter.remove_skills(tmp_path, rendered)
    assert not (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "extra.md").is_file()  # user resource retained, dir not pruned


def test_add_skills_warns_on_overwrite(tmp_path: Path, adapter: ClineAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill()])
    with pytest.warns(UserWarning, match="Overwriting"):
        adapter.add_skills(tmp_path, [_skill()])


def test_add_mcp_unsupported(tmp_path: Path, adapter: ClineAdapter) -> None:
    mcp = NormalizedMcp(
        servers=[
            {
                "name": "spectask-search",
                "extension": "spectask",
                "transport": McpTransport(type="stdio", command="uvx"),
            }
        ]
    )
    with pytest.warns(UserWarning, match="project-scope MCP"):
        assert adapter.add_mcp(tmp_path, mcp) == []
    assert not (tmp_path / ".cline" / "mcp.json").exists()
    with pytest.warns(UserWarning):
        adapter.remove_mcp(tmp_path, ["spectask-search"])


def test_agent_ignore_roundtrip(tmp_path: Path, adapter: ClineAdapter) -> None:
    ignore = tmp_path / ".clineignore"
    ignore.write_text("user-secret/**\n", encoding="utf-8")
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "user-secret/**" in text
    assert "spawn/.core/**" in text
    adapter.remove_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "spawn/.core/**" not in text
    assert "user-secret/**" in text


def test_agent_ignore_idempotent(tmp_path: Path, adapter: ClineAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = (tmp_path / ".clineignore").read_text(encoding="utf-8")
    assert text.count("spawn/.core/**") == 1  # re-adding is a no-op


def test_legacy_ignore_block_migrates(tmp_path: Path, adapter: ClineAdapter) -> None:
    ignore = tmp_path / ".clineignore"
    ignore.write_text(
        "# spawn:start\nspawn/.core/**\n# spawn:end\n", encoding="utf-8"
    )
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "# spawn:core:start" in text  # legacy single block migrated to split regions


def test_split_ignore_and_clear(tmp_path: Path, adapter: ClineAdapter) -> None:
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["ext/**"])
    text = (tmp_path / ".clineignore").read_text(encoding="utf-8")
    assert "# spawn:core:" in text and "# spawn:ext:" in text
    adapter.clear_spawn_agent_ignore(tmp_path)
    text = (tmp_path / ".clineignore").read_text(encoding="utf-8")
    assert "spawn/.core/**" not in text and "ext/**" not in text


def test_entry_point_creates_and_replaces(tmp_path: Path, adapter: ClineAdapter) -> None:
    assert adapter.rewrite_entry_point(tmp_path, "first prompt") == "AGENTS.md"
    ep = tmp_path / "AGENTS.md"
    assert "first prompt" in ep.read_text(encoding="utf-8")
    ep.write_text(
        "# user header\n<!-- spawn:start -->\nold prompt\n<!-- spawn:end -->\n",
        encoding="utf-8",
    )
    assert adapter.rewrite_entry_point(tmp_path, "second prompt") == "AGENTS.md"
    text = ep.read_text(encoding="utf-8")
    assert "# user header" in text
    assert "old prompt" not in text and "second prompt" in text


def test_finalize_removes_vacant_cline(tmp_path: Path, adapter: ClineAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.remove_skills(tmp_path, rendered)
    adapter.clear_spawn_agent_ignore(tmp_path)
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".cline").exists()
    assert not (tmp_path / ".clineignore").exists()


def test_finalize_keeps_user_content(tmp_path: Path, adapter: ClineAdapter) -> None:
    (tmp_path / ".cline" / "rules").mkdir(parents=True)
    (tmp_path / ".cline" / "rules" / "keep.md").write_text("rule", encoding="utf-8")
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    ignore = tmp_path / ".clineignore"
    assert "user-secret/**" not in ignore.read_text(encoding="utf-8")
    with ignore.open("a", encoding="utf-8") as f:
        f.write("user-secret/**\n")  # user line appended after the spawn block
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert (tmp_path / ".cline" / "rules" / "keep.md").is_file()
    assert "user-secret/**" in ignore.read_text(encoding="utf-8")
