from __future__ import annotations

import time
import uuid
import warnings
from importlib import resources
from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.io.yaml_io import configure_yaml_dump, load_yaml

YAML_W = YAML(typ="safe")
configure_yaml_dump(YAML_W)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        YAML_W.dump(data, fh)


def test_list_extensions_empty(tmp_path: Path) -> None:
    ll.init(tmp_path)
    assert ll.list_extensions(tmp_path) == []


def test_list_extensions(tmp_path: Path) -> None:
    ll.init(tmp_path)
    extend = tmp_path / "spawn" / ".extend"
    (extend / "alpha").mkdir(parents=True)
    (extend / "beta").mkdir(parents=True)
    assert ll.list_extensions(tmp_path) == ["alpha", "beta"]


def test_add_remove_ide_to_list(tmp_path: Path) -> None:
    ll.init(tmp_path)
    ll.add_ide_to_list(tmp_path, "cursor")
    ll.add_ide_to_list(tmp_path, "cursor")
    assert ll.list_ides(tmp_path) == ["cursor"]
    ll.add_ide_to_list(tmp_path, "codex")
    assert ll.list_ides(tmp_path) == ["cursor", "codex"]
    ll.remove_ide_from_list(tmp_path, "cursor")
    assert ll.list_ides(tmp_path) == ["codex"]


def test_remove_ide_metadata_dir(tmp_path: Path) -> None:
    ll.init(tmp_path)
    md = tmp_path / "spawn" / ".metadata" / "cursor"
    md.mkdir(parents=True)
    (md / "stub.yaml").write_text("x: 1\n", encoding="utf-8")
    ll.remove_ide_metadata_dir(tmp_path, "cursor")
    assert not md.exists()


def test_prune_metadata_temp(tmp_path: Path) -> None:
    ll.init(tmp_path)
    parent = tmp_path / "spawn" / ".metadata" / "temp"
    parent.mkdir(parents=True)
    uid_old = str(uuid.uuid4())
    uid_recent = str(uuid.uuid4())
    old_d = parent / uid_old
    keep_d = parent / uid_recent
    old_d.mkdir()
    keep_d.mkdir()
    old_ts = time.time() - ll.METADATA_TEMP_MAX_AGE_SECONDS - 3600
    recent_ts = time.time() - 100
    import os

    os.utime(old_d, (old_ts, old_ts))
    os.utime(keep_d, (recent_ts, recent_ts))
    ll.prune_metadata_temp(parent, max_age_seconds=ll.METADATA_TEMP_MAX_AGE_SECONDS, reserved=uid_recent)
    assert not old_d.exists()
    assert keep_d.exists()


def test_get_required_read_global(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "x",
        "version": "1.0.0",
        "schema": 1,
        "files": {
            "doc/a.md": {
                "description": "A doc",
                "mode": "static",
                "globalRead": "required",
                "localRead": "no",
            },
        },
    }
    ext = tmp_path / "spawn" / ".extend" / "spectask"
    _write_yaml(ext / "config.yaml", cfg)
    refs = ll.get_required_read_global(tmp_path, "spectask")
    assert len(refs) == 1
    assert refs[0].file == "doc/a.md"
    assert refs[0].description == "A doc"


