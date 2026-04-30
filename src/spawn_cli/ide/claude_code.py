"""Anthropic Claude Code IDE adapter: .claude/skills, root .mcp.json, settings permissions, CLAUDE.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

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


def _build_generic_mcp_entry(server: McpServer) -> dict:
    transport = server.transport
    if transport.type == "stdio":
        entry: dict = {"command": transport.command, "args": list(transport.args)}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": transport.type, "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    else:
        entry = {"command": transport.command, "args": list(transport.args)}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry


class ClaudeCodeAdapter(IdeAdapter):
    key = "claude-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".claude").exists() or (target_root / "CLAUDE.md").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="claude-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".claude" / "skills" / name
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
        mcp_path = target_root / ".mcp.json"
        data = json.loads(mcp_path.read_text(encoding="utf-8")) if mcp_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            data["mcpServers"][server.name] = _build_generic_mcp_entry(server)
            rendered_names.append(server.name)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        mcp_path = target_root / ".mcp.json"
        if not mcp_path.exists():
            return
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        mcp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        settings_path = target_root / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        perms = data.setdefault("permissions", {})
        deny = perms.setdefault("deny", [])
        if not isinstance(deny, list):
            deny_list: list = []
            perms["deny"] = deny_list
        else:
            deny_list = deny
        for glob in globs:
            if glob not in deny_list:
                deny_list.append(glob)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        settings_path = target_root / ".claude" / "settings.json"
        if not settings_path.exists():
            return
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        perms = data.get("permissions")
        if not isinstance(perms, dict):
            return
        deny = perms.get("deny")
        if not isinstance(deny, list):
            return
        drop = set(globs)
        perms["deny"] = [g for g in deny if g not in drop]
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "CLAUDE.md"
        if (target_root / ".claude" / "CLAUDE.md").exists():
            warnings.warn(
                "Claude Code: .claude/CLAUDE.md exists but Spawn writes to repo-root CLAUDE.md. "
                "Update .claude/CLAUDE.md manually if needed."
            )
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()


register(ClaudeCodeAdapter())

__all__ = ["ClaudeCodeAdapter"]
