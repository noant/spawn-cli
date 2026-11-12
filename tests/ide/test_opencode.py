"""Tests for the OpenCode CLI adapter."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.opencode import OpenCodeAdapter, _sanitize_skill_name
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> OpenCodeAdapter:
    return OpenCodeAdapter()


def _skill(name: str = "spectask-execute") -> SkillMetadata:
    return SkillMetadata(
        name=name,
        description="Execute approved spectasks.",
        content="# body\n",
        hints=["Prefer spectask steps in order."],
    )


def _stdio_server(name: str = "srv", proxy: bool = False) -> McpServer:
    return McpServer(
        name=name,
        extension="ext",
        spawn_stdio_proxy=proxy,
        transport=McpTransport(type="stdio", command="tool-cmd", args=["--flag"]),
    )


# detect ---------------------------------------------------------------------


def test_detect_dot_opencode_dir(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False
    (tmp_path / ".opencode").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_opencode_json(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    (tmp_path / "opencode.json").write_text("{}", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_opencode_jsonc(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    (tmp_path / "opencode.jsonc").write_text("{}", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_capabilities(adapter: OpenCodeAdapter, tmp_path: Path) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "project"
    assert caps.agent_ignore == "project"
    assert caps.entry_point == "agents-md"


# skills ---------------------------------------------------------------------


def test_add_skills(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    path = tmp_path / ".opencode" / "skills" / "spectask-execute" / "SKILL.md"
    assert path.is_file()
    assert rendered == [{"skill": "spectask-execute", "path": ".opencode/skills/spectask-execute/SKILL.md"}]


def test_add_skills_sanitizes_name(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    assert _sanitize_skill_name("My_Skill.v2") == "my-skill-v2"
    adapter.add_skills(tmp_path, [_skill("My_Skill.v2")])
    path = tmp_path / ".opencode" / "skills" / "my-skill-v2" / "SKILL.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "name: my-skill-v2" in text  # frontmatter name == directory name (OpenCode rule)


def test_add_skills_warns_on_overwrite(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_skills(tmp_path, [_skill()])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [_skill()])
        assert len(w) == 1
        assert issubclass(w[0].category, SpawnWarning)


def test_remove_skills(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    rendered = adapter.add_skills(tmp_path, [_skill()])
    path = tmp_path / ".opencode" / "skills" / "spectask-execute" / "SKILL.md"
    adapter.remove_skills(tmp_path, rendered)
    assert not path.exists()
    assert not path.parent.exists()


# mcp ------------------------------------------------------------------------


def test_add_mcp_local_shape(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server("srv")]))
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    entry = data["mcp"]["srv"]
    assert entry["type"] == "local"
    assert entry["command"] == ["tool-cmd", "--flag"]
    assert entry["enabled"] is True


def test_add_mcp_remote_shape(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    server = McpServer(
        name="remote",
        extension="e",
        transport=McpTransport(
            type="streamable-http",
            url="https://example.com/mcp",
            headers={"Authorization": "MY_TOKEN"},
        ),
    )
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[server]))
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    entry = data["mcp"]["remote"]
    assert entry == {
        "type": "remote",
        "url": "https://example.com/mcp",
        "headers": {"Authorization": "{env:MY_TOKEN}"},
        "enabled": True,
    }


def test_add_mcp_merges_existing(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"keep": 1, "mcp": {"old": {"type": "local", "command": ["x"], "enabled": True}}}),
        encoding="utf-8",
    )
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server("new")]))
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert data["keep"] == 1
    assert "old" in data["mcp"]
    assert "new" in data["mcp"]


def test_add_mcp_env_placeholders(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    server = _stdio_server()
    server.env["PLAIN"] = McpEnvVar(value="lit")
    server.env["SECRET"] = McpEnvVar(secret=True)
    server.env["EMPTY"] = McpEnvVar()
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[server]))
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    env = data["mcp"]["srv"]["environment"]
    assert env["PLAIN"] == "lit"
    assert env["SECRET"] == "{env:SECRET}"
    assert env["EMPTY"] == "{env:EMPTY}"


def test_remove_mcp(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server("a"), _stdio_server("b")]))
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert "a" not in data["mcp"]
    assert "b" in data["mcp"]


def test_remove_mcp_prunes_empty_key(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server("a")]))
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert "mcp" not in data


def test_remove_mcp_missing_file_noop(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.remove_mcp(tmp_path, ["x"])


def test_invalid_config_raises(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    (tmp_path / "opencode.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(SpawnError):
        adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server()]))


def test_load_config_warns_on_jsonc(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    (tmp_path / "opencode.jsonc").write_text("{}", encoding="utf-8")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_mcp(tmp_path, NormalizedMcp(servers=[_stdio_server()]))
        assert any("opencode.jsonc" in str(x.message) for x in w)


# agent ignore ---------------------------------------------------------------


def test_add_agent_ignore_deny_read_edit(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**"])
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert data["permission"]["read"]["spawn/**"] == "deny"
    assert data["permission"]["edit"]["spawn/**"] == "deny"


def test_add_agent_ignore_idempotent(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["g"])
    adapter.add_agent_ignore(tmp_path, ["g"])
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert len(data["permission"]["read"]) == 1
    assert len(data["permission"]["edit"]) == 1


def test_remove_agent_ignore_keeps_user_rules(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn-only"])
    path = tmp_path / "opencode.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["permission"]["read"]["user-keep"] = "deny"
    path.write_text(json.dumps(data), encoding="utf-8")
    adapter.remove_agent_ignore(tmp_path, ["spawn-only"])
    data2 = json.loads(path.read_text(encoding="utf-8"))
    assert "spawn-only" not in data2["permission"]["read"]
    assert data2["permission"]["read"]["user-keep"] == "deny"


def test_remove_agent_ignore_prunes_empty(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["g"])
    adapter.remove_agent_ignore(tmp_path, ["g"])
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert "permission" not in data


def test_remove_agent_ignore_missing_file_noop(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.remove_agent_ignore(tmp_path, ["x"])


def test_clear_spawn_agent_ignore(tmp_path: Path, adapter: OpenCodeAdapter) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**"])
    ll.save_agent_ignore_list(tmp_path, "opencode", ["spawn/**"])
    adapter.clear_spawn_agent_ignore(tmp_path)
    data = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    assert "permission" not in data


# entry point ----------------------------------------------------------------


def test_rewrite_entry_point_agents_md(adapter: OpenCodeAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "body")
    assert rel == "AGENTS.md"
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text and SPAWN_BLOCK_END in text
    assert "body" in text
