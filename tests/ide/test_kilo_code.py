"""Tests for the Kilo Code IDE adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide.kilo_code import KiloCodeAdapter, _sanitize_skill_name
from spawn_cli.models.mcp import McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> KiloCodeAdapter:
    return KiloCodeAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Execute approved spectasks.",
        content="# body\n",
        hints=["Prefer spectask steps in order."],
    )


def _stdio_mcp(name: str = "srv") -> NormalizedMcp:
    return NormalizedMcp(
        servers=[
            {
                "name": name,
                "extension": "spectask",
                "transport": McpTransport(type="stdio", command="uvx"),
            }
        ]
    )


# detect ---------------------------------------------------------------------


def test_detect_markers(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".kilo").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True
    for marker, make_dir in ((".kilocode", True), ("kilo.json", False), ("kilo.jsonc", False)):
        d = tmp_path / f"m-{marker}"
        d.mkdir()
        if make_dir:
            (d / marker).mkdir()
        else:
            (d / marker).touch()
        assert adapter.detect(d).used_in_repo is True


def test_capabilities(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "project"
    assert caps.agent_ignore == "native"
    assert caps.entry_point == "agents-md"


# skills ---------------------------------------------------------------------


def test_add_and_remove_skills(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill("My Skill")])
    path = tmp_path / ".kilo" / "skills" / "my-skill" / "SKILL.md"
    assert path.is_file()
    assert rendered == [{"skill": "My Skill", "path": ".kilo/skills/my-skill/SKILL.md"}]
    text = path.read_text(encoding="utf-8")
    assert "name: my-skill" in text  # frontmatter name == directory name (Kilo rule)
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


def test_sanitize_skill_name() -> None:
    assert _sanitize_skill_name("a.b_c") == "a-b-c"  # dots/underscores -> hyphens (rule 04)
    assert _sanitize_skill_name("a--b") == "a-b"
    long = "x" * 80
    sanitized = _sanitize_skill_name(long)
    assert len(sanitized) == 64
    assert not sanitized.endswith("-")


def test_remove_skills_keeps_extra_files(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    skill_dir = tmp_path / ".kilo" / "skills" / "spectask-execute"
    (skill_dir / "extra.md").write_text("resource", encoding="utf-8")
    adapter.remove_skills(tmp_path, rendered)
    assert not (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "extra.md").is_file()  # user resource retained, dir not pruned


def test_add_skills_warns_on_overwrite(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill()])
    with pytest.warns(SpawnWarning, match="Overwriting"):
        adapter.add_skills(tmp_path, [_skill()])


# mcp ------------------------------------------------------------------------


def test_add_mcp_and_remove_mcp(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    adapter.add_mcp(tmp_path, _stdio_mcp("srv"))
    cfg = tmp_path / ".kilo" / "kilo.json"
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["mcp"]["srv"] == {
        "type": "local",
        "command": ["uvx"],
        "enabled": True,
    }
    adapter.remove_mcp(tmp_path, ["srv"])
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "mcp" not in data  # empty mcp key is pruned
    assert cfg.read_text(encoding="utf-8").strip() == "{}"  # file left as {}


def test_mcp_unparseable_errors_before_mutation(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    cfg = tmp_path / ".kilo" / "kilo.json"
    cfg.parent.mkdir()
    cfg.write_text("{ not json", encoding="utf-8")
    with pytest.raises(SpawnError):
        adapter.add_mcp(tmp_path, _stdio_mcp("srv"))
    assert cfg.read_text(encoding="utf-8") == "{ not json"  # rule 05: no partial mutation


def test_jsonc_variant_warns(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    (tmp_path / ".kilo").mkdir()
    (tmp_path / ".kilo" / "kilo.jsonc").write_text("{}", encoding="utf-8")
    with pytest.warns(SpawnWarning, match="kilo.json"):
        adapter.add_mcp(tmp_path, _stdio_mcp("srv"))


# agent ignore ---------------------------------------------------------------


def test_agent_ignore_roundtrip(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    ignore = tmp_path / ".kilocodeignore"
    ignore.write_text("user-secret/**\n", encoding="utf-8")
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "user-secret/**" in text
    assert "spawn/.core/**" in text
    adapter.remove_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "spawn/.core/**" not in text
    assert "user-secret/**" in text


def test_agent_ignore_idempotent(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = (tmp_path / ".kilocodeignore").read_text(encoding="utf-8")
    assert text.count("spawn/.core/**") == 1  # re-adding is a no-op


def test_legacy_ignore_block_migrates(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    ignore = tmp_path / ".kilocodeignore"
    ignore.write_text(
        "# spawn:start\nspawn/.core/**\n# spawn:end\n", encoding="utf-8"
    )
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    text = ignore.read_text(encoding="utf-8")
    assert "# spawn:core:start" in text  # legacy single block migrated to split regions


def test_split_ignore_and_clear(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["ext/**"])
    text = (tmp_path / ".kilocodeignore").read_text(encoding="utf-8")
    assert "# spawn:core:" in text and "# spawn:ext:" in text
    adapter.clear_spawn_agent_ignore(tmp_path)
    text = (tmp_path / ".kilocodeignore").read_text(encoding="utf-8")
    assert "spawn/.core/**" not in text and "ext/**" not in text


# entry point ----------------------------------------------------------------


def test_entry_point_creates_and_replaces(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
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


# vacancy cleanup ------------------------------------------------------------


def test_finalize_removes_vacant_kilo(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.remove_skills(tmp_path, rendered)
    adapter.clear_spawn_agent_ignore(tmp_path)
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".kilo").exists()
    assert not (tmp_path / ".kilocodeignore").exists()


@pytest.mark.parametrize("payload", [{}, {"mcp": {}}])
def test_finalize_removes_vacant_kilo_json(payload: dict, tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    cfg = tmp_path / ".kilo" / "kilo.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(json.dumps(payload), encoding="utf-8")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not cfg.exists()
    assert not (tmp_path / ".kilo").exists()  # dir drops when otherwise empty


def test_finalize_keeps_user_content(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    (tmp_path / ".kilo" / "rules").mkdir(parents=True)
    (tmp_path / ".kilo" / "rules" / "keep.md").write_text("rule", encoding="utf-8")
    adapter.add_agent_ignore(tmp_path, ["spawn/.core/**"])
    ignore = tmp_path / ".kilocodeignore"
    with ignore.open("a", encoding="utf-8") as f:
        f.write("user-secret/**\n")  # user line appended after the spawn block
    cfg = tmp_path / ".kilo" / "kilo.json"
    cfg.write_text(json.dumps({"instructions": ["be nice"]}), encoding="utf-8")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert (tmp_path / ".kilo" / "rules" / "keep.md").is_file()
    assert "user-secret/**" in ignore.read_text(encoding="utf-8")
    assert cfg.is_file()  # user key keeps kilo.json alive


def test_finalize_removes_vacant_legacy_kilocode_dir(tmp_path: Path, adapter: KiloCodeAdapter) -> None:
    (tmp_path / ".kilocode").mkdir()
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".kilocode").exists()
