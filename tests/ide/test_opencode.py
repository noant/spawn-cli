from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.opencode import OPENCODE_CONFIG_JSON_FILENAME, OPENCODE_CONFIG_SCHEMA_URL, OpencodeAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> OpencodeAdapter:
    return OpencodeAdapter()


def test_detect_with_opencode_dir(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / ".opencode").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_with_opencode_json(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).write_text("{}", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_neither(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_detect_capabilities(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    caps = adapter.detect(tmp_path).capabilities
    assert caps.skills == "native"
    assert caps.mcp == "project"
    assert caps.agent_ignore == "project"
    assert caps.entry_point == "agents-md"


def test_add_skills_creates_subdirectory_skill_md(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    results = adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="my-skill", description="d", content="body")],
    )
    skill_path = tmp_path / ".opencode" / "skills" / "my-skill" / "SKILL.md"
    assert skill_path.exists()
    assert results == [{"skill": "my-skill", "path": ".opencode/skills/my-skill/SKILL.md"}]


def test_add_skills_normalizes_name(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="  Foo Bar  ", description="d", content="c")],
    )
    assert (tmp_path / ".opencode" / "skills" / "foo-bar" / "SKILL.md").exists()


def test_add_skills_warns_on_overwrite(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="1")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="2")])
        assert w is not None
        assert len(w) == 1
        assert "Overwriting" in str(w[0].message)


def test_remove_skills_deletes_skill_md_and_empty_parent(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    results = adapter.add_skills(tmp_path, [SkillMetadata(name="z", description="d", content="c")])
    skill_dir = tmp_path / ".opencode" / "skills" / "z"
    assert skill_dir.exists()
    adapter.remove_skills(tmp_path, results)
    assert not (skill_dir / "SKILL.md").exists()
    assert not skill_dir.exists()


def test_remove_skills_keeps_nonempty_parent(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    results = adapter.add_skills(tmp_path, [SkillMetadata(name="z", description="d", content="c")])
    skill_dir = tmp_path / ".opencode" / "skills" / "z"
    # Place an extra file so parent dir is not empty after removal
    (skill_dir / "extra.txt").write_text("keep", encoding="utf-8")
    adapter.remove_skills(tmp_path, results)
    assert not (skill_dir / "SKILL.md").exists()
    assert skill_dir.exists()


def test_add_mcp_creates_config(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="srv",
                    extension="e",
                    transport=McpTransport(type="stdio", command="uvx", args=["tool"]),
                )
            ]
        ),
    )
    p = tmp_path / OPENCODE_CONFIG_JSON_FILENAME
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "$schema" in data
    assert "mcp" in data
    entry = data["mcp"]["srv"]
    assert entry["type"] == "local"
    assert entry["command"] == ["uvx", "tool"]
    assert entry["enabled"] is True


def test_add_mcp_includes_schema(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(servers=[]),
    )
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["$schema"] == OPENCODE_CONFIG_SCHEMA_URL


def test_add_mcp_merges_existing_config(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).write_text(
        json.dumps({"$schema": OPENCODE_CONFIG_SCHEMA_URL, "custom": 1, "mcp": {}}),
        encoding="utf-8",
    )
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="n",
                    extension="e",
                    transport=McpTransport(type="stdio", command="x", args=[]),
                )
            ]
        ),
    )
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["custom"] == 1
    assert "n" in data["mcp"]


def test_add_mcp_preserves_existing_schema(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).write_text(
        json.dumps({"$schema": "https://custom.example.com/schema.json"}),
        encoding="utf-8",
    )
    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[]))
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["$schema"] == "https://custom.example.com/schema.json"


def test_add_mcp_stdio_shape(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="s",
                    extension="e",
                    transport=McpTransport(type="stdio", command="uvx", args=["mcp"]),
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["s"]
    assert entry["type"] == "local"
    assert entry["command"] == ["uvx", "mcp"]


def test_add_mcp_http_uses_remote_type(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="h",
                    extension="e",
                    transport=McpTransport(
                        type="streamable-http",
                        url="https://example.com/mcp",
                    ),
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["h"]
    assert entry["type"] == "remote"
    assert entry["url"] == "https://example.com/mcp"


def test_add_mcp_sse_uses_remote_type_and_url(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="h",
                    extension="e",
                    transport=McpTransport(type="sse", url="https://ex.com/sse"),
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["h"]
    assert entry["type"] == "remote"
    assert entry["url"] == "https://ex.com/sse"


def test_add_mcp_secret_placeholder(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="s",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"TOKEN": McpEnvVar(secret=True)},
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["s"]
    assert entry["environment"]["TOKEN"] == "${TOKEN}"


def test_add_mcp_plain_env_value(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="s",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"HOST": McpEnvVar(secret=False, value="localhost")},
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["s"]
    assert entry["environment"]["HOST"] == "localhost"


def test_add_mcp_empty_env_uses_placeholder(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="s",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"KEY": McpEnvVar(secret=False)},
                )
            ]
        ),
    )
    entry = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))["mcp"]["s"]
    assert entry["environment"]["KEY"] == "${KEY}"


