from __future__ import annotations

import json
import warnings
from pathlib import Path

import pytest

from spawn_cli.ide import IGNORE_BLOCK_END, IGNORE_BLOCK_START, SPAWN_BLOCK_END, SPAWN_BLOCK_START
from spawn_cli.ide.gemini_cli import GeminiCliAdapter
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


@pytest.fixture
def adapter() -> GeminiCliAdapter:
    return GeminiCliAdapter()


def test_detect_with_gemini_dir(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    (tmp_path / ".gemini").mkdir()
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_with_gemini_md(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    (tmp_path / "GEMINI.md").write_text("x", encoding="utf-8")
    assert adapter.detect(tmp_path).used_in_repo is True


def test_detect_neither(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    assert adapter.detect(tmp_path).used_in_repo is False


def test_add_skills_creates_under_gemini(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_skills(
        tmp_path,
        [SkillMetadata(name="G", description="d", content="b")],
    )
    assert (tmp_path / ".gemini" / "skills" / "g" / "SKILL.md").exists()


def test_add_skills_warns_on_overwrite(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="1")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        adapter.add_skills(tmp_path, [SkillMetadata(name="s", description="d", content="2")])
        assert len(w) == 1


def test_remove_skills_deletes_file(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_skills(tmp_path, [SkillMetadata(name="z", description="d", content="c")])
    adapter.remove_skills(tmp_path, [{"skill": "z", "path": ".gemini/skills/z/SKILL.md"}])
    assert not (tmp_path / ".gemini" / "skills" / "z" / "SKILL.md").exists()


def test_add_mcp_creates_settings_json(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_mcp(
        tmp_path,
        NormalizedMcp(
            servers=[
                McpServer(
                    name="s",
                    extension="e",
                    transport=McpTransport(type="stdio", command="c", args=["a"]),
                )
            ]
        ),
    )
    p = tmp_path / ".gemini" / "settings.json"
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "mcpServers" in data


def test_add_mcp_merges_existing_settings(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    (tmp_path / ".gemini").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".gemini" / "settings.json").write_text(
        json.dumps({"context": {"fileName": "GEMINI.md"}, "mcpServers": {}}),
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
    data = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))
    assert data["context"]["fileName"] == "GEMINI.md"
    assert "n" in data["mcpServers"]


def test_add_mcp_stdio_shape(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
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
    entry = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))[
        "mcpServers"
    ]["s"]
    assert entry["command"] == "uvx"
    assert entry["args"] == ["mcp"]


def test_add_mcp_http_uses_http_url(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
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
    entry = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))[
        "mcpServers"
    ]["h"]
    assert entry["httpUrl"] == "https://example.com/mcp"


def test_add_mcp_sse_uses_url(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
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
    entry = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))[
        "mcpServers"
    ]["h"]
    assert entry["url"] == "https://ex.com/sse"


def test_add_mcp_secret_placeholder(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
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
    entry = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))[
        "mcpServers"
    ]["s"]
    assert entry["env"]["TOKEN"] == "${TOKEN}"


def test_remove_mcp_removes_entry(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
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
    data = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))
    assert "a" not in data["mcpServers"]
    assert "b" in data["mcpServers"]


def test_add_agent_ignore_creates_geminiignore(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["*.log"])
    text = (tmp_path / ".geminiignore").read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START in text
    assert "*.log" in text
    assert IGNORE_BLOCK_END in text


def test_remove_agent_ignore_removes_block(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    adapter.add_agent_ignore(tmp_path, ["g"])
    adapter.remove_agent_ignore(tmp_path, [])
    text = (tmp_path / ".geminiignore").read_text(encoding="utf-8")
    assert IGNORE_BLOCK_START not in text


def test_rewrite_entry_point_gemini_md(adapter: GeminiCliAdapter, tmp_path: Path) -> None:
    rel = adapter.rewrite_entry_point(tmp_path, "gem")
    assert rel == "GEMINI.md"
    t = (tmp_path / "GEMINI.md").read_text(encoding="utf-8")
    assert SPAWN_BLOCK_START in t and "gem" in t
