"""OpenAI Codex IDE adapter: skills under .agents/, MCP in .codex/config.toml, AGENTS.md."""

from __future__ import annotations

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
from spawn_cli.io.toml_io import load_toml, save_toml
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


def _build_toml_server_entry(server: McpServer) -> dict:
    transport = server.transport
    entry: dict = {}
    if transport.type == "stdio":
        entry["command"] = transport.command
        entry["args"] = list(transport.args)
    else:
        entry["url"] = transport.url
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else (v.value or f"${{{k}}}")
            for k, v in server.env.items()
        }
    return entry


class CodexAdapter(IdeAdapter):
    key = "codex"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".codex").exists() or (target_root / ".agents").exists()
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
            skill_dir = target_root / ".agents" / "skills" / name
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
        config_path = target_root / ".codex" / "config.toml"
        data = load_toml(config_path)
        mcp_servers = data.setdefault("mcp_servers", {})
        if not isinstance(mcp_servers, dict):
            mcp_servers = {}
            data["mcp_servers"] = mcp_servers
        rendered_names = []
        for server in normalized_mcp.servers:
            mcp_servers[server.name] = _build_toml_server_entry(server)
            rendered_names.append(server.name)
        save_toml(config_path, data)
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        config_path = target_root / ".codex" / "config.toml"
        if not config_path.is_file():
            return
        data = load_toml(config_path)
        mcp_servers = data.get("mcp_servers")
        if isinstance(mcp_servers, dict):
            for name in rendered_mcp_names:
                mcp_servers.pop(name, None)
        save_toml(config_path, data)

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("codex: agent ignore is unsupported; steer via AGENTS.md policy instead")

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("codex: agent ignore is unsupported")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()


register(CodexAdapter())

__all__ = ["CodexAdapter"]
