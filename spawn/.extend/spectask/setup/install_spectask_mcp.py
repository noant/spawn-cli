#!/usr/bin/env python3
"""After-install: uv tool install then upgrade for spectask-mcp; optional Jira setup.

Uses `uv tool install` so no project virtualenv is required. Always runs
`uv tool upgrade spectask-mcp` after install (best-effort; older `uv` without
`tool upgrade` logs a failure). Fresh install needs install first; upgrade alone
errors if the tool is missing.

Spawn runs scripts from materialized packs with the target workspace as cwd when the
CLI installs from repo root (see spawn-ext-guide user-guide / spawn extension commands).
Uses os.getcwd(); no standardized env overrides are documented as of config-yaml schema 1.

Non-zero subprocess runs are logged to stderr; exit code is always 0 (best-effort).
"""

from __future__ import annotations

import os
from pathlib import Path
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


def _run_uv_best_effort(cmd: list[str], cwd: str) -> None:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError as exc:
        print(f"install_spectask_mcp: {cmd[0]} not found: {exc}", file=sys.stderr)
        return
    if proc.returncode != 0:
        _log_uv_failure(cmd, proc)


def _migrate_design_yaml(cwd: str) -> None:
    """Move spec/design.yaml documents into spawn/navigation.yaml; delete the file on success."""
    root = Path(cwd)
    design = root / "spec" / "design.yaml"
    if not design.is_file():
        return
    try:
        from ruamel.yaml import YAML
        from ruamel.yaml.comments import CommentedMap, CommentedSeq

        ry = YAML(typ="rt")
        with design.open("r", encoding="utf-8") as fh:
            data = ry.load(fh) or {}
        if not isinstance(data, dict):
            raise ValueError("spec/design.yaml is not a mapping")
        docs = data.get("documents")
        if docs is None:
            docs = []
        if not isinstance(docs, list):
            raise ValueError("spec/design.yaml documents is not a list")
        rows = []
        seen = set()
        for d in docs:
            if not isinstance(d, dict) or not isinstance(d.get("path"), str):
                continue
            p = d.get("path", "").strip()
            if not p or p in seen:
                continue
            seen.add(p)
            rows.append({"path": p, "description": str(d.get("description", "")).strip()})
        nav = root / "spawn" / "navigation.yaml"
        nav.parent.mkdir(parents=True, exist_ok=True)
        if nav.is_file():
            with nav.open("r", encoding="utf-8") as fh:
                navdata = ry.load(fh)
            if navdata is not None and not isinstance(navdata, dict):
                raise ValueError("spawn/navigation.yaml is not a mapping")
        else:
            navdata = CommentedMap()
        rc = navdata.get("read-contextual")
        if rc is not None and not isinstance(rc, list):
            raise ValueError("spawn/navigation.yaml read-contextual is not a list")
        if not isinstance(rc, list):
            rc = CommentedSeq()
            navdata["read-contextual"] = rc
        rules_seq = None
        for grp in rc:
            if isinstance(grp, dict) and isinstance(grp.get("rules"), list):
                rules_seq = grp["rules"]
                break
        if rules_seq is None:
            grp = CommentedMap()
            rules_seq = CommentedSeq()
            grp["rules"] = rules_seq
            rc.append(grp)
        known = set()
        for section in (navdata.get("read-required"), rc):
            if not isinstance(section, list):
                continue
            for g in section:
                if isinstance(g, dict):
                    for lst in (g.get("rules"), g.get("files")):
                        for item in lst or []:
                            if isinstance(item, dict) and item.get("path"):
                                known.add(str(item["path"]))
        changed = False
        for row in rows:
            if row["path"] in known:
                continue
            m = CommentedMap()
            m["path"] = row["path"]
            m["description"] = row["description"]
            rules_seq.append(m)
            known.add(row["path"])
            changed = True
        with nav.open("w", encoding="utf-8") as fh:
            ry.dump(navdata, fh)
        design.unlink(missing_ok=True)
        if changed:
            try:
                subprocess.run(["spawn", "refresh"], cwd=str(root), check=False)
            except FileNotFoundError:
                print("spectask: spawn not found; navigation rows apply on next spawn run", file=sys.stderr)
    except Exception as exc:
        print(f"spectask: design.yaml migration skipped: {exc}", file=sys.stderr)
        return


def _run_interactive_setup(cwd: str) -> None:
    """Prefer spectask-mcp on PATH; fall back to python -m."""
    commands: list[list[str]] = [["spectask-mcp", "interactive", "--setup"]]
    if sys.platform == "win32":
        commands.append(["python", "-m", "spectask_mcp", "interactive", "--setup"])
    else:
        commands.append(["python3", "-m", "spectask_mcp", "interactive", "--setup"])
        commands.append(["python", "-m", "spectask_mcp", "interactive", "--setup"])

    for cmd in commands:
        try:
            subprocess.run(cmd, cwd=cwd, check=False)
        except FileNotFoundError:
            continue
        return
    sys.stderr.write(
        "install_spectask_mcp: could not run spectask-mcp interactive --setup "
        "(no suitable executable on PATH)\n"
    )


def main() -> int:
    cwd = _cwd()
    _migrate_design_yaml(cwd)
    pkg = "spectask-mcp"
    _run_uv_best_effort(["uv", "tool", "install", pkg], cwd)
    _run_uv_best_effort(["uv", "tool", "upgrade", pkg], cwd)
    _run_interactive_setup(cwd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