def test_generate_skills_metadata(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {
            "glob.md": {
                "description": "Global",
                "mode": "static",
                "globalRead": "required",
                "localRead": "no",
            },
            "ctx.md": {
                "description": "CTX",
                "mode": "static",
                "globalRead": "auto",
                "localRead": "no",
            },
        },
        "skills": {
            "two.md": {
                "required-read": ["extra.md"],
            },
        },
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "one.md").write_text("# one\n", encoding="utf-8")
    (skill_dir / "two.md").write_text("# two\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)

    meta = ll.generate_skills_metadata(tmp_path, "spectask")
    by_name = {m.name: m for m in meta}
    one = by_name["one"]
    paths_one = [r.file for r in one.required_read]
    assert paths_one.count("glob.md") == 1
    two = by_name["two"]
    paths_two_set = {r.file for r in two.required_read}
    assert paths_two_set == {"extra.md", "glob.md"}

    globs = [r.file for r in one.auto_read]
    assert globs.count("ctx.md") == 1


def test_generate_skills_metadata_required_vs_contextual_dedup(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {
            "mixed-auto-local-required.md": {
                "description": "globalRead auto + localRead required",
                "mode": "static",
                "globalRead": "auto",
                "localRead": "required",
            },
            "mixed-global-required-local-auto.md": {
                "description": "globalRead required + localRead auto",
                "mode": "static",
                "globalRead": "required",
                "localRead": "auto",
            },
            "ctx.md": {
                "description": "context only",
                "mode": "static",
                "globalRead": "auto",
                "localRead": "auto",
            },
        },
        "skills": {},
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "skill.md").write_text("# skill\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)

    meta = ll.generate_skills_metadata(tmp_path, "spectask")
    m = next(x for x in meta if x.name == "skill")
    req_paths = {r.file for r in m.required_read}
    auto_paths = {r.file for r in m.auto_read}
    assert req_paths == {
        "mixed-auto-local-required.md",
        "mixed-global-required-local-auto.md",
    }
    assert auto_paths == {"ctx.md"}
    assert not (req_paths & auto_paths)


def test_generate_skills_metadata_required_paths_normalized_dedup(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {
            "glob.md": {
                "description": "Global",
                "mode": "static",
                "globalRead": "required",
                "localRead": "no",
            },
            "ctx.md": {
                "description": "context only",
                "mode": "static",
                "globalRead": "auto",
                "localRead": "no",
            },
        },
        "skills": {
            "two.md": {
                "required-read": ["glob.md", "glob.md", "doc\\dup.md", "doc/dup.md"],
            },
        },
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "two.md").write_text("# two\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)

    m = next(x for x in ll.generate_skills_metadata(tmp_path, "spectask") if x.name == "two")
    req_norm = {ll._norm_read_path(r.file) for r in m.required_read}
    assert req_norm == {ll._norm_read_path("glob.md"), ll._norm_read_path("doc/dup.md")}
    assert len(m.required_read) == 2
    auto_norm = {ll._norm_read_path(r.file) for r in m.auto_read}
    assert auto_norm == {ll._norm_read_path("ctx.md")}
    assert not (req_norm & auto_norm)


def test_generate_skills_metadata_includes_navigation_rules_refs(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {},
        "skills": {"one.md": {}},
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "one.md").write_text("---\nname: one\n---\n\nbody\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)
    same_path = "spawn/rules/both.md"
    _write_yaml(
        tmp_path / "spawn" / "navigation.yaml",
        {
            "read-required": [
                {
                    "rules": [
                        {
                            "path": "spawn/rules/required.md",
                            "description": "Req rule.",
                        },
                        {"path": same_path, "description": "In required tier."},
                    ],
                },
            ],
            "read-contextual": [
                {
                    "rules": [
                        {
                            "path": "spawn/rules/context.md",
                            "description": "Ctx rule.",
                        },
                        {"path": same_path, "description": "Also in contextual (ignored)."},
                    ],
                },
            ],
        },
    )

    m = next(x for x in ll.generate_skills_metadata(tmp_path, "spectask") if x.name == "one")
    req_by = {ll._norm_read_path(r.file): r.description for r in m.required_read}
    assert ll._norm_read_path("spawn/rules/required.md") in req_by
    assert req_by[ll._norm_read_path("spawn/rules/required.md")] == "Req rule."
    assert ll._norm_read_path(same_path) in req_by
    auto_by = {ll._norm_read_path(r.file): r.description for r in m.auto_read}
    assert ll._norm_read_path("spawn/rules/context.md") in auto_by
    assert auto_by[ll._norm_read_path("spawn/rules/context.md")] == "Ctx rule."
    assert ll._norm_read_path(same_path) not in auto_by


def test_generate_skills_metadata_hints_merge_and_contextual_ignored(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {},
        "skills": {"one.md": {}},
        "hints": {"global": ["  global dup ", "global dup"], "local": ["local hint"]},
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "one.md").write_text("---\nname: one\n---\nbody\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)

    _write_yaml(
        tmp_path / "spawn" / "navigation.yaml",
        {
            "read-required": [
                {
                    "rules": [
                        {"path": "spawn/rules/r1.md", "description": "", "hint": "from required"},
                        {"path": "spawn/rules/r2.md", "description": "", "hint": "global dup"},
                    ],
                },
            ],
            "read-contextual": [
                {
                    "rules": [{"path": "spawn/rules/c1.md", "description": "", "hint": "contextual skipped"}],
                },
            ],
        },
    )

    m = next(x for x in ll.generate_skills_metadata(tmp_path, "spectask") if x.name == "one")
    assert m.hints
    joined = "\n".join(m.hints)
    assert joined.index("global dup") < joined.index("local hint")
    assert joined.index("local hint") < joined.index("from required")
    assert "contextual skipped" not in joined


def test_generate_skills_metadata_global_hints_from_all_extensions(tmp_path: Path) -> None:
    """hints.global behaves like cross-extension mandatory reads: every skill sees every pack's globals."""
    ll.init(tmp_path)
    extend = tmp_path / "spawn" / ".extend"

    def _minimal_cfg(name: str, **extra: Any) -> dict[str, Any]:
        return {
            "name": name,
            "version": "1.0.0",
            "schema": 1,
            "files": {},
            "skills": {"one.md": {}},
            **extra,
        }

    alfa_root = extend / "alfa"
    alfa_skill = alfa_root / "skills"
    alfa_skill.mkdir(parents=True)
    (alfa_skill / "one.md").write_text("---\nname: one\n---\na\n", encoding="utf-8")
    _write_yaml(
        alfa_root / "config.yaml",
        _minimal_cfg("alfa", hints={"global": ["from alfa"]}),
    )

    beta_root = extend / "betaext"
    beta_skill = beta_root / "skills"
    beta_skill.mkdir(parents=True)
    (beta_skill / "one.md").write_text("---\nname: one\n---\nb\n", encoding="utf-8")
    _write_yaml(
        beta_root / "config.yaml",
        _minimal_cfg(
            "betaext",
            hints={"global": ["from beta"], "local": ["only on beta skill"]},
        ),
    )

    _write_yaml(tmp_path / "spawn" / "navigation.yaml", {"read-required": [], "read-contextual": []})

    m_beta = next(x for x in ll.generate_skills_metadata(tmp_path, "betaext") if x.name == "one")
    m_alfa = next(x for x in ll.generate_skills_metadata(tmp_path, "alfa") if x.name == "one")

    beta_joined = "\n".join(m_beta.hints)
    assert beta_joined.index("from alfa") < beta_joined.index("from beta")
    assert beta_joined.index("from beta") < beta_joined.index("only on beta skill")

    alfa_joined = "\n".join(m_alfa.hints)
    assert "from alfa" in alfa_joined and "from beta" in alfa_joined
    assert "only on beta skill" not in alfa_joined


def test_generate_skills_metadata_skill_hint_per_hint_truncate_warns(tmp_path: Path) -> None:
    ll.init(tmp_path)
    long = "a" * 520
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {},
        "skills": {"one.md": {}},
        "hints": {"global": [long]},
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "one.md").write_text("---\nname: one\n---\nbody\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)
    _write_yaml(tmp_path / "spawn" / "navigation.yaml", {"read-required": [], "read-contextual": []})

    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        m = next(x for x in ll.generate_skills_metadata(tmp_path, "spectask") if x.name == "one")
    assert len(m.hints) == 1
    assert m.hints[0] == "a" * 512
    assert any(issubclass(w.category, SpawnWarning) and "512" in str(w.message) for w in wrec)


def test_generate_skills_metadata_combined_budget_adds_ellipsis_hint(tmp_path: Path) -> None:
    ll.init(tmp_path)
    pieces = []
    for i in range(20):
        pieces.append("-".join(["hint", str(i), "x" * 200]))
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {},
        "skills": {"one.md": {}},
        "hints": {"global": pieces},
    }
    root = tmp_path / "spawn" / ".extend" / "spectask"
    skill_dir = root / "skills"
    skill_dir.mkdir(parents=True)
    (skill_dir / "one.md").write_text("---\nname: one\n---\nbody\n", encoding="utf-8")
    _write_yaml(root / "config.yaml", cfg)
    _write_yaml(tmp_path / "spawn" / "navigation.yaml", {"read-required": [], "read-contextual": []})

    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        m = next(x for x in ll.generate_skills_metadata(tmp_path, "spectask") if x.name == "one")
    assert "..." in m.hints
    block = "Hints:\n" + "\n".join(f"- {h}" for h in m.hints)
    assert len(block) <= ll._SKILL_HINT_SECTION_COMBINED_MAX_CHARS
    assert any(issubclass(w.category, SpawnWarning) and "4096" in str(w.message) for w in wrec)


def test_rollup_hints_for_agents_excludes_local(tmp_path: Path) -> None:
    ll.init(tmp_path)
    ext = tmp_path / "spawn" / ".extend" / "spectask"
    ext.mkdir(parents=True)
    cfg = {
        "name": "spectask",
        "version": "1.0.0",
        "schema": 1,
        "files": {},
        "skills": {},
        "hints": {"global": ["g"], "local": ["loc"]},
    }
    _write_yaml(ext / "config.yaml", cfg)
    nav = ll.rollup_hints_for_agents(tmp_path)
    assert nav == ["g"]


def test_save_extension_navigation_contextual_omits_paths_in_required(tmp_path: Path) -> None:
    ll.init(tmp_path)
    from spawn_cli.models.skill import SkillFileRef

    ll.save_extension_navigation(
        tmp_path,
        "spectask",
        [SkillFileRef(file="spec/main.md", description="req")],
        [
            SkillFileRef(file=r"spec\main.md", description="ctx duplicate"),
            SkillFileRef(file="spec/other.md", description="ctx only"),
        ],
    )
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rq = next(g for g in nav["read-required"] if isinstance(g, dict) and g.get("ext") == "spectask")
    cq = next(g for g in nav["read-contextual"] if isinstance(g, dict) and g.get("ext") == "spectask")
    rq_paths = {ll._norm_read_path(e["path"]) for e in rq["files"]}
    cq_paths = {ll._norm_read_path(e["path"]) for e in cq["files"]}
    assert ll._norm_read_path("spec/main.md") in rq_paths
    assert ll._norm_read_path("spec/main.md") not in cq_paths
    assert ll._norm_read_path("spec/other.md") in cq_paths


def test_list_mcp(tmp_path: Path) -> None:
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    mcp = {
        "servers": [
            {
                "name": "test-srv",
                "transport": {
                    "type": "stdio",
                    "command": "uvx",
                    "args": ["tool"],
                    "cwd": ".",
                },
                "env": {},
                "capabilities": {"tools": True},
            },
        ]
    }
    _write_yaml(root / "config.yaml", {"name": "spectask", "version": "1.0.0", "schema": 1})
    import json

    mdir = root / "mcp"
    mdir.mkdir(parents=True)
    body = json.dumps(mcp)
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")

    nm = ll.list_mcp(tmp_path, "spectask")
    assert len(nm.servers) == 1
    assert nm.servers[0].name == "test-srv"
    assert nm.servers[0].extension == "spectask"


def test_list_mcp_empty_without_mcp_dir_ignores_root_json(tmp_path: Path) -> None:
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    _write_yaml(root / "config.yaml", {"name": "spectask", "version": "1.0.0", "schema": 1})
    (root / "mcp.json").write_text('{"servers": [{"name": "ignored"}]}', encoding="utf-8")
    nm = ll.list_mcp(tmp_path, "spectask")
    assert nm.servers == []


def test_list_mcp_raises_when_platform_file_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("spawn_cli.core.low_level.sys.platform", "linux")
    ll.init(tmp_path)
    root = tmp_path / "spawn" / ".extend" / "spectask"
    root.mkdir(parents=True)
    _write_yaml(root / "config.yaml", {"name": "spectask", "version": "1.0.0", "schema": 1})
    mdir = root / "mcp"
    mdir.mkdir(parents=True)
    import json

    (mdir / "windows.json").write_text(json.dumps({"servers": []}), encoding="utf-8")
    (mdir / "macos.json").write_text(json.dumps({"servers": []}), encoding="utf-8")
    with pytest.raises(SpawnError, match="missing MCP platform file"):
        ll.list_mcp(tmp_path, "spectask")


def test_mcp_host_platform_stem_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("spawn_cli.core.low_level.sys.platform", "freebsd14")
    with pytest.raises(SpawnError, match="unsupported platform"):
        ll.mcp_host_platform_stem()


def test_save_get_rendered_skills(tmp_path: Path) -> None:
    ll.init(tmp_path)
    rows = [{"skill": "a.md", "path": ".agents/skills/a/SKILL.md"}]
    ll.save_skills_rendered(tmp_path, "cursor", "spectask", rows)
    assert ll.get_rendered_skills(tmp_path, "cursor", "spectask") == rows


def test_save_get_rendered_mcp(tmp_path: Path) -> None:
    ll.init(tmp_path)
    ll.save_mcp_rendered(tmp_path, "cursor", "spectask", ["srv-a", "srv-b"])
    assert ll.get_rendered_mcp(tmp_path, "cursor", "spectask") == ["srv-a", "srv-b"]


def test_push_remove_global_gitignore(tmp_path: Path) -> None:
    git = tmp_path / ".gitignore"
    git.write_text("user-only\n", encoding="utf-8")
    ll.push_to_global_gitignore(tmp_path, ["spawn/.metadata/temp/**"])
    ll.push_to_global_gitignore(tmp_path, ["spawn/.metadata/temp/**"])
    lines = git.read_text(encoding="utf-8").splitlines()
    assert "# spawn:start" in lines
    hits = [ln for ln in lines if ln.strip() == "spawn/.metadata/temp/**"]
    assert len(hits) == 1
    ll.remove_from_global_gitignore(tmp_path, ["spawn/.metadata/temp/**"])
    text = git.read_text(encoding="utf-8")
    assert "spawn/.metadata/temp/**" not in text
    assert "user-only" in text


def test_save_extension_navigation_empty_removes_section(tmp_path: Path) -> None:
    ll.init(tmp_path)
    from spawn_cli.models.skill import SkillFileRef

    ll.save_extension_navigation(
        tmp_path,
        "spectask",
        [SkillFileRef(file="spec/main.md", description="spec")],
        [],
    )
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    assert any(isinstance(g, dict) and g.get("ext") == "spectask" for g in nav["read-required"])

    ll.save_extension_navigation(tmp_path, "spectask", [], [])
    nav2 = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    assert not any(isinstance(g, dict) and g.get("ext") == "spectask" for g in nav2["read-required"])


def test_save_rules_navigation_new_rule(tmp_path: Path) -> None:
    ll.init(tmp_path)
    rule_file = tmp_path / "spawn" / "rules" / "team.yaml"
    rule_file.parent.mkdir(parents=True, exist_ok=True)
    rule_file.write_text("key: val\n", encoding="utf-8")
    ll.save_rules_navigation(tmp_path)
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rules_grp = next(g for g in nav["read-required"] if isinstance(g, dict) and "rules" in g)
    paths = [e["path"] for e in rules_grp["rules"]]
    norm = Path(paths[0]).as_posix().replace("\\", "/")
    assert norm == "spawn/rules/team.yaml"


def test_save_rules_navigation_missing_rule_warns(tmp_path: Path) -> None:
    ll.init(tmp_path)
    nav_before = {"read-required": [{"rules": [{"path": "spawn/rules/missing.yaml", "description": "gone"}]}], "read-contextual": []}
    _write_yaml(tmp_path / "spawn" / "navigation.yaml", nav_before)
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        ll.save_rules_navigation(tmp_path)
    assert any(isinstance(w.message, SpawnWarning) for w in wrec)
    nav_after = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rules_grp = next(g for g in nav_after["read-required"] if isinstance(g, dict) and "rules" in g)
    assert rules_grp["rules"] == []


def test_save_extension_navigation_hints_roundtrip_and_contextual_omits_hints(tmp_path: Path) -> None:
    ll.init(tmp_path)
    from spawn_cli.models.skill import SkillFileRef

    ext = tmp_path / "spawn" / ".extend" / "spectask"
    ext.mkdir(parents=True)
    _write_yaml(
        ext / "config.yaml",
        {
            "name": "spectask",
            "version": "1.0.0",
            "schema": 1,
            "hints": {"global": ["  Alpha ", "Beta", "Beta"], "local": ["only skills"]},
            "files": {},
            "skills": {},
            "folders": {},
        },
    )
    ll.save_extension_navigation(
        tmp_path,
        "spectask",
        [SkillFileRef(file="spec/main.md", description="req")],
        [SkillFileRef(file="spec/other.md", description="ctx")],
    )
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rq = next(g for g in nav["read-required"] if isinstance(g, dict) and g.get("ext") == "spectask")
    cq = next(g for g in nav["read-contextual"] if isinstance(g, dict) and g.get("ext") == "spectask")
    assert rq["hints"] == ["Alpha", "Beta"]
    assert "hints" not in cq


def test_save_extension_navigation_oversized_global_hint_warns_and_truncates(tmp_path: Path) -> None:
    ll.init(tmp_path)
    from spawn_cli.models.skill import SkillFileRef

    long_hint = "x" * 513
    ext = tmp_path / "spawn" / ".extend" / "spectask"
    ext.mkdir(parents=True)
    _write_yaml(
        ext / "config.yaml",
        {
            "name": "spectask",
            "version": "1.0.0",
            "schema": 1,
            "hints": {"global": [long_hint]},
            "files": {},
            "skills": {},
            "folders": {},
        },
    )
    with warnings.catch_warnings(record=True) as wrec:
        warnings.simplefilter("always")
        ll.save_extension_navigation(
            tmp_path,
            "spectask",
            [SkillFileRef(file="spec/main.md", description="req")],
            [],
        )
    assert any(isinstance(w.message, SpawnWarning) for w in wrec)
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rq = next(g for g in nav["read-required"] if isinstance(g, dict) and g.get("ext") == "spectask")
    assert rq["hints"] == ["x" * 512]


def test_save_rules_navigation_preserves_hint_on_rules_rows(tmp_path: Path) -> None:
    ll.init(tmp_path)
    req_rule = tmp_path / "spawn" / "rules" / "req.md"
    req_rule.parent.mkdir(parents=True, exist_ok=True)
    req_rule.write_text("x\n", encoding="utf-8")
    ctx_rule = tmp_path / "spawn" / "rules" / "ctx.md"
    ctx_rule.write_text("y\n", encoding="utf-8")
    _write_yaml(
        tmp_path / "spawn" / "navigation.yaml",
        {
            "read-required": [
                {
                    "rules": [
                        {
                            "path": "spawn/rules/req.md",
                            "description": "Required.",
                            "hint": "Keep required concise.",
                        },
                    ],
                },
            ],
            "read-contextual": [
                {
                    "rules": [
                        {
                            "path": "spawn/rules/ctx.md",
                            "description": "Contextual.",
                            "hint": "Context hint preserved.",
                        },
                    ],
                },
            ],
        },
    )
    ll.save_rules_navigation(tmp_path)
    nav = YAML_W.load((tmp_path / "spawn" / "navigation.yaml").read_text(encoding="utf-8"))
    rq_rules = next(g for g in nav["read-required"] if isinstance(g, dict) and "rules" in g)["rules"]
    cq_rules = next(g for g in nav["read-contextual"] if isinstance(g, dict) and "rules" in g)["rules"]
    req_row = next(r for r in rq_rules if ll._norm_read_path(str(r["path"])) == ll._norm_read_path("spawn/rules/req.md"))
    ctx_row = next(r for r in cq_rules if ll._norm_read_path(str(r["path"])) == ll._norm_read_path("spawn/rules/ctx.md"))
    assert req_row["hint"] == "Keep required concise."
    assert ctx_row["hint"] == "Context hint preserved."


def test_validate_rendered_identity_duplicate_skill(tmp_path: Path) -> None:
    ll.init(tmp_path)
    base_skill = "---\nname: Same Name\n---\nbody\n"
    for name in ("a", "b"):
        root = tmp_path / "spawn" / ".extend" / name
        (root / "skills").mkdir(parents=True)
        (root / "skills" / "s.md").write_text(base_skill, encoding="utf-8")
        _write_yaml(
            root / "config.yaml",
            {"name": name, "version": "1", "schema": 1},
        )
    with pytest.raises(SpawnError):
        ll.validate_rendered_identity(tmp_path)


def test_validate_rendered_identity_duplicate_mcp(tmp_path: Path) -> None:
    ll.init(tmp_path)
    import json

    srv = {"name": "dup", "transport": {"type": "stdio"}, "capabilities": {}}
    body = json.dumps({"servers": [srv]})
    for name in ("a", "b"):
        root = tmp_path / "spawn" / ".extend" / name
        root.mkdir(parents=True)
        _write_yaml(root / "config.yaml", {"name": name, "version": "1", "schema": 1})
        mdir = root / "mcp"
        mdir.mkdir(parents=True)
        for plat in ("windows", "linux", "macos"):
            (mdir / f"{plat}.json").write_text(body, encoding="utf-8")
    with pytest.raises(SpawnError):
        ll.validate_rendered_identity(tmp_path)


def test_init_idempotent(tmp_path: Path) -> None:
    ll.init(tmp_path)
    ll.init(tmp_path)
    assert (tmp_path / "spawn" / ".core" / "config.yaml").is_file()


def test_navigation_yaml_root_keys_read_required_first_after_rules_refresh(tmp_path: Path) -> None:
    ll.init(tmp_path)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text("read-contextual: []\nread-required: []\n", encoding="utf-8")
    ll.save_rules_navigation(tmp_path)
    text = nav.read_text(encoding="utf-8")
    assert text.index("read-required") < text.index("read-contextual")


def test_navigation_yaml_root_keys_read_required_first_after_extension_save(tmp_path: Path) -> None:
    ll.init(tmp_path)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text("read-contextual: []\nread-required: []\n", encoding="utf-8")
    from spawn_cli.models.skill import SkillFileRef

    ll.save_extension_navigation(
        tmp_path,
        "spectask",
        [SkillFileRef(file="spec/main.md", description="spec")],
        [],
    )
    text = nav.read_text(encoding="utf-8")
    assert text.index("read-required") < text.index("read-contextual")


def test_navigation_yaml_unknown_root_keys_after_canonical_pair(tmp_path: Path) -> None:
    ll.init(tmp_path)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "read-contextual: []\nlegacy_note: []\nread-required: []\n",
        encoding="utf-8",
    )
    ll.save_rules_navigation(tmp_path)
    parsed = YAML_W.load(nav.read_text(encoding="utf-8"))
    assert list(parsed.keys()) == ["read-required", "read-contextual", "legacy_note"]


def test_navigation_yaml_roundtrip_preserves_comments(tmp_path: Path) -> None:
    from spawn_cli.models.skill import SkillFileRef

    ll.init(tmp_path)
    nav = tmp_path / "spawn" / "navigation.yaml"
    nav.write_text(
        "# Header comment must survive\n"
        "\n"
        "read-required: []\n"
        "\n"
        "# Between sections\n"
        "read-contextual: []\n"
        "# Footer\n",
        encoding="utf-8",
    )
    ll.save_extension_navigation(
        tmp_path,
        "spectask",
        [SkillFileRef(file="spec/main.md", description="spec")],
        [],
    )
    text = nav.read_text(encoding="utf-8")
    assert "# Header comment must survive" in text
    assert "# Between sections" in text
    assert "# Footer" in text
    assert "spectask" in text
    assert "spec/main.md" in text


def test_sync_core_config_from_defaults_overwrites_with_bundled_defaults(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = tmp_path / "spawn" / ".core" / "config.yaml"
    _write_yaml(
        cfg,
        {
            "version": "0.0.1",
            "agent-ignore": [
                "spawn/.extend/**",
                "custom/glob/**",
            ],
        },
    )
    ll.sync_core_config_from_defaults(tmp_path)
    out = load_yaml(cfg)
    bundled_txt = resources.files("spawn_cli.resources").joinpath("default_core_config.yaml").read_text(
        encoding="utf-8"
    )
    expected = YAML_W.load(bundled_txt)
    assert isinstance(expected, dict)
    assert out == expected


def test_sync_core_config_from_defaults_rejects_invalid_core(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = tmp_path / "spawn" / ".core" / "config.yaml"
    _write_yaml(cfg, {"agent-ignore": []})
    with pytest.raises(SpawnError, match="invalid spawn"):
        ll.sync_core_config_from_defaults(tmp_path)


def test_sync_core_config_from_defaults_rejects_empty_file(tmp_path: Path) -> None:
    ll.init(tmp_path)
    cfg = tmp_path / "spawn" / ".core" / "config.yaml"
    cfg.write_text("", encoding="utf-8")
    with pytest.raises(SpawnError, match="empty or invalid"):
        ll.sync_core_config_from_defaults(tmp_path)
