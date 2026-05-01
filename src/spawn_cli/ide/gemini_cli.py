"""Google Gemini CLI IDE adapter: .gemini/skills, settings mcpServers, .geminiignore, GEMINI.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
    rewrite_managed_block,
)
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    register,
    normalize_skill_name,
    render_skill_md,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata


def _build_gemini_mcp_entry(server: McpServer) -> dict:
    transport = server.transport
    entry: dict = {}
    if transport.type == "stdio":
        entry["command"] = transport.command
        entry["args"] = list(transport.args)
    elif transport.type == "streamable-http":
        entry["httpUrl"] = transport.url or ""
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    elif transport.type == "sse":
        entry["url"] = transport.url or ""
        if transport.headers:
            entry["headers"] = {k: f"${{{v}}}" for k, v in transport.headers.items()}
    else:
        entry["command"] = transport.command
        entry["args"] = list(transport.args)
    if server.env:
        entry["env"] = {
            k: f"${{{k}}}" if v.secret else (v.value or f"${{{k}}}")
            for k, v in server.env.items()
        }
    return entry


class GeminiCliAdapter(IdeAdapter):
    key = "gemini-cli"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".gemini").exists() or (target_root / "GEMINI.md").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="native",
                entry_point="gemini-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".gemini" / "skills" / name
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
        settings_path = target_root / ".gemini" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        data = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
        data.setdefault("mcpServers", {})
        rendered_names = []
        for server in normalized_mcp.servers:
            data["mcpServers"][server.name] = _build_gemini_mcp_entry(server)
            rendered_names.append(server.name)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return rendered_names

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        settings_path = target_root / ".gemini" / "settings.json"
        if not settings_path.exists():
            return
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        for name in rendered_mcp_names:
            data.get("mcpServers", {}).pop(name, None)
        settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_ignore_block(target_root / ".geminiignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".geminiignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".geminiignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".geminiignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".geminiignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "GEMINI.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_standard_dotdir_skills_and_mcp(
            target_root,
            ".gemini",
            allow_delete_entire=True,
            unlink_settings_json_when_mcp_servers_empty=True,
        )


register(GeminiCliAdapter())

__all__ = ["GeminiCliAdapter"]
