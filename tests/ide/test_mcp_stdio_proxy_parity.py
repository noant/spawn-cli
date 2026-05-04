"""Golden checks: spawn_stdio_proxy stdio emission matches inline stdio payload except command/args.

overview.md requires cwd parity for proxy vs inlined stdio. Current adapters omit ``cwd`` in emitted IDE
configs for both paths; equality after stripping command/args therefore includes that shared omission until
adapter emitters gain cwd fields (outside Step 4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from spawn_cli.ide.claude_code import ClaudeCodeAdapter
from spawn_cli.ide.codex import CodexAdapter
from spawn_cli.ide.cursor import CursorAdapter
from spawn_cli.ide.gemini_cli import GeminiCliAdapter
from spawn_cli.ide.github_copilot import GitHubCopilotAdapter
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.io.toml_io import load_toml
from spawn_cli.models.mcp import McpEnvVar, McpServer, McpTransport, NormalizedMcp


def _pop_command_args(d: dict) -> None:
    d.pop("command", None)
    d.pop("args", None)


def _assert_stdio_wrapper_golden(proxy_entry: dict, *, extension_id: str, server_name: str) -> None:
    """Proxy path must expose only the Spawn wrapper; inner transport.argv must stay out of IDE config."""
    assert proxy_entry["command"] == "spawn"
    expected = mcp_stdio_argv(extension_id, server_name)
    assert proxy_entry["args"] == expected
    assert "tool-uv-name" not in proxy_entry["args"]


@pytest.mark.parametrize(
    "adapter, read_entries",
    [
        pytest.param(CursorAdapter(), "cursor_json", id="cursor"),
        pytest.param(ClaudeCodeAdapter(), "claude_json", id="claude_code"),
        pytest.param(GeminiCliAdapter(), "gemini_json", id="gemini_cli"),
        pytest.param(CodexAdapter(), "codex_toml", id="codex"),
        pytest.param(GitHubCopilotAdapter(), "vscode_json", id="github_copilot"),
    ],
)
def test_stdio_spawn_proxy_preserves_env_and_stable_spawn_wrapper(
    adapter,
    read_entries: str,
    tmp_path: Path,
) -> None:
    ext_id = "ext-with-dash"
    tr = McpTransport(type="stdio", command="tool-uv-name", args=["--flag"], cwd=".")
    # GitHub Copilot binds secret placeholders to `${input:<server>-<var>}`; two server names ⇒ no byte-identical env.
    env = {"PLAIN": McpEnvVar(value="lit")}
    inline = McpServer(
        name="inline-srv",
        extension=ext_id,
        spawn_stdio_proxy=False,
        transport=tr,
        env=dict(env),
    )
    proxied = McpServer(
        name="proxy-srv",
        extension=ext_id,
        spawn_stdio_proxy=True,
        transport=tr,
        env=dict(env),
    )

    adapter.add_mcp(tmp_path, NormalizedMcp(servers=[inline, proxied]))

    inline_entry: dict
    proxy_entry: dict

    if read_entries == "cursor_json":
        data = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
        inline_entry = dict(data["mcpServers"][inline.name])
        proxy_entry = dict(data["mcpServers"][proxied.name])
    elif read_entries == "claude_json":
        data = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
        inline_entry = dict(data["mcpServers"][inline.name])
        proxy_entry = dict(data["mcpServers"][proxied.name])
    elif read_entries == "gemini_json":
        data = json.loads((tmp_path / ".gemini" / "settings.json").read_text(encoding="utf-8"))
        inline_entry = dict(data["mcpServers"][inline.name])
        proxy_entry = dict(data["mcpServers"][proxied.name])
    elif read_entries == "vscode_json":
        data = json.loads((tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
        inline_entry = dict(data["servers"][inline.name])
        proxy_entry = dict(data["servers"][proxied.name])
        assert proxy_entry["type"] == inline_entry["type"] == "stdio"
    elif read_entries == "codex_toml":
        data = load_toml(tmp_path / ".codex" / "config.toml")
        inline_entry = dict(data["mcp_servers"][inline.name])
        proxy_entry = dict(data["mcp_servers"][proxied.name])
    else:
        raise AssertionError(read_entries)

    _assert_stdio_wrapper_golden(proxy_entry, extension_id=ext_id, server_name=proxied.name)
    ie, pe = dict(inline_entry), dict(proxy_entry)
    _pop_command_args(ie)
    _pop_command_args(pe)
    assert ie == pe, "only command and args differ when spawn_stdio_proxy is true"
