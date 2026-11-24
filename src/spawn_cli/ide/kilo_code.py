"""Kilo Code adapter: .kilo/skills, .kilo/kilo.json (mcp), .kilocodeignore, AGENTS.md."""

from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from spawn_cli.errors import SpawnError, SpawnWarning
from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide._helpers import (
    clear_split_agent_ignore_file,
    remove_ignore_block,
    rewrite_core_agent_ignore_region,
    rewrite_extension_agent_ignore_region,
    rewrite_ignore_block,
    rewrite_managed_block,
)
from spawn_cli.ide.mcp_stdio_argv import mcp_stdio_argv
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    normalize_skill_name,
    register,
    render_skill_md,
)
from spawn_cli.models.mcp import McpServer, NormalizedMcp
from spawn_cli.models.skill import SkillMetadata

_CONFIG = Path(".kilo") / "kilo.json"


def _sanitize_skill_name(name: str) -> str:
    # Kilo: name regex ^[a-z0-9]+(-[a-z0-9]+)*$, max 64 chars (rule 04).
    name = normalize_skill_name(name)
    name = name.replace("_", "-").replace(".", "-")
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name[:64].strip("-")


def _load_config(target_root: Path) -> dict:
    path = target_root / _CONFIG
    if not path.exists():
        variants = []
        if (target_root / ".kilo" / "kilo.jsonc").exists():
            variants.append(".kilo/kilo.jsonc")
        if (target_root / "kilo.json").exists():
            variants.append("kilo.json")
        if (target_root / "kilo.jsonc").exists():
            variants.append("kilo.jsonc")
        if variants:
            warnings.warn(
                "Kilo Code: Spawn manages .kilo/kilo.json; existing "
                + ", ".join(variants)
                + " not merged",
                SpawnWarning,
            )
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SpawnError(f"Kilo Code config is not valid JSON: {path} ({exc})") from exc


def _save_config(target_root: Path, data: dict) -> None:
    path = target_root / _CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _build_mcp_entry(server: McpServer) -> dict:
    # Same local/remote shape as Mimo Code (OpenCode family); Kilo reads the
    # top-level "mcp" key of kilo.json with {env:VAR} placeholders.
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


class KiloCodeAdapter(IdeAdapter):
    key = "kilo-code"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".kilo").exists()
            or (target_root / ".kilocode").exists()
            or (target_root / "kilo.json").exists()
            or (target_root / "kilo.jsonc").exists()
        )
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
            name = _sanitize_skill_name(skill.name)
            skill_dir = target_root / ".kilo" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}", SpawnWarning)
            # Kilo requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}), "AGENTS.md")
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
        rewrite_ignore_block(target_root / ".kilocodeignore", globs)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        remove_ignore_block(target_root / ".kilocodeignore", globs)

    def rewrite_core_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_core_agent_ignore_region(target_root / ".kilocodeignore", globs)

    def rewrite_extension_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        rewrite_extension_agent_ignore_region(target_root / ".kilocodeignore", globs)

    def clear_spawn_agent_ignore(self, target_root: Path) -> None:
        clear_split_agent_ignore_file(target_root / ".kilocodeignore")

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / "AGENTS.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_kilo_code_repo(target_root)


register(KiloCodeAdapter())

__all__ = ["KiloCodeAdapter"]
