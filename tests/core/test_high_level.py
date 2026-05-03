from __future__ import annotations

import json
import shutil

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import warnings
from ruamel.yaml import YAML

from spawn_cli.core import high_level as hl
from spawn_cli.core import low_level as ll
from spawn_cli.core.errors import SpawnError, SpawnWarning
from spawn_cli.ide.registry import DetectResult, IdeCapabilities
from spawn_cli.ide.windsurf import WindsurfAdapter

from spawn_cli.io.yaml_io import configure_yaml_dump, load_yaml

YAML_W = YAML(typ="safe")
configure_yaml_dump(YAML_W)


def _load_cfg_dict(path: Path) -> dict:
    return dict(load_yaml(path) or {})


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        YAML_W.dump(data, fh)


def _write_mcp_trio(ext_root: Path, servers: list) -> None:
    mdir = ext_root / "mcp"
    mdir.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"servers": servers})
    for plat in ("windows", "linux", "macos"):
        (mdir / f"{plat}.json").write_text(body, encoding="utf-8")


@pytest.fixture
def target(tmp_path: Path) -> Path:
    ll.init(tmp_path)
    return tmp_path


def _stub_ide():
    """Minimal IDE adapter matching StubIdeAdapter behavior."""
    from spawn_cli.models.mcp import NormalizedMcp
    from spawn_cli.models.skill import SkillMetadata

    class A:
        key = "cursor"

        def detect(self, root: Path):
            return DetectResult(
                False,
                IdeCapabilities("native", "project", "native", "agents-md"),
            )

        def add_skills(self, root: Path, metas: list[SkillMetadata]):
            return [{"skill": m.name, "path": f".t/{m.name}"} for m in metas]

        def remove_skills(self, root: Path, rendered: list[dict]):
            return None

        def add_mcp(self, root: Path, normalized_mcp: NormalizedMcp):
            return [s.name for s in normalized_mcp.servers]

        def remove_mcp(self, root: Path, names: list[str]):
            return None

        def add_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def remove_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def rewrite_core_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def rewrite_extension_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def clear_spawn_agent_ignore(self, root: Path) -> None:
            return None

        def rewrite_entry_point(self, root: Path, prompt: str):
            return "AGENTS.md"

        def finalize_repo_after_ide_removed(self, root: Path):
            return None

    return A()


def _stub_with_caps(skills_cap: str = "native", mcp_cap: str = "project"):
    """Minimal IDE stub with configurable skill/MCP capability flags."""

    from spawn_cli.models.mcp import NormalizedMcp
    from spawn_cli.models.skill import SkillMetadata

    class A:
        key = "cursor"

        def detect(self, root: Path):
            return DetectResult(
                False,
                IdeCapabilities(skills_cap, mcp_cap, "native", "agents-md"),
            )

        def add_skills(self, root: Path, metas: list[SkillMetadata]):
            return [{"skill": m.name, "path": f".t/{m.name}"} for m in metas]

        def remove_skills(self, root: Path, rendered: list[dict]):
            return None

        def add_mcp(self, root: Path, normalized_mcp: NormalizedMcp):
            return [s.name for s in normalized_mcp.servers]

        def remove_mcp(self, root: Path, names: list[str]):
            return None

        def add_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def remove_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def rewrite_core_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def rewrite_extension_agent_ignore(self, root: Path, globs: list[str]):
            return None

        def clear_spawn_agent_ignore(self, root: Path) -> None:
            return None

        def rewrite_entry_point(self, root: Path, prompt: str):
            return "AGENTS.md"

        def finalize_repo_after_ide_removed(self, root: Path):
            return None

    return A()


