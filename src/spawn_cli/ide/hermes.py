"""Hermes Agent (Nous Research) IDE adapter.

Project scope: skills at <repo>/.hermes/skills/<name>/SKILL.md and a
spawn-managed block in root `.hermes.md` (Hermes highest-priority project
context file; priority: .hermes.md > AGENTS.override.md > AGENTS.md).
MCP config and agent ignore are global-only in Hermes
(~/.hermes/config.yaml; no ignore file) -> unsupported here.
Project skills require `hermes skills trust` before Hermes loads them.
`.agents/skills` is intentionally NOT used (owned by the Codex adapter).
"""

from __future__ import annotations

import warnings
from pathlib import Path

from spawn_cli.errors import SpawnWarning
from spawn_cli.ide import _vacancy as _vac
from spawn_cli.ide._helpers import rewrite_managed_block
from spawn_cli.ide.registry import (
    DetectResult,
    IdeAdapter,
    IdeCapabilities,
    normalize_skill_name,
    register,
    render_skill_md,
)
from spawn_cli.models.mcp import NormalizedMcp
from spawn_cli.models.skill import SkillMetadata

CAPS = IdeCapabilities(
    skills="native",
    mcp="unsupported",
    agent_ignore="unsupported",
    entry_point="hermes-md",
)


class HermesAdapter(IdeAdapter):
    key = "hermes"

    def detect(self, target_root: Path) -> DetectResult:
        used = (
            (target_root / ".hermes").is_dir()
            or (target_root / ".hermes.md").is_file()
            or (target_root / "HERMES.md").is_file()
        )
        return DetectResult(used_in_repo=used, capabilities=CAPS)

    def add_skills(self, target_root: Path, skill_metadata: list[SkillMetadata]) -> list[dict]:
        results = []
        for skill in skill_metadata:
            name = normalize_skill_name(skill.name)
            skill_dir = target_root / ".hermes" / "skills" / name
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_path = skill_dir / "SKILL.md"
            if skill_path.exists():
                warnings.warn(f"Overwriting existing rendered skill: {skill_path}")
            # Hermes requires frontmatter name == directory name.
            rendered = render_skill_md(skill.model_copy(update={"name": name}))
            skill_path.write_text(rendered, encoding="utf-8")
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
        del normalized_mcp
        del target_root
        warnings.warn(
            "Hermes has no project-scope MCP settings; "
            "servers stay configured globally in ~/.hermes/config.yaml",
            SpawnWarning,
        )
        return []

    def remove_mcp(self, target_root: Path, rendered_mcp_names: list[str]) -> None:
        del target_root, rendered_mcp_names
        warnings.warn("MCP is not managed by spawn for hermes; nothing to remove", SpawnWarning)

    def add_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("hermes: agent ignore is unsupported", SpawnWarning)

    def remove_agent_ignore(self, target_root: Path, globs: list[str]) -> None:
        del target_root, globs
        warnings.warn("hermes: agent ignore is unsupported", SpawnWarning)

    def rewrite_entry_point(self, target_root: Path, prompt: str) -> str:
        ep = target_root / ".hermes.md"
        rewrite_managed_block(ep, prompt)
        return ep.relative_to(target_root).as_posix()

    def finalize_repo_after_ide_removed(self, target_root: Path) -> None:
        _vac.finalize_hermes_repo(target_root)


register(HermesAdapter())

__all__ = ["HermesAdapter"]
