"""Cursor IDE adapter: skills, MCP, agent ignore, AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
)
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


def _build_mcp_server_entry(server: McpServer) -> dict:
    """Convert McpServer to .cursor/mcp.json entry (mcpServers format)."""
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            entry = {"command": "spawn", "args": mcp_stdio_argv(server.extension, server.name)}
        else:
            entry = {"command": transport.command, "args": transport.args}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": transport.type, "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    else:
        entry = {"command": transport.command, "args": transport.args}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry


class CursorAdapter(IdeAdapter):
    key = "cursor"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".cursor").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="native",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".cursor" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            skill_path.write_text(render_skill_md(skill), encoding="utf-8")
            rel = skill_path.relative_to(target_root).as_posix()
            results.append({"skill": skill.name, "path": rel})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        """Merge Spawn-owned servers into .cursor/mcp.json (mcpServers format)."""
        mcp_path = target_root / ".cursor" / "mcp.json"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            entry = _build_mcp_server_entry(server)
            data["mcpServers"][server.name] = entry
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        """Remove named entries from .cursor/mcp.json."""
        mcp_path = target_root / ".cursor" / "mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".cursorignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".cursorignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".cursorignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".cursorignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".cursorignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return str(ep.relative_to(target_root))

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_standard_dotdir_skills_and_mcp(target_root, ".cursor", allow_delete_entire=True)


register(CursorAdapter())

__all__ = ["CursorAdapter"]