def _install_ext(
    target_root: Path,
    name: str,
    *,
    git_ignore: list[str] | None = None,
    skills: dict | None = None,
    files: dict | None = None,
    mcp_servers: list | None = None,
    setup: dict | None = None,
) -> None:
    root = target_root / "spawn" / ".extend" / name
    root.mkdir(parents=True)
    cfg = {
        "name": name,
        "version": "1.0.0",
        "schema": 1,
        "files": files or {},
        "folders": {},
        "agent-ignore": [],
        "git-ignore": git_ignore or [],
        "skills": skills or {},
        "setup": setup or {},
    }
    _write_yaml(root / "config.yaml", cfg)
    sk = root / "skills"
    sk.mkdir(exist_ok=True)
    for k in (skills or {}):
        (sk / k).write_text("---\nname: sn\n---\nbody\n", encoding="utf-8")
    if mcp_servers is not None:
        _write_mcp_trio(root, mcp_servers)
    if setup:
        (root / "setup").mkdir(exist_ok=True)


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_gitignore(target: Path) -> None:
    _install_ext(target, "e1", git_ignore=[".cache/**"])
    hl.refresh_gitignore(target)
    lines = (target / "spawn" / ".metadata" / "git-ignore.txt").read_text(encoding="utf-8")
    assert ".cache/**" in lines
    gi = (target / ".gitignore").read_text(encoding="utf-8")
    assert ".cache/**" in gi


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_gitignore_removes_old(target: Path) -> None:
    _install_ext(target, "e1", git_ignore=["a/"])
    hl.refresh_gitignore(target)
    ext = target / "spawn" / ".extend" / "e1"
    raw = _load_cfg_dict(ext / "config.yaml")
    raw["git-ignore"] = ["b/"]
    _write_yaml(ext / "config.yaml", raw)
    hl.refresh_gitignore(target)
    meta = ll.get_git_ignore_list(target)
    assert "b/" in meta
    assert "a/" not in meta


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_agent_ignore(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", git_ignore=[])
    ext_dir = target / "spawn" / ".extend" / "e1"
    cfg = _load_cfg_dict(ext_dir / "config.yaml")
    cfg["agent-ignore"] = ["logs/**"]
    _write_yaml(ext_dir / "config.yaml", cfg)
    hl.refresh_agent_ignore(target, "cursor")
    got = ll.get_agent_ignore_list(target, "cursor")
    assert any("logs/**" in g for g in got)


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_skills(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        skills={"s.md": {"name": "uniq-skill", "description": "d"}},
    )
    hl.refresh_skills(target, "cursor", "e1")
    data = ll.get_rendered_skills(target, "cursor", "e1")
    assert len(data) >= 1


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_skills_duplicate_name_errors(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "a", skills={"x.md": {"name": "dup", "description": "d"}})
    _install_ext(target, "b", skills={"y.md": {"name": "dup", "description": "d"}})
    with pytest.raises(SpawnError, match="duplicate"):
        hl.refresh_skills(target, "cursor", "b")


BETA_GLOBAL_READ_FILE = "docs/beta-global.md"
_BETA_GLOBAL_META = {
    BETA_GLOBAL_READ_FILE: {
        "description": "Beta global context.",
        "mode": "static",
        "globalRead": "required",
        "localRead": "no",
    }
}


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_extension_core_rebuilds_peer_skills_when_new_ext_adds_global_read(
    target: Path,
) -> None:
    """Installing a second extension must re-render the first extension's skills
    so merged global ``required_read`` lists stay current.
    """
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "alpha", skills={"a.md": {"name": "alpha-skill", "description": "d"}})
    hl._refresh_extension_core(target, "alpha")
    m_alpha_only = ll.generate_skills_metadata(target, "alpha")[0]
    assert BETA_GLOBAL_READ_FILE not in {r.file for r in m_alpha_only.required_read}

    _install_ext(target, "beta", files=dict(_BETA_GLOBAL_META))
    hl._refresh_extension_core(target, "beta")
    m_after = ll.generate_skills_metadata(target, "alpha")[0]
    assert BETA_GLOBAL_READ_FILE in {r.file for r in m_after.required_read}


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_remove_extension_rebuilds_survivor_skills_without_removed_global_read(
    target: Path,
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "alpha", skills={"a.md": {"name": "alpha-skill", "description": "d"}})
    _install_ext(target, "beta", files=dict(_BETA_GLOBAL_META))
    hl._refresh_extension_core(target, "beta")
    assert BETA_GLOBAL_READ_FILE in {
        r.file for r in ll.generate_skills_metadata(target, "alpha")[0].required_read
    }

    hl.remove_extension(target, "beta")
    m_survivor = ll.generate_skills_metadata(target, "alpha")[0]
    assert BETA_GLOBAL_READ_FILE not in {r.file for r in m_survivor.required_read}


