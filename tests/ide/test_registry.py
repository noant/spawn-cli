from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from spawn_cli.core.errors import SpawnError
from spawn_cli.core.low_level import CANONICAL_IDE_KEYS
from spawn_cli.ide import (
    CORE_IGNORE_BLOCK_END,
    CORE_IGNORE_BLOCK_START,
    EXT_IGNORE_BLOCK_END,
    EXT_IGNORE_BLOCK_START,
    IGNORE_BLOCK_END,
    IGNORE_BLOCK_START,
    SPAWN_BLOCK_END,
    SPAWN_BLOCK_START,
    ClaudeCodeAdapter,
    CodexAdapter,
    CursorAdapter,
    DetectResult,
    GeminiCliAdapter,
    GitHubCopilotAdapter,
    IdeCapabilities,
    StubAdapter,
    WindsurfAdapter,
    detect_supported_ides,
    get,
    normalize_skill_name,
    register,
    remove_ignore_block,
    render_skill_md,
    rewrite_ignore_block,
    rewrite_managed_block,
)


def test_get_known_adapter() -> None:
    assert isinstance(get("cursor"), CursorAdapter)
    assert get("cursor").key == "cursor"
    assert isinstance(get("codex"), CodexAdapter)
    assert get("codex").key == "codex"
    assert isinstance(get("github-copilot"), GitHubCopilotAdapter)
    assert isinstance(get("windsurf"), WindsurfAdapter)


def test_get_alias() -> None:
    a = get("claude")
    assert a.key == "claude-code"
    assert isinstance(a, ClaudeCodeAdapter)
    g = get("gemini")
    assert g.key == "gemini-cli"
    assert isinstance(g, GeminiCliAdapter)


def test_get_unknown_raises() -> None:
    with pytest.raises(SpawnError, match="Unknown IDE"):
        get("not-an-ide")


def test_register_rejects_unknown_key() -> None:
    cap = IdeCapabilities("native", "project", "project", "agents-md")
    bad = StubAdapter("cursor", cap)
    bad.key = "not-a-canonical-ide"
    with pytest.raises(SpawnError, match="Cannot register unknown IDE key"):
        register(bad)


def test_detect_supported_ides(tmp_path: Path) -> None:
    out = detect_supported_ides(tmp_path)
    assert list(out.keys()) == list(CANONICAL_IDE_KEYS)
    for key in CANONICAL_IDE_KEYS:
        assert isinstance(out[key], DetectResult)
        assert out[key].used_in_repo is False
        assert isinstance(out[key].capabilities, IdeCapabilities)


def test_normalize_skill_name() -> None:
    assert normalize_skill_name("  Foo Bar  ") == "foo-bar"
    assert normalize_skill_name("UPPER") == "upper"
    assert normalize_skill_name("a!!b__c") == "ab__c"
    assert normalize_skill_name("a---b") == "a-b"


def test_render_skill_md_minimal() -> None:
    from spawn_cli.models.skill import SkillMetadata

    md = render_skill_md(
        SkillMetadata(
            name="spectask-run",
            description="Run tasks.",
            content="Skill body line.",
        )
    )
    assert "---\nname: spectask-run\ndescription: Run tasks.\n---" in md
    assert "Read `spawn/navigation.yaml` first." not in md
    idx_body = md.index("Skill body line.")
    idx_mand = md.index("Mandatory reads:")
    assert idx_body < idx_mand
    assert "- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual)." in md
    assert md.index("- `spawn/navigation.yaml`") > md.rindex("Mandatory reads:")
    assert "Contextual reads:" not in md


def test_render_skill_md_full() -> None:
    from spawn_cli.models.skill import SkillFileRef, SkillMetadata

    md = render_skill_md(
        SkillMetadata(
            name="n",
            description="d",
            content="body",
            required_read=[
                SkillFileRef(file="spec/main.md", description="Main spec"),
            ],
            auto_read=[
                SkillFileRef(file="doc/hla.md", description="HLA"),
            ],
        )
    )
    idx_body = md.index("body")
    idx_mand = md.index("Mandatory reads:")
    idx_ctx = md.index("Contextual reads:")
    assert idx_body < idx_mand < idx_ctx
    assert "- `spec/main.md` - Main spec" in md
    assert "- `doc/hla.md` - HLA" in md
    assert "- `spawn/navigation.yaml` - Merged Spawn navigation (read-required, read-contextual)." in md
    mand = md.split("Contextual reads:", 1)[0]
    assert mand.index("spec/main.md") < mand.index("spawn/navigation.yaml")


def test_render_skill_md_mandatory_nav_reordered() -> None:
    from spawn_cli.models.skill import SkillFileRef, SkillMetadata

    md = render_skill_md(
        SkillMetadata(
            name="a",
            description="b",
            content="c",
            required_read=[
                SkillFileRef(file="spawn/navigation.yaml", description="Custom nav"),
                SkillFileRef(file="spec/main.md", description="Main"),
            ],
            auto_read=[],
        )
    )
    mand = md.split("Contextual reads:")[0] if "Contextual reads:" in md else md
    assert mand.index("spec/main.md") < mand.index("spawn/navigation.yaml")
    assert "- `spawn/navigation.yaml` - Custom nav" in md


def test_render_skill_md_mandatory_nav_deduped() -> None:
    from spawn_cli.models.skill import SkillFileRef, SkillMetadata

    md = render_skill_md(
        SkillMetadata(
            name="a",
            description="b",
            content="c",
            required_read=[
                SkillFileRef(file="spawn/navigation.yaml", description="First"),
                SkillFileRef(file=r"spawn\navigation.yaml", description="Second"),
            ],
            auto_read=[],
        )
    )
    assert md.count("spawn/navigation.yaml") + md.count(r"spawn\navigation.yaml") == 1
    assert " - First" in md
    assert "Second" not in md


