"""Detect vacant IDE-managed filesystem trees after teardown (skills/MCP removals)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


def json_value_nonempty(v: object) -> bool:
    """True if nested JSON-ish value carries user-visible substance."""
    if v is None:
        return False
    if isinstance(v, dict):
        return len(v) > 0
    if isinstance(v, list):
        return len(v) > 0
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    return True


def mcp_json_mcp_servers_format_is_empty(path: Path) -> bool:
    """True when path is Cursor or Claude-root style JSON ({mcpServers?: ...})."""
    if not path.is_file():
        return False
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    if data == {}:
        return True
    servers = data.get("mcpServers")
    srv_empty = servers in (None, {}) or (isinstance(servers, dict) and len(servers) == 0)
    if not srv_empty:
        return False
    for k, v in data.items():
        if k != "mcpServers" and json_value_nonempty(v):
            return False
    return True


def vscode_servers_mcp_json_is_empty(path: Path) -> bool:
    """True when path is VS Code MCP format (`servers`, `inputs`). Used for .vscode/mcp.json."""
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(data, dict):
        return False
    if data == {}:
        return True
    servers = data.get("servers")
    srv_empty = servers in (None, {}) or (isinstance(servers, dict) and len(servers) == 0)
    inputs = data.get("inputs")
    inp_empty = inputs in (None, []) or (isinstance(inputs, list) and len(inputs) == 0)
    if not (srv_empty and inp_empty):
        return False
    for k, v in data.items():
        if k not in ("servers", "inputs") and json_value_nonempty(v):
            return False
    return True


def dir_has_any_file(root: Path) -> bool:
    """True if any regular file exists under root."""
    if not root.is_dir():
        return False
    try:
        for p in root.rglob("*"):
            if p.is_file():
                return True
    except OSError:
        return True
    return False


def prune_empty_directories_under(container: Path) -> None:
    """Remove descendant directories bottom-up while empty (excluding container itself)."""
    if not container.is_dir():
        return
    dirs = [p for p in container.rglob("*") if p.is_dir()]
    dirs.sort(key=lambda p: len(p.parts), reverse=True)
    for d in dirs:
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except OSError:
            pass


def ide_dotdir_is_entirely_removable(root: Path, *, allow_delete_entire: bool) -> bool:
    """
    Whole-directory removal permitted only when enabled and container has zero files beneath.
    """
    if not allow_delete_entire or not root.exists():
        return False
    return not dir_has_any_file(root)


def try_unlink_empty_mcp_mcp_servers(path: Path) -> None:
    if mcp_json_mcp_servers_format_is_empty(path):
        path.unlink(missing_ok=True)


def try_unlink_empty_vscode_mcp(path: Path) -> None:
    if vscode_servers_mcp_json_is_empty(path):
        path.unlink(missing_ok=True)


def finalize_standard_dotdir_skills_and_mcp(
    target_root: Path,
    rel_dir: str,
    *,
    allow_delete_entire: bool,
    unlink_settings_json_when_mcp_servers_empty: bool = False,
) -> None:
    """Shared layout: IDE dotdir plus optional MCP JSON files."""
    root = target_root / rel_dir
    if not root.is_dir():
        return
    try_unlink_empty_mcp_mcp_servers(root / "mcp.json")
    if unlink_settings_json_when_mcp_servers_empty:
        sj = root / "settings.json"
        if sj.is_file():
            try_unlink_empty_mcp_mcp_servers(sj)
    prune_empty_directories_under(root)
    if ide_dotdir_is_entirely_removable(root, allow_delete_entire=allow_delete_entire):
        shutil.rmtree(root, ignore_errors=True)


def claude_root_mcp_maybe_unlink(target_root: Path) -> None:
    try_unlink_empty_mcp_mcp_servers(target_root / ".mcp.json")


def claude_settings_maybe_unlink(path: Path) -> None:
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if data == {}:
        path.unlink(missing_ok=True)
        return
    if not isinstance(data, dict):
        return
    perm = data.get("permissions")
    if isinstance(perm, dict) and perm.get("deny") == [] and set(data.keys()) == {"permissions"}:
        if set(perm.keys()) <= {"deny"}:
            path.unlink(missing_ok=True)


def finalize_claude_repo(target_root: Path) -> None:
    """Claude adapter: repo `.mcp.json`, `.claude/{skills,settings,...}`, drop `.claude` if vacant."""
    claude_root_mcp_maybe_unlink(target_root)
    settings = target_root / ".claude" / "settings.json"
    claude_settings_maybe_unlink(settings)
    finalize_standard_dotdir_skills_and_mcp(
        target_root,
        ".claude",
        allow_delete_entire=True,
        unlink_settings_json_when_mcp_servers_empty=False,
    )


def finalize_codex_repo(target_root: Path) -> None:
    from spawn_cli.io.toml_io import load_toml

    agents = target_root / ".agents"
    codex_cfg = target_root / ".codex" / "config.toml"
    if codex_cfg.is_file():
        data = load_toml(codex_cfg)
        if isinstance(data, dict) and (
            data == {} or (set(data.keys()) <= {"mcp_servers"} and not data.get("mcp_servers"))
        ):
            codex_cfg.unlink(missing_ok=True)
    prune_empty_directories_under(codex_cfg.parent)
    prune_empty_directories_under(agents)
    codex_root = target_root / ".codex"
    try:
        if codex_root.is_dir() and not any(codex_root.iterdir()):
            codex_root.rmdir()
    except OSError:
        pass
    if agents.is_dir() and not dir_has_any_file(agents):
        shutil.rmtree(agents, ignore_errors=True)


def finalize_github_copilot_repo(target_root: Path) -> None:
    try_unlink_empty_vscode_mcp(target_root / ".vscode" / "mcp.json")
    prune_empty_directories_under(target_root / ".github" / "skills")
    sk = target_root / ".github" / "skills"
    try:
        if sk.is_dir() and not any(sk.iterdir()):
            sk.rmdir()
    except OSError:
        pass


__all__ = [
    "dir_has_any_file",
    "finalize_claude_repo",
    "finalize_codex_repo",
    "finalize_github_copilot_repo",
    "finalize_standard_dotdir_skills_and_mcp",
    "ide_dotdir_is_entirely_removable",
    "json_value_nonempty",
    "mcp_json_mcp_servers_format_is_empty",
    "prune_empty_directories_under",
    "vscode_servers_mcp_json_is_empty",
]