def test_remove_mcp_removes_entry(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="a",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                ),
                McpServer(
                    name="b",
                    extension="e",
                    transport=McpTransport(type="stdio", command="d", args=[]),
                ),
            ]
        ),
    )
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert "a" not in data["mcp"]
    assert "b" in data["mcp"]


def test_remove_mcp_noop_when_no_config(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.remove_mcp(tmp_path, ["x"])
    assert not (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).exists()


def test_remove_mcp_preserves_custom_fields(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).write_text(
        json.dumps({"$schema": OPENCODE_CONFIG_SCHEMA_URL, "custom": 42, "mcp": {"a": {}, "b": {}}}),
        encoding="utf-8",
    )
    adapter.remove_mcp(tmp_path, ["a"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["custom"] == 42
    assert "a" not in data["mcp"]


def test_add_agent_ignore_merges_into_watcher(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**", "*.log"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["watcher"]["ignore"] == ["spawn/**", "*.log"]


def test_add_agent_ignore_deduplicates(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**"])
    adapter.add_agent_ignore(tmp_path, ["spawn/**", "*.log"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["watcher"]["ignore"] == ["spawn/**", "*.log"]


def test_add_agent_ignore_preserves_existing_config(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).write_text(
        json.dumps({"$schema": OPENCODE_CONFIG_SCHEMA_URL, "custom": 1}),
        encoding="utf-8",
    )
    adapter.add_agent_ignore(tmp_path, ["spawn/**"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["custom"] == 1
    assert data["watcher"]["ignore"] == ["spawn/**"]


def test_remove_agent_ignore_removes_from_watcher(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**", "*.log", "dist/**"])
    adapter.remove_agent_ignore(tmp_path, ["*.log"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert data["watcher"]["ignore"] == ["spawn/**", "dist/**"]


def test_remove_agent_ignore_cleans_empty_watcher(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["spawn/**"])
    adapter.remove_agent_ignore(tmp_path, ["spawn/**"])
    data = json.loads((tmp_path / OPENCODE_CONFIG_JSON_FILENAME).read_text(encoding="utf-8"))
    assert "watcher" not in data


def test_remove_agent_ignore_noop_when_no_config(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.remove_agent_ignore(tmp_path, ["spawn/**"])
    assert not (tmp_path / OPENCODE_CONFIG_JSON_FILENAME).exists()


def test_rewrite_entry_point_creates_agents_md(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "hello-agent")
    assert rel == "AGENTS.md"
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text
    assert "hello-agent" in text


def test_rewrite_entry_point_replaces_existing(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text(
        f"preamble\n{SPAWN_BLOCK_START}\nold\n{SPAWN_BLOCK_END}\npostamble",
        encoding="utf-8",
    )
    adapter.rewrite_entry_point(tmp_path, "new-content")
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "old" not in text
    assert "new-content" in text
    assert "preamble" in text


def test_finalize_repo_removes_skill_subdirs(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    skill_a_dir = tmp_path / ".opencode" / "skills" / "alpha"
    skill_a_dir.mkdir(parents=True, exist_ok=True)
    (skill_a_dir / "SKILL.md").write_text("x", encoding="utf-8")
    skill_b_dir = tmp_path / ".opencode" / "skills" / "beta"
    skill_b_dir.mkdir(parents=True, exist_ok=True)
    (skill_b_dir / "SKILL.md").write_text("y", encoding="utf-8")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (skill_a_dir / "SKILL.md").exists()
    assert not (skill_b_dir / "SKILL.md").exists()
    assert not skill_a_dir.exists()
    assert not skill_b_dir.exists()


def test_finalize_repo_prunes_empty_skills_dir(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    skill_dir = tmp_path / ".opencode" / "skills" / "s"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".opencode" / "skills").exists()


def test_finalize_repo_removes_empty_opencode_dir(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    skill_dir = tmp_path / ".opencode" / "skills" / "s"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("x", encoding="utf-8")
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / ".opencode").exists()


def test_finalize_repo_removes_empty_opencode_json(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"$schema": OPENCODE_CONFIG_SCHEMA_URL, "mcp": {}}),
        encoding="utf-8",
    )
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert not (tmp_path / "opencode.json").exists()


def test_finalize_repo_keeps_opencode_json_with_servers(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        json.dumps({"$schema": OPENCODE_CONFIG_SCHEMA_URL, "mcp": {"srv": {"type": "local"}}}),
        encoding="utf-8",
    )
    adapter.finalize_repo_after_ide_removed(tmp_path)
    assert (tmp_path / "opencode.json").exists()


def test_finalize_repo_noop_when_nothing(adapter: OpencodeAdapter, tmp_path: Path) -> None:
    adapter.finalize_repo_after_ide_removed(tmp_path)