@patch("spawn_cli.core.high_level.warnings.warn")
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_with_caps("native", "unsupported"))
def test_refresh_extension_core_warns_limited_mcp_when_servers_present(
    mock_warn: MagicMock, target: Path
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {"name": "srv-one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    hl._refresh_extension_core(target, "e1")
    mock_warn.assert_called_once()
    assert "limited MCP support" in str(mock_warn.call_args[0][0])
    assert mock_warn.call_args[0][1] is SpawnWarning


@patch("spawn_cli.core.high_level.warnings.warn")
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_with_caps("unsupported", "project"))
def test_refresh_extension_core_warns_skills_unsupported_when_skill_files_present(
    mock_warn: MagicMock, target: Path
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"a.md": {"name": "s", "description": "d"}})
    hl._refresh_extension_core(target, "e1")
    mock_warn.assert_called_once()
    assert "does not support skills" in str(mock_warn.call_args[0][0])
    assert mock_warn.call_args[0][1] is SpawnWarning


@patch("spawn_cli.core.high_level.warnings.warn")
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_with_caps("unsupported", "unsupported"))
def test_add_ide_no_capability_warnings_when_no_extensions(mock_warn: MagicMock, target: Path) -> None:
    hl.add_ide(target, "cursor")
    mock_warn.assert_not_called()


