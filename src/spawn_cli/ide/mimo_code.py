"""Mimo Code adapter: .mimocode/skills, .mimocode/mimocode.json (mcp + permission), AGENTS.md."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

from spawn_cli.core import low_level as ll
from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    normalize_skill_name,
    register,
    render_skill_md,
    rewrite_managed_block,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata

_CONFIG = Path(".mimocode") / "mimocode.json"


def _load_config(target_root: Path) -> dict:
    path = target_root / _CONFIG
    if not path.exists():
        if (target_root / ".mimocode" / "mimocode.jsonc").exists():
            warnings.warn(
                "Mimo Code: Spawn manages .mimocode/mimocode.json; existing mimocode.jsonc is not merged",
                SpawnWarning,
            )
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpawnError(f"Mimo Code config is not valid JSON: {path} ({exc})") from exc


def _save_config(target_root: Path, data: dict) -> None:
    path = target_root / _CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _build_mcp_entry(server: McpServer) -> dict:
    transport = server.transport
    if transport.type == "stdio":
        if server.spawn_stdio_proxy:
            entry = {
                "type": "local",
                "command": ["spawn"] + mcp_stdio_argv(server.extension, server.name),
            }
        else:
            entry = {"type": "local", "command": [transport.command, *list(transport.args)]}
    else:  # streamable-http and sse both render as remote
        entry = {"type": "remote", "url": transport.url}
        if transport.headers:
            entry["headers"] = {k: f"{{env:{v}}}" for k, v in transport.headers.items()}
    entry["enabled"] = True
    if server.env:
        entry["environment"] = {
            k: f"{{env:{k}}}" if v.secret else (v.value or f"{{env:{k}}}")
            for k, v in server.env.items()
        }
    return entry


class MimoCodeAdapter(IdeAdapter):
    key = "mimo-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (target_root / ".mimocode").exists()
        return DetectResult(
            used_in_repo=used,
            capabilities=IdeCapabilities(
                skills="native",
                mcp="project",
                agent_ignore="project",
                entry_point="agents-md",
            ),
        )

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".mimocode" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}", SpawnWarning)
            # Mimo Code requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}))
            skill_path.write_text(rendered, encoding="utf-8")
            results.append({"skill": skill.name, "path": skill_path.relative_to(target_root).as_posix()})
        return results

    def remove_skills(self, target_root: Path, rendered_paths: list[dict]) -> None:
        for entry in rendered_paths:
            p = target_root / entry["path"]
            if p.exists():
                p.unlink()
            if p.parent.exists() and not any(p.parent.iterdir()):
                p.parent.rmdir()

    def add_mcp(self, target_root: Path, normalized_mcp: NormalizedMcp) -> list[str]:
        data = _load_config(target_root)
        mcp = data.setdefault("mcp", {})
        for server in normalized_mcp.servers:
            mcp[server.name] = _build_mcp_entry(server)
        _save_config(target_root, data)
        return [s.name for s in normalized_mcp.servers]

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        if not (target_root / _CONFIG).exists():
            return
        data = _load_config(target_root)
        mcp = data.get("mcp")
        if isinstance(mcp, dict):
            for name in rendered_mcp_names:
                mcp.pop(name, None)
            if not mcp:
                data.pop("mcp", None)
        _save_config(target_root, data)

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        data = _load_config(target_root)
        perms = data.setdefault("permission", {})
        for section in ("read", "edit"):
            rules = perms.setdefault(section, {})
            if not isinstance(rules, dict):
                rules = {}
                perms[section] = rules
            for glob in globs:
                rules[glob] = "deny"
        _save_config(target_root, data)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        if not (target_root / _CONFIG).exists():
            return
        data = _load_config(target_root)
        perms = data.get("permission")
        if not isinstance(perms, dict):
            return
        drop = set(globs)
        for section in ("read", "edit"):
            rules = perms.get(section)
            if isinstance(rules, dict):
                for glob in drop:
                    rules.pop(glob, None)
                if not rules:
                    perms.pop(section, None)
        if not perms:
            data.pop("permission", None)
        _save_config(target_root, data)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        recorded = ll.get_agent_ignore_list(target_root, self.key)
        if recorded:
            self.remove_agent_ignore(target_root, recorded)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_mimo_code_repo(target_root)


register(MimoCodeAdapter())

__all__ = ["MimoCodeAdapter"]
