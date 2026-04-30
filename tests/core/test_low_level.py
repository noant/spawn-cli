from __future__ import annotations

import time
import uuid
import warnings
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.io.yaml_io import configure_yaml_dump

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

    (root / "mcp.json").write_text(json.dumps(mcp), encoding="utf-8")

    nm = ll.list_mcp(tmp_path, "spectask")
    assert len(nm.servers) == 1
    assert nm.servers[0].name == "test-srv"
    assert nm.servers[0].extension == "spectask"


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
    for name in ("a", "b"):
        root = tmp_path / "spawn" / ".extend" / name
        root.mkdir(parents=True)
        _write_yaml(root / "config.yaml", {"name": name, "version": "1", "schema": 1})
        (root / "mcp.json").write_text(json.dumps({"servers": [srv]}), encoding="utf-8")
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