@patch("spawn_cli.core.high_level.warnings.warn")
@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_with_caps("native", "unsupported"))
def test_refresh_extension_for_ide_mcp_warn_only_when_named_ext_has_servers(
    mock_warn: MagicMock, target: Path
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "srv",
        mcp_servers=[
            {"name": "one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    _install_ext(target, "skills_only", skills={"k.md": {"name": "k", "description": "d"}})
    hl.refresh_extension_for_ide(target, "cursor", "skills_only")
    mock_warn.assert_not_called()
    hl.refresh_extension_for_ide(target, "cursor", "srv")
    mock_warn.assert_called_once()
    assert "limited MCP support" in str(mock_warn.call_args[0][0])


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_extension_for_ide_calls_refresh_navigation(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    with patch.object(hl, "refresh_navigation") as rn:
        hl.refresh_extension_for_ide(target, "cursor", "e1")
        rn.assert_called_once_with(target)


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_mcp(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {
                "name": "srv-one",
                "transport": {"type": "stdio", "command": "true"},
            }
        ],
    )
    hl.refresh_mcp(target, "cursor", "e1")
    assert ll.get_rendered_mcp(target, "cursor", "e1") == ["srv-one"]


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_mcp_stdout_exact_merged_notice(capsys: pytest.CaptureFixture[str], target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {"name": "srv-one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    hl.refresh_mcp(target, "cursor", "e1")
    assert capsys.readouterr().out == hl.MCP_MERGED_NOTICE + "\n"


@patch("spawn_cli.core.high_level.ide_get", return_value=WindsurfAdapter())
def test_refresh_mcp_no_stdout_notice_windsurf_noop_mcp(
    capsys: pytest.CaptureFixture[str],
    target: Path,
) -> None:
    ll.add_ide_to_list(target, "windsurf")
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {"name": "srv-one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    hl.refresh_mcp(target, "windsurf", "e1")
    assert hl.MCP_MERGED_NOTICE not in capsys.readouterr().out
    assert ll.get_rendered_mcp(target, "windsurf", "e1") == []


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
@pytest.mark.parametrize("empty_mcp_kind", ["missing_file", "empty_servers_key"])
def test_refresh_mcp_no_stdout_notice_without_mcp_servers(
    capsys: pytest.CaptureFixture[str],
    target: Path,
    empty_mcp_kind: str,
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1")
    ext_root = target / "spawn" / ".extend" / "e1"
    if empty_mcp_kind == "empty_servers_key":
        _write_mcp_trio(ext_root, [])
    hl.refresh_mcp(target, "cursor", "e1")
    assert hl.MCP_MERGED_NOTICE not in capsys.readouterr().out


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_add_ide_prints_merged_notice_once_with_two_mcp_extensions(
    capsys: pytest.CaptureFixture[str],
    target: Path,
) -> None:
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {"name": "srv-a", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    _install_ext(
        target,
        "e2",
        mcp_servers=[
            {"name": "srv-b", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.add_ide(target, "cursor")
    out = capsys.readouterr().out
    assert out.count(hl.MCP_MERGED_NOTICE) == 1


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_mcp_skip_notice_still_persists_rendered_mcp(
    capsys: pytest.CaptureFixture[str],
    target: Path,
) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        mcp_servers=[
            {"name": "srv-one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    hl.refresh_mcp(target, "cursor", "e1", emit_mcp_merged_notice=False)
    assert hl.MCP_MERGED_NOTICE not in capsys.readouterr().out
    assert ll.get_rendered_mcp(target, "cursor", "e1") == ["srv-one"]


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_mcp_duplicate_server_errors(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    s = {"name": "same", "transport": {"type": "stdio", "command": "true"}}
    _install_ext(target, "a", mcp_servers=[s])
    _install_ext(target, "b", mcp_servers=[s])
    with pytest.raises(SpawnError, match="duplicate"):
        hl.refresh_mcp(target, "cursor", "b")


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_remove_skills(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"s.md": {"name": "n", "description": "d"}})
    hl.refresh_skills(target, "cursor", "e1")
    hl.remove_skills(target, "cursor", "e1")
    assert ll.get_rendered_skills(target, "cursor", "e1") == []


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.refresh_entry_point(target, "cursor")
    mock.rewrite_entry_point.assert_called_once()
    assert hl.SPAWN_ENTRY_POINT_PROMPT in mock.rewrite_entry_point.call_args[0][1]


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point_hints_rollup_skips_local(tmp_path: Path) -> None:
    target = tmp_path
    ll.init(target)
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    cfg = _load_cfg_dict(target / "spawn" / ".extend" / "e1" / "config.yaml")
    cfg["hints"] = {"global": ["global-for-agents"], "local": ["locals-only"]}
    _write_yaml(target / "spawn" / ".extend" / "e1" / "config.yaml", cfg)
    _write_yaml(
        target / "spawn" / "navigation.yaml",
        {
            "read-required": [
                {
                    "rules": [
                        {
                            "path": "spawn/rules/r.md",
                            "description": "r",
                            "hint": " maintainer-required ",
                        }
                    ]
                },
            ],
            "read-contextual": [],
        },
    )
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.refresh_entry_point(target, "cursor")
    prompt = mock.rewrite_entry_point.call_args[0][1]
    assert hl.SPAWN_ENTRY_POINT_PROMPT in prompt
    assert "Hints:" in prompt
    assert "- global-for-agents" in prompt
    assert "- maintainer-required" in prompt
    assert "locals-only" not in prompt


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_entry_point_agents_warnings_for_oversize_hint(tmp_path: Path) -> None:
    target = tmp_path
    ll.init(target)
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={})
    cfg = _load_cfg_dict(target / "spawn" / ".extend" / "e1" / "config.yaml")
    cfg["hints"] = {"global": ["x" * 600]}
    _write_yaml(target / "spawn" / ".extend" / "e1" / "config.yaml", cfg)
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        with warnings.catch_warnings(record=True) as wrec:
            warnings.simplefilter("always")
            hl.refresh_entry_point(target, "cursor")
        assert mock.rewrite_entry_point.called
        prompt = mock.rewrite_entry_point.call_args[0][1]
        assert "x" * 600 in prompt
        assert any(issubclass(w.category, SpawnWarning) for w in wrec)


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_rules_navigation(target: Path) -> None:
    with patch("spawn_cli.core.low_level.save_rules_navigation") as srn:
        hl.refresh_rules_navigation(target)
        srn.assert_called_once_with(target)


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_add_ide(target: Path) -> None:
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    mock = MagicMock(wraps=_stub_ide())
    with patch("spawn_cli.core.high_level.ide_get", return_value=mock):
        hl.add_ide(target, "cursor")
    assert "cursor" in ll.list_ides(target)
    assert mock.rewrite_entry_point.called
    assert mock.add_skills.called


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_remove_ide(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    hl.refresh_skills(target, "cursor", "e1")
    hl.remove_ide(target, "cursor")
    assert "cursor" not in ll.list_ides(target)
    assert ll.get_rendered_skills(target, "cursor", "e1") == []


def test_remove_ide_cursor_deletes_dot_cursor_and_metadata(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        skills={"s.md": {"name": "sk", "description": "d"}},
        mcp_servers=[
            {"name": "srv-one", "transport": {"type": "stdio", "command": "true"}},
        ],
    )
    hl.refresh_skills(target, "cursor", "e1")
    hl.refresh_mcp(target, "cursor", "e1")
    assert (target / ".cursor").is_dir()
    meta_ide = target / "spawn" / ".metadata" / "cursor"
    assert meta_ide.is_dir()

    hl.remove_ide(target, "cursor")

    assert "cursor" not in ll.list_ides(target)
    assert not (target / ".cursor").exists()
    assert not meta_ide.exists()


def test_remove_ide_keeps_cursor_when_user_file_remains(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    hl.refresh_skills(target, "cursor", "e1")
    user_file = target / ".cursor" / "rules" / "keep.md"
    user_file.parent.mkdir(parents=True)
    user_file.write_text("x", encoding="utf-8")

    hl.remove_ide(target, "cursor")

    assert "cursor" not in ll.list_ides(target)
    assert user_file.exists()
    assert (target / ".cursor").is_dir()


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_refresh_extension(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        skills={"s.md": {"name": "sk", "description": "d"}},
        setup={"before-install": "bi.py", "after-install": "ai.py"},
    )
    setup_dir = target / "spawn" / ".extend" / "e1" / "setup"
    (setup_dir / "bi.py").write_text("print(1)\n", encoding="utf-8")
    (setup_dir / "ai.py").write_text("print(1)\n", encoding="utf-8")
    with (
        patch("spawn_cli.core.high_level.scripts.run_before_install_scripts") as bi,
        patch("spawn_cli.core.high_level.scripts.run_after_install_scripts") as ai,
    ):
        hl.refresh_extension(target, "e1")
        bi.assert_called_once()
        ai.assert_called_once()


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_remove_extension(target: Path) -> None:
    ll.add_ide_to_list(target, "cursor")
    _install_ext(
        target,
        "e1",
        skills={"s.md": {"name": "sk", "description": "d"}},
        setup={"before-uninstall": "bu.py", "after-uninstall": "au.py"},
    )
    sd = target / "spawn" / ".extend" / "e1" / "setup"
    (sd / "bu.py").write_text("# noop\n", encoding="utf-8")
    (sd / "au.py").write_text("# noop\n", encoding="utf-8")
    hl.refresh_skills(target, "cursor", "e1")
    with patch("spawn_cli.core.high_level.scripts.run_before_uninstall_scripts") as bu:
        hl.remove_extension(target, "e1")
        bu.assert_called_once()
    assert "e1" not in ll.list_extensions(target)


def _write_ext_source_yaml(target_root: Path, ext: str, *, path: str, branch: str | None) -> None:
    src: dict = {"type": "git", "path": path}
    if branch is not None:
        src["branch"] = branch
    _write_yaml(
        target_root / "spawn" / ".extend" / ext / "source.yaml",
        {
            "extension": ext,
            "source": src,
            "installed": {"version": "1.0.0", "installedAt": "2020-01-01T00:00:00+00:00"},
        },
    )


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_reinstall_extension_remove_then_install(target: Path) -> None:
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    _write_ext_source_yaml(target, "e1", path="https://example.com/e.git", branch="main")
    order: list[str] = []

    with (
        patch.object(hl, "remove_extension") as mock_rm,
        patch.object(hl, "install_extension") as mock_inst,
    ):
        mock_rm.side_effect = lambda *a, **k: order.append("rm")
        mock_inst.side_effect = lambda *a, **k: order.append("in")
        hl.reinstall_extension(target, "e1")

    assert order == ["rm", "in"]
    mock_rm.assert_called_once_with(target, "e1")
    mock_inst.assert_called_once_with(target, "https://example.com/e.git", "main")


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_reinstall_extension_install_branch_none(target: Path) -> None:
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    _write_ext_source_yaml(target, "e1", path="/local/ext", branch=None)
    with (
        patch.object(hl, "remove_extension", MagicMock()),
        patch.object(hl, "install_extension") as mock_inst,
    ):
        hl.reinstall_extension(target, "e1")
    mock_inst.assert_called_once_with(target, "/local/ext", None)


def test_reinstall_extension_not_installed(target: Path) -> None:
    with pytest.raises(SpawnError, match="not installed"):
        hl.reinstall_extension(target, "missing")


@patch("spawn_cli.core.high_level.ide_get", lambda *_a, **_k: _stub_ide())
def test_reinstall_extension_no_source_yaml(target: Path) -> None:
    _install_ext(target, "e1", skills={"s.md": {"name": "sk", "description": "d"}})
    with pytest.raises(SpawnError, match="no source.yaml"):
        hl.reinstall_extension(target, "e1")


def test_extension_init_creates_skeleton(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "my-pack")
    cfg = tmp_path / "extsrc" / "config.yaml"
    assert cfg.is_file()
    raw = _load_cfg_dict(cfg)
    assert raw.get("name") == "my-pack"
    assert (tmp_path / "extsrc" / "skills").is_dir()
    mdir = tmp_path / "extsrc" / "mcp"
    assert mdir.is_dir()
    for plat in ("windows", "linux", "macos"):
        p = mdir / f"{plat}.json"
        assert p.is_file()
        assert json.loads(p.read_text(encoding="utf-8")) == {"servers": []}


def test_extension_init_idempotent(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "my-pack")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        hl.extension_init(tmp_path, "other")
        assert any("already exists" in str(x.message) for x in w)
    raw = _load_cfg_dict(tmp_path / "extsrc" / "config.yaml")
    assert raw.get("name") == "my-pack"


def test_extension_check_valid(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    assert hl.extension_check(tmp_path, strict=False) == []


def test_extension_check_missing_skill(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    extsrc = tmp_path / "extsrc"
    cfg = _load_cfg_dict(extsrc / "config.yaml")
    cfg["skills"] = {"missing.md": {"name": "m", "description": "d"}}
    _write_yaml(extsrc / "config.yaml", cfg)
    with pytest.raises(SpawnError, match="skill file missing"):
        hl.extension_check(tmp_path, strict=True)


def test_extension_check_missing_description(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    extsrc = tmp_path / "extsrc"
    cfg = _load_cfg_dict(extsrc / "config.yaml")
    cfg["files"] = {
        "doc.md": {
            "description": "",
            "mode": "static",
            "globalRead": "required",
            "localRead": "no",
        }
    }
    _write_yaml(extsrc / "config.yaml", cfg)
    with pytest.raises(SpawnError, match="description"):
        hl.extension_check(tmp_path, strict=True)


def test_extension_check_missing_mcp_dir_strict(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    shutil.rmtree(tmp_path / "extsrc" / "mcp")
    with pytest.raises(SpawnError, match="missing extsrc/mcp"):
        hl.extension_check(tmp_path, strict=True)


def test_extension_check_obsolete_root_mcp_strict(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    (tmp_path / "extsrc" / "mcp.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SpawnError, match="obsolete"):
        hl.extension_check(tmp_path, strict=True)


def test_extension_check_mcp_name_mismatch_strict(tmp_path: Path) -> None:
    hl.extension_init(tmp_path, "p")
    extsrc = tmp_path / "extsrc" / "mcp"
    (extsrc / "windows.json").write_text(
        json.dumps({"servers": [{"name": "a", "transport": {"type": "stdio"}}]}),
        encoding="utf-8",
    )
    (extsrc / "linux.json").write_text(json.dumps({"servers": []}), encoding="utf-8")
    (extsrc / "macos.json").write_text(json.dumps({"servers": []}), encoding="utf-8")
    with pytest.raises(SpawnError, match="must match"):
        hl.extension_check(tmp_path, strict=True)
