from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import IGNORE_BLOCK_END, IGNORE_BLOCK_START, SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.github_copilot import GitHubCopilotAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> GitHubCopilotAdapter:
    return GitHubCopilotAdapter()


def test_detect_with_github_dir(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    (tmp_path / ".github").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_with_vscode_dir(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    (tmp_path / ".vscode").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_neither(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_add_skills_creates_under_github(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="Skill One", description="d", content="b")],
    )
    assert (tmp_path / ".github" / "skills" / "skill-one" / "SKILL.md").exists()


def test_add_skills_warns_on_overwrite(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="1")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="2")])
        assert len(w) == 1


def test_remove_skills_deletes_file(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="z", description="d", content="c")])
    adapter.remove_skills(tmp_path, [{"skill": "z", "path": ".github/skills/z/SKILL.md"}])
    assert not (tmp_path / ".github" / "skills" / "z" / "SKILL.md").exists()


def test_add_mcp_creates_vscode_mcp_json(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
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
    p = tmp_path / ".vscode" / "mcp.json"
    assert p.exists()


def test_add_mcp_uses_servers_key_not_mcp_servers(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="x",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                )
            ]
        ),
    )
    data = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert "servers" in data
    assert "mcpServers" not in data


def test_add_mcp_secret_generates_input(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="spectask-search",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"SPECTASK_TOKEN": McpEnvVar(secret=True)},
                )
            ]
        ),
    )
    data = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert data["servers"]["spectask-search"]["env"]["SPECTASK_TOKEN"] == "${input:spectask-search-spectask-token}"
    assert any(
        inp.get("id") == "spectask-search-spectask-token" for inp in data.get("inputs", [])
    )


def test_add_mcp_merges_inputs_no_duplicate(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    nm = NormalizedMcp(
        servers=[
            McpServer(
                name="srv1",
                extension="e",
                transport=McpTransport(type="stdio", command="c", args=[]),
                env={"K": McpEnvVar(secret=True)},
            )
        ]
    )
    adapter.add_mcp(tmp_path, nm)
    adapter.add_mcp(tmp_path, nm)
    data = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    ids = [inp["id"] for inp in data["inputs"]]
    assert ids.count("srv1-k") == 1


def test_remove_mcp_removes_server_and_inputs(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="spectask-search",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=[]),
                    env={"SPECTASK_TOKEN": McpEnvVar(secret=True)},
                ),
                McpServer(
                    name="other",
                    extension="e",
                    transport=McpTransport(type="stdio", command="d", args=[]),
                ),
            ]
        ),
    )
    adapter.remove_mcp(tmp_path, ["spectask-search"])
    data = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
    assert "spectask-search" not in data["servers"]
    assert "other" in data["servers"]
    assert not any(
        inp["id"].startswith("spectask-search-") for inp in data.get("inputs", [])
    )


def test_add_agent_ignore_warns(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1


def test_remove_agent_ignore_warns(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.remove_agent_ignore(tmp_path, ["**"])
        assert len(w) == 1


def test_rewrite_entry_point_writes_copilot_instructions(
    adapter: GitHubCopilotAdapter, tmp_path: Path
) -> None:
    adapter.rewrite_entry_point(tmp_path, "hello")
    text = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in text
    assert "hello" in text


def test_rewrite_entry_point_also_writes_agents_md(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    adapter.rewrite_entry_point(tmp_path, "same")
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "same" in text
    assert SPAWN_BLOCK_END in text


def test_rewrite_entry_point_returns_copilot_path(adapter: GitHubCopilotAdapter, tmp_path: Path) -> None:
    assert adapter.rewrite_entry_point(tmp_path, "p") == ".github/copilot-instructions.md"
