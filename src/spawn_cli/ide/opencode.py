"""OpenCode IDE adapter: skills under .opencode/skills/{name}/SKILL.md, MCP in opencode.json, AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
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


OPENCODE_CONFIG_JSON_FILENAME = "opencode.json"
OPENCODE_CONFIG_SCHEMA_URL = "https://opencode.ai/config.json"


def _build_local_mcp_cmd(server: McpServer) -> list[str]:
    transport = server.transport
    cmd = [transport.command] if transport.command else []
    cmd.extend(transport.args or [])
    return cmd


def _build_opencode_mcp_entry(server: McpServer) -> dict[str, Any]:
    transport = server.transport
    entry: dict[str, Any]
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            cmd = ["spawn", *mcp_stdio_argv(server.extension, server.name)]
        else:
            cmd = _build_local_mcp_cmd(server)
        entry = {"type": "local", "command": cmd, "enabled": True}
    elif transport.type in ("streamable-http", "sse"):
        entry = {"type": "remote", "url": transport.url or "", "enabled": True}
    else:
        cmd = _build_local_mcp_cmd(server)
        entry = {"type": "local", "command": cmd, "enabled": True}
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else v.value or f"${{{k}}}"
            for k, v in server.env.items()
        }
    return entry


class OpencodeAdapter(IdeAdapter):
    key = "opencode"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".opencode").exists() or (target_root / OPENCODE_CONFIG_JSON_FILENAME).exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="unsupported",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".opencode" / "skills" / name
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
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        existing_schema = OPENCODE_CONFIG_SCHEMA_URL
        if config_path.exists():
            data = json.loads(config_path.read_text(encoding="utf-8"))
            existing_schema = data.get("$schema", OPENCODE_CONFIG_SCHEMA_URL)
        else:
            data = {}
        data.setdefault("$schema", existing_schema)
        mcp_servers = data.setdefault("mcp", {})
        if not isinstance(mcp_servers, dict):
            mcp_servers = {}
            data["mcp"] = mcp_servers
        rendered_names = []
        for server in normalized_mcp.servers:
            mcp_servers[server.name] = _build_opencode_mcp_entry(server)
            rendered_names.append(server.name)
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        config_path = target_root / OPENCODE_CONFIG_JSON_FILENAME
        if not config_path.exists():
            return
        data = json.loads(config_path.read_text(encoding="utf-8"))
        mcp_servers = data.get("mcp")
        if isinstance(mcp_servers, dict):
            for name in rendered_mcp_names:
                mcp_servers.pop(name, None)
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("opencode: agent ignore is unsupported; steer via AGENTS.md policy instead")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("opencode: agent ignore is unsupported")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_opencode_repo(target_root)


register(OpencodeAdapter())

__all__ = ["OpencodeAdapter"]
