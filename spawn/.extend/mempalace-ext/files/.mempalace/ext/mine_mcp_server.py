#!/usr/bin/env python3
"""Minimal MCP (stdio, JSON lines) that exposes ``mempalace mine`` as tool ``mempalace_mine``.

Spawn / Cursor run this with workspace cwd set to the repo root, e.g.:

    python .mempalace/ext/mine_mcp_server.py

Requires the ``mempalace`` CLI from the same environment (``pip install mempalace``).
Protocol shape aligned with MemPalace's ``mcp_server.py`` (initialize, tools/list, tools/call).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("mempalace_mine_mcp")
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

SUPPORTED_PROTOCOL_VERSIONS = [
    "2025-11-25",
    "2025-06-18",
    "2025-03-26",
    "2024-11-05",
]


def _truthy_env_opt(name: str) -> bool:
    return (os.environ.get(name, "") or "").strip().lower() in ("1", "true", "yes")


def _resolved_cli_palace(root: str, palace_tool_arg: str | None) -> str | None:
    """Absolute palace for ``--palace``, or ``None`` to let MemPalace use its defaults.

    Matches after_install: repo-local ``<cwd>/.mempalace/palace`` unless
    ``MEMPALACE_EXTENSION_GLOBAL_PALACE`` or env already sets palace path semantics
    via ``MEMPALACE_PALACE_PATH`` / ``MEMPAL_PALACE_PATH``. Explicit tool ``palace`` wins.
    """
    if palace_tool_arg:
        return os.path.abspath(os.path.expanduser(str(palace_tool_arg)))
    inherited = (
        (os.environ.get("MEMPALACE_PALACE_PATH") or "").strip()
        or (os.environ.get("MEMPAL_PALACE_PATH") or "").strip()
    )
    if inherited:
        return os.path.abspath(os.path.expanduser(inherited))
    if _truthy_env_opt("MEMPALACE_EXTENSION_GLOBAL_PALACE"):
        return None
    return os.path.abspath(os.path.join(root, ".mempalace", "palace"))


def _mempalace_cli() -> list[str]:
    d = Path(sys.executable).resolve().parent
    for name in ("mempalace.exe", "mempalace"):
        p = d / name
        if p.exists():
            return [str(p)]
    return [sys.executable, "-m", "mempalace"]


def _subprocess_env_for_mempalace_child() -> dict[str, str]:
    """Environment for MemPalace CLI subprocesses when stdout/stderr are captured.

    On Windows the child's pipe encoding is often a legacy code page; palace text
    with Unicode (e.g. U+2192) can raise UnicodeEncodeError before wakeup.md is written.
    """
    env = os.environ.copy()
    if sys.platform == "win32":
        env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _wake_up_write_wakeup_md(
    root: str, palace_path: str | None, wing: str | None
) -> dict[str, Any]:
    """Run ``mempalace wake-up`` and write ``<root>/.mempalace/wakeup.md``."""

    wakeup_dir = os.path.join(root, ".mempalace")
    try:
        os.makedirs(wakeup_dir, exist_ok=True)
    except OSError as e:
        return {
            "wakeup_written": False,
            "wakeup_path": os.path.join(wakeup_dir, "wakeup.md"),
            "wakeup_error": str(e),
        }

    wakeup_path = os.path.join(wakeup_dir, "wakeup.md")
    wake_cmd: list[str] = []
    wake_cmd.extend(_mempalace_cli())
    if palace_path:
        wake_cmd.extend(["--palace", os.path.expanduser(str(palace_path))])
    wake_cmd.append("wake-up")
    if wing:
        wake_cmd.extend(["--wing", str(wing)])

    logger.info("running wake-up → %s: %s", wakeup_path, " ".join(wake_cmd))
    proc = subprocess.run(
        wake_cmd,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_subprocess_env_for_mempalace_child(),
    )
    if proc.returncode != 0:
        err = (proc.stderr or "").strip()
        return {
            "wakeup_written": False,
            "wakeup_path": wakeup_path,
            "wakeup_error": err[-20_000:] if len(err) > 20_000 else err or f"exit {proc.returncode}",
        }

    body = proc.stdout if proc.stdout is not None else ""
    try:
        Path(wakeup_path).write_text(body, encoding="utf-8", newline="\n")
    except OSError as e:
        return {
            "wakeup_written": False,
            "wakeup_path": wakeup_path,
            "wakeup_error": str(e),
        }

    return {"wakeup_written": True, "wakeup_path": wakeup_path}


def _tool_mempalace_mine(
    directory: str = ".",
    mode: str = "projects",
    wing: str | None = None,
    palace: str | None = None,
) -> dict[str, Any]:
    """Run ``mempalace [--palace P] mine <dir> ...`` and return process output.

    After a successful mine, runs ``wake-up`` and overwrites ``.mempalace/wakeup.md``.

    Rare CLI options (dry-run, limit, --no-gitignore, --include-ignored,
    --extract general, --redetect-origin, custom --agent) are intentionally not
    exposed on the MCP tool — use the terminal for those.
    """
    root = os.getcwd()
    dir_abs = os.path.abspath(os.path.join(root, str(directory)))
    if not os.path.isdir(dir_abs):
        return {"error": f"not a directory: {dir_abs}"}

    cli_palace = _resolved_cli_palace(root, palace)

    cmd: list[str] = []
    cmd.extend(_mempalace_cli())
    if cli_palace:
        cmd.extend(["--palace", cli_palace])
    cmd.append("mine")
    cmd.append(dir_abs)

    if mode and mode != "projects":
        cmd.extend(["--mode", mode])
    if wing:
        cmd.extend(["--wing", str(wing)])
    if mode == "convos":
        cmd.extend(["--extract", "exchange"])
    cmd.extend(["--agent", "mcp"])

    logger.info("running: %s", " ".join(cmd))
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_subprocess_env_for_mempalace_child(),
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    result: dict[str, Any] = {
        "exit_code": proc.returncode,
        "stdout": out[-200_000:] if len(out) > 200_000 else out,
        "stderr": err[-200_000:] if len(err) > 200_000 else err,
    }
    if proc.returncode == 0:
        result.update(_wake_up_write_wakeup_md(root, cli_palace, wing))
    return result


TOOLS: dict[str, dict[str, Any]] = {
    "mempalace_mine": {
        "description": (
            "Run mempalace mine on a directory: mode=projects (code/docs, respects .gitignore) "
            "or mode=convos (chat exports; uses default --extract exchange). "
            "Optional wing and palace override config. "
            "After a successful mine, runs mempalace wake-up and writes .mempalace/wakeup.md. "
            "Advanced mine flags are CLI-only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Path to mine, relative to workspace cwd or absolute (default: '.').",
                    "default": ".",
                },
                "mode": {
                    "type": "string",
                    "enum": ["projects", "convos"],
                    "description": "Ingest mode (default: projects).",
                    "default": "projects",
                },
                "wing": {
                    "type": "string",
                    "description": "Optional wing name override.",
                },
                "palace": {
                    "type": "string",
                    "description": (
                        "Optional explicit --palace; if omitted, uses MEMPALACE_PALACE_PATH when set, "
                        "otherwise <cwd>/.mempalace/palace unless MEMPALACE_EXTENSION_GLOBAL_PALACE=1."
                    ),
                },
            },
        },
        "handler": _tool_mempalace_mine,
    },
}


def _handle_request(request: dict) -> dict | None:
    method = request.get("method") or ""
    params = request.get("params") or {}
    req_id = request.get("id")

    if method == "initialize":
        client_version = params.get("protocolVersion", SUPPORTED_PROTOCOL_VERSIONS[-1])
        negotiated = (
            client_version
            if client_version in SUPPORTED_PROTOCOL_VERSIONS
            else SUPPORTED_PROTOCOL_VERSIONS[0]
        )
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": negotiated,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "mempalace-mine-mcp", "version": "1.0.0"},
            },
        }

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method.startswith("notifications/"):
        return None

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {"name": n, "description": t["description"], "inputSchema": t["input_schema"]}
                    for n, t in TOOLS.items()
                ]
            },
        }

    if method == "tools/call":
        tool_name = params.get("name")
        tool_args = params.get("arguments") or {}
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        schema_props = TOOLS[tool_name]["input_schema"].get("properties", {})
        tool_args = {k: v for k, v in tool_args.items() if k in schema_props}
        try:
            result = TOOLS[tool_name]["handler"](**tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except TypeError as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32602, "message": str(e)},
            }
        except Exception:
            logger.exception("tool error")
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": "Internal tool error"},
            }

    if req_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Unknown method: {method}"},
    }


def main() -> None:
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = _handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except json.JSONDecodeError as e:
            logger.error("bad json: %s", e)
        except Exception as e:
            logger.error("server error: %s", e)


if __name__ == "__main__":
    main()
