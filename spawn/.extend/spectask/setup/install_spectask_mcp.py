#!/usr/bin/env python3
"""After-install: uv tool install then upgrade for spectask-mcp; optional Jira setup.

Uses `uv tool install` so no project virtualenv is required. Always runs
`uv tool upgrade spectask-mcp` after install (best-effort; older `uv` without
`tool upgrade` logs a failure). Fresh install needs install first; upgrade alone
errors if the tool is missing.

Spawn runs scripts from materialized packs with the target workspace as cwd when the
CLI installs from repo root (see spawn-ext-guide user-guide / spawn extension commands).
Uses os.getcwd(); no standardized env overrides are documented as of config-yaml schema 1.

Non-zero subprocess runs are logged to stderr; exit code propagates failures.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any


def _cwd() -> str:
    """Target workspace directory for spawned subprocesses."""
    return os.getcwd()


def _log_uv_failure(cmd: list[str], proc: subprocess.CompletedProcess[Any]) -> None:
    sys.stderr.write(
        f"install_spectask_mcp: command failed rc={proc.returncode}: {' '.join(cmd)}\n"
    )


def _run_uv_best_effort(cmd: list[str], cwd: str) -> int:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        _log_uv_failure(cmd, proc)
    return proc.returncode


def _run_interactive_setup(cwd: str) -> int:
    """Prefer spectask-mcp on PATH; fall back to python -m. Returns 0 on success."""
    commands: list[list[str]] = [["spectask-mcp", "interactive", "--setup"]]
    if sys.platform == "win32":
        commands.append(["python", "-m", "spectask_mcp", "interactive", "--setup"])
    else:
        commands.append(["python3", "-m", "spectask_mcp", "interactive", "--setup"])
        commands.append(["python", "-m", "spectask_mcp", "interactive", "--setup"])

    for cmd in commands:
        try:
            proc = subprocess.run(
                cmd, cwd=cwd, stdin=subprocess.DEVNULL, check=False
            )
        except FileNotFoundError:
            continue
        if proc.returncode != 0:
            sys.stderr.write(
                f"install_spectask_mcp: command failed rc={proc.returncode}: "
                f"{' '.join(cmd)}\n"
            )
        return proc.returncode
    sys.stderr.write(
        "install_spectask_mcp: could not run spectask-mcp interactive --setup "
        "(no suitable executable on PATH)\n"
    )
    return 1


def main() -> int:
    cwd = _cwd()
    pkg = "spectask-mcp"
    failed = False
    if _run_uv_best_effort(["uv", "tool", "install", pkg], cwd) != 0:
        failed = True
    _run_uv_best_effort(["uv", "tool", "upgrade", pkg], cwd)
    if _run_interactive_setup(cwd) != 0:
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