def test_render_skill_md_hints_before_mandatory_reads() -> None:
    from spawn_cli.models.skill import SkillFileRef, SkillMetadata

    md = render_skill_md(
        SkillMetadata(
            name="n",
            description="d",
            content="body",
            hints=["alpha", "beta"],
            required_read=[
                SkillFileRef(file="spec/main.md", description="Main spec"),
            ],
            auto_read=[],
        )
    )
    idx_body = md.index("body")
    idx_hints = md.index("Hints:")
    idx_mand = md.index("Mandatory reads:")
    assert idx_body < idx_hints < idx_mand
    assert "- alpha" in md and "- beta" in md
    sect = md.split("Mandatory reads:", 1)[0]
    assert sect.rstrip().endswith("beta")


def test_rewrite_managed_block_creates(tmp_path: Path) -> None:
    f = tmp_path / "AGENTS.md"
    rewrite_managed_block(f, "hello")
    text = f.read_text(encoding="utf-8")
    assert text.startswith(f"{SPAWN_BLOCK_START}\nhello\n{SPAWN_BLOCK_END}\n")


def test_rewrite_managed_block_replaces(tmp_path: Path) -> None:
    f = tmp_path / "AGENTS.md"
    f.write_text(
        f"before\n{SPAWN_BLOCK_START}\nold\n{SPAWN_BLOCK_END}\nafter\n",
        encoding="utf-8",
    )
    rewrite_managed_block(f, "new")
    text = f.read_text(encoding="utf-8")
    assert "before\n" in text
    assert f"{SPAWN_BLOCK_START}\nnew\n{SPAWN_BLOCK_END}" in text
    assert "after\n" in text
    assert "old" not in text


def test_rewrite_ignore_block_add(tmp_path: Path) -> None:
    f = tmp_path / ".cursorignore"
    f.write_text("user-line\n", encoding="utf-8")
    rewrite_ignore_block(f, ["a", "b"])
    text = f.read_text(encoding="utf-8")
    assert "user-line" in text
    assert IGNORE_BLOCK_START in text
    assert "a" in text and "b" in text
    assert IGNORE_BLOCK_END in text


def test_rewrite_ignore_block_replace(tmp_path: Path) -> None:
    f = tmp_path / ".cursorignore"
    f.write_text(
        f"top\n{IGNORE_BLOCK_START}\nold1\nold2\n{IGNORE_BLOCK_END}\nbottom\n",
        encoding="utf-8",
    )
    rewrite_ignore_block(f, ["g1"])
    text = f.read_text(encoding="utf-8")
    assert "top\n" in text
    assert "bottom\n" in text
    assert "g1" in text
    assert "old1" not in text


def test_remove_ignore_block(tmp_path: Path) -> None:
    f = tmp_path / ".cursorignore"
    f.write_text(
        f"keep-top\n{IGNORE_BLOCK_START}\ngone\n{IGNORE_BLOCK_END}\nkeep-bottom\n",
        encoding="utf-8",
    )
    remove_ignore_block(f, [])
    text = f.read_text(encoding="utf-8")
    assert "keep-top" in text
    assert "keep-bottom" in text
    assert IGNORE_BLOCK_START not in text


def test_cursor_dual_ignore_idempotent(tmp_path: Path) -> None:
    adapter = CursorAdapter()
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["logs/**"])
    adapter.rewrite_core_agent_ignore(tmp_path, ["spawn/.core/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["logs/**"])
    text = (tmp_path / ".cursorignore").read_text(encoding="utf-8")
    assert text.count("spawn/.core/**") == 1
    assert text.count("logs/**") == 1
    assert CORE_IGNORE_BLOCK_START in text
    assert EXT_IGNORE_BLOCK_START in text


def test_legacy_single_block_migrates_on_rewrite(tmp_path: Path) -> None:
    f = tmp_path / ".cursorignore"
    f.write_text(
        f"top\n{IGNORE_BLOCK_START}\nlegacy-line\n{IGNORE_BLOCK_END}\nbottom\n",
        encoding="utf-8",
    )
    CursorAdapter().rewrite_core_agent_ignore(tmp_path, ["c/core/**"])
    CursorAdapter().rewrite_extension_agent_ignore(tmp_path, ["e/ext/**"])
    text = f.read_text(encoding="utf-8")
    assert "legacy-line" not in text
    assert "c/core/**" in text
    assert "e/ext/**" in text
    assert IGNORE_BLOCK_START not in text


def test_clear_spawn_agent_ignore_keeps_user_lines(tmp_path: Path) -> None:
    adapter = CursorAdapter()
    adapter.rewrite_core_agent_ignore(tmp_path, ["a/**"])
    adapter.rewrite_extension_agent_ignore(tmp_path, ["b/**"])
    p = tmp_path / ".cursorignore"
    prev = p.read_text(encoding="utf-8")
    p.write_text("user\n" + prev, encoding="utf-8")
    adapter.clear_spawn_agent_ignore(tmp_path)
    text = p.read_text(encoding="utf-8")
    assert "user\n" in text
    assert CORE_IGNORE_BLOCK_START not in text


def test_stub_add_skills_warns() -> None:
    cap = IdeCapabilities("native", "project", "project", "agents-md")
    stub = StubAdapter("cursor", cap)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        stub.add_skills(Path("."), [])
        assert len(w) == 1
        assert "cursor" in str(w[0].message)
        assert "skill rendering not yet implemented" in str(w[0].message)
