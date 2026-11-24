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
    ClineAdapter,
    CodexAdapter,
    CursorAdapter,
    DetectResult,
    GeminiCliAdapter,
    GitHubCopilotAdapter,
    HermesAdapter,
    IdeCapabilities,
    JunieAdapter,
    KiloCodeAdapter,
    MimoCodeAdapter,
    OpenCodeAdapter,
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
    assert isinstance(get("cline"), ClineAdapter)
    assert get("cline").key == "cline"
    assert isinstance(get("hermes"), HermesAdapter)
    assert get("hermes").key == "hermes"
    assert isinstance(get("kilo-code"), KiloCodeAdapter)
    assert get("kilo-code").key == "kilo-code"


def test_get_alias() -> None:
    a = get("claude")
    assert a.key == "claude-code"
    assert isinstance(a, ClaudeCodeAdapter)
    g = get("gemini")
    assert g.key == "gemini-cli"
    assert isinstance(g, GeminiCliAdapter)
    m = get("mimo")
    assert m.key == "mimo-code"
    assert isinstance(m, MimoCodeAdapter)
    k = get("kilo")
    assert k.key == "kilo-code"
    assert isinstance(k, KiloCodeAdapter)


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
    assert "mimo-code" in out


def test_mimo_code_in_supported_ides(tmp_path: Path) -> None:
    (tmp_path / ".mimocode").mkdir()
    assert "mimo-code" in detect_supported_ides(tmp_path)


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
    assert "spawn/navigation.yaml" not in md
    idx_body = md.index("Skill body line.")
    idx_mand = md.index("Mandatory reads:")
    assert idx_body < idx_mand
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
        ),
        entry_file="AGENTS.md",
    )
    idx_body = md.index("body")
    idx_mand = md.index("Mandatory reads:")
    idx_ctx = md.index("Contextual reads:")
    assert idx_body < idx_mand < idx_ctx
    assert "- `spec/main.md` - Main spec" in md
    assert "- `doc/hla.md` - HLA" in md
    assert "read `AGENTS.md` first" in md
    assert "spawn/navigation.yaml" not in md


def test_render_skill_md_entry_instruction() -> None:
    from spawn_cli.models.skill import SkillFileRef, SkillMetadata

    skill = SkillMetadata(
        name="s",
        description="d",
        content="body",
        required_read=[SkillFileRef(file="a.md", description="ad")],
        auto_read=[],
        hints=[],
    )
    md = render_skill_md(
        SkillMetadata(
            name="s",
            description="d",
            content="body",
            required_read=[SkillFileRef(file="a.md", description="ad")],
            auto_read=[],
            hints=["alpha"],
        ),
        "AGENTS.md",
    )
    assert "read `AGENTS.md` first" in md
    idx_body = md.index("body")
    idx_entry = md.index("Before this skill")
    idx_hints = md.index("- alpha")
    idx_mand = md.index("Mandatory reads:")
    assert idx_body < idx_entry < idx_hints < idx_mand
    assert "spawn/navigation.yaml" not in md
    md_no_entry = render_skill_md(skill)
    assert "AGENTS.md" not in md_no_entry


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
    idx_hints = md.index("- alpha")
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


def test_rewrite_managed_block_backslash_replacement(tmp_path: Path) -> None:
    # Entry-point prompts embed navigation.yaml content; "\" (e.g. \u in a
    # description) must not be parsed as re.sub template escapes (task 34 fixup).
    f = tmp_path / "AGENTS.md"
    f.write_text(
        f"before\n{SPAWN_BLOCK_START}\nold \\g1 old\n{SPAWN_BLOCK_END}\nafter\n",
        encoding="utf-8",
    )
    prompt = "safe UTF-8 text without \\u escapes"
    rewrite_managed_block(f, prompt)
    text = f.read_text(encoding="utf-8")
    assert prompt in text
    assert "old" not in text


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


ADAPTER_ENTRY_FILES = [
    (ClaudeCodeAdapter, "CLAUDE.md"),
    (ClineAdapter, "AGENTS.md"),
    (CodexAdapter, "AGENTS.md"),
    (CursorAdapter, "AGENTS.md"),
    (GeminiCliAdapter, "GEMINI.md"),
    (GitHubCopilotAdapter, ".github/copilot-instructions.md"),
    (HermesAdapter, ".hermes.md"),
    (JunieAdapter, "AGENTS.md"),
    (KiloCodeAdapter, "AGENTS.md"),
    (MimoCodeAdapter, "AGENTS.md"),
    (OpenCodeAdapter, "AGENTS.md"),
    (WindsurfAdapter, "AGENTS.md"),
]


@pytest.mark.parametrize(
    ("adapter_cls", "entry_file"),
    ADAPTER_ENTRY_FILES,
    ids=lambda x: x if isinstance(x, str) else x.__name__,
)
def test_adapter_renders_entry_instruction(adapter_cls, entry_file, tmp_path: Path) -> None:
    from spawn_cli.models.skill import SkillMetadata

    adapter = adapter_cls()
    results = adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="s", description="d", content="Body.")],
    )
    skill_path = tmp_path / results[0]["path"]
    text = skill_path.read_text(encoding="utf-8")
    assert f"read `{entry_file}` first" in text
    assert "spawn/navigation.yaml" not in text
