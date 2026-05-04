"""Runtime stdio MCP proxy: resolve server from platform JSON and exec inner command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from spawn_cli.core.errors import SpawnError
from spawn_cli.core.low_level import list_extensions, list_mcp, merged_os_environ_with_mcp_env


def run_mcp_stdio_proxy(target_root: Path, extension_id: str, server_name: str) -> int:
    if extension_id not in list_extensions(target_root):
        raise SpawnError(
            f"unknown extension {extension_id!r}: install it under spawn/.extend/<id>/ "
            f"(see: spawn extension list)."
        )

    nm = list_mcp(target_root, extension_id)
    srv = next((s for s in nm.servers if s.name == server_name), None)
    existing = [s.name for s in nm.servers]
    if srv is None:
        raise SpawnError(
            f"unknown MCP server {server_name!r} for extension {extension_id!r}; "
            f"declared servers: {existing}"
        )

    if not srv.spawn_stdio_proxy:
        raise SpawnError(
            f"MCP server {server_name!r} in extension {extension_id!r} is not enabled for "
            f"stdio proxy: set \"spawn_stdio_proxy\": true on that server in "
            f"extsrc/mcp/*.json (then reinstall or refresh)."
        )

    if srv.transport.type != "stdio":
        raise SpawnError(
            f"MCP server {server_name!r} uses transport type {srv.transport.type!r}; "
            f"spawn mcp_stdio requires type \"stdio\"."
        )

    cmd = srv.transport.command
    if not cmd:
        raise SpawnError(
            f"MCP server {server_name!r} has no transport.command; "
            f"fix stdio transport in extension MCP JSON."
        )

    argv = [cmd, *srv.transport.args]
    cwd_path = (target_root / srv.transport.cwd).resolve()
    child_env = merged_os_environ_with_mcp_env(os.environ, srv.env)

    try:
        with subprocess.Popen(
            argv,
            cwd=str(cwd_path),
            env=child_env,
            stdin=sys.stdin.buffer,
            stdout=sys.stdout.buffer,
            stderr=None,
            shell=False,
            bufsize=0,
        ) as proc:
            return int(proc.wait())
    except OSError as e:
        raise SpawnError(f"failed to start MCP server {server_name!r}: {e}") from e
